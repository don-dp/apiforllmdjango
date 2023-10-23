from apiforllmdjango.celery import app
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .helpers import has_sufficient_balance, num_tokens_from_messages, get_chat_messages, moderation_endpoint, get_chat_completion, can_execute_function
from decimal import Decimal
from .models import ChatMessage, UserBalance, ChatSession
from django.contrib.auth.models import User
import requests
import json
from django.core import signing

@app.task(soft_time_limit=30, time_limit=35)
def openai_api_call(session_id, user_id, content):
    try:
        session = ChatSession.objects.get(id=session_id)
        user = User.objects.get(id=user_id)
        messages = get_chat_messages(session.id)

        if 'content' in content:
            user_message = {'role' : 'user', 'content' : content['content']}
            chat_record = ChatMessage(
                session=session,
                role=user_message['role'],
                content=user_message['content'],
            )
            chat_record.save() 
            send_message(session_id, user_message)
            messages.append(user_message)
        
        elif 'invoke_ai' in content:
            send_message(session_id, {'role' : 'system', 'content' : "Invoking AI."})
            user_message = {'role' : 'user', 'content' : ''}
        
        elif 'invoke_function' in content:
            send_message(session_id, {'role' : 'system', 'content' : "Invoking function."})
            last_message_content = messages[-1]['content']
            execute_function.delay(session_id, last_message_content)
            return

        input_tokens = num_tokens_from_messages(messages)
        if(input_tokens >= 16000):
            error_message = {"role": "system", "content": "Token limit exceeded. Please start a new chat session."}
            send_message(session_id, error_message)
            return
        
        if(not has_sufficient_balance(user, input_tokens)):
            error_message = {"role": "system", "content": "Insufficient balance in your account. Please topup your account to continue."}
            send_message(session_id, error_message)
            return

        try:
            response = get_chat_completion(messages, user.username, session)
            input_cost = Decimal(str(response['costs']['input_cost']))
            output_cost = Decimal(str(response['costs']['output_cost']))
            total_cost = input_cost + output_cost
            user_balance = UserBalance.objects.get(user=user)  
            user_balance.debit(total_cost)
            api_response = response['chat_completion']['choices'][0]['message']['content']
            if moderation_endpoint(user_message['content']) or moderation_endpoint(api_response):
                session.flagged = True
                session.save()
                
                send_message(session_id, {"role": "system", "content": "This chat session has been flagged by the moderation endpoint."})
                return
        except Exception as e:
            error_message = {"role": "system", "content": "A network error occurred."}
            send_message(session_id, error_message)
            return

        role = response['chat_completion']['choices'][0]['message']['role']
        is_function_call = False

        if api_response is None:  
            function_name = response['chat_completion']['choices'][0]['message']['function_call']['name']
            function_args = response['chat_completion']['choices'][0]['message']['function_call']['arguments']
            api_response = f"Function: {function_name}, Arguments: {function_args}"
            is_function_call = True
        
        message = ChatMessage(
            session=session,
            role=role,
            content=api_response,
            input_cost=input_cost,
            output_cost=output_cost,
        )

        message.save()

        send_message(session_id, {'role' : role, 'content' : api_response})
        if is_function_call:
            send_message(session_id, {'is_function_call' : True, 'function_approval_required' : session.function_approval_required})
    
    except Exception as e:
        error_message = {"role": "system", "content": "An error occurred."}
        send_message(session_id, error_message)

def send_message(session_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        str(session_id),
        {
            'type': 'receive_group_message',  
            'message': message,
        }
    )

@app.task(soft_time_limit=30, time_limit=35)
def execute_function(session_id, api_response):
    try:
        session = ChatSession.objects.get(id=session_id)
        prefix = "Function: "
        prefix_args = "Arguments: "
        function_name = api_response[api_response.index(prefix) + len(prefix):api_response.index(", Arguments: ")].strip()
        
        if not can_execute_function(function_name, session):
            raise Exception("Cannot execute function.")
        function_args = api_response[api_response.index(prefix_args) + len(prefix_args):].strip()
        function_args = json.loads(function_args)

        function = session.template.functions.filter(name=function_name).first()
        secrets = function.secrets.all()
        for secret in secrets:
            secret_key = secret.name
            decrypted_key_value = secret.decrypt_key()
            if secret_key in function_args:
                raise Exception(f'Secret key {secret_key} already exists in function_args')
            function_args[secret_key] = decrypted_key_value

        signer = signing.TimestampSigner()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': signer.sign(session_id)
        }
        data = {
            'docker_image': function_name,
            'arguments': function_args,
            'network': function.network_access
        }
        hostname = session.function_server.hostname.rstrip('/')
        url = "{}/runfunction/{}".format(hostname, session.id)

        response = requests.post(url, headers=headers, data=json.dumps(data))

        #print(f"URL: {url}\nStatus code: {response.status_code}\nJSON content: {response.json()}\nData: {data}")

    except Exception as e:
        error_message = {"role": "system", "content": "A function call error occurred."}
        send_message(session.id, error_message)