import openai
from .models import ChatSession, ChatMessage, UserBalance, FunctionSchema
from django.conf import settings
import hashlib
import tiktoken
from decimal import Decimal

def get_model(session):
    return session.template.model

def get_chat_completion(messages, username, session):
    openai.api_key = settings.APIFORLLMDJANGO_OPENAI_KEY
    model = get_model(session)
    
    functions = get_functions_as_json(session)
    if functions:
        chat_completion = openai.ChatCompletion.create(
            model=model, 
            messages=messages, 
            user=hash_username(username),
            temperature=session.template.temperature,
            functions=functions
        )
    else:
        chat_completion = openai.ChatCompletion.create(
            model=model, 
            messages=messages, 
            user=hash_username(username),
            temperature=session.template.temperature
        )

    costs = calculate_cost(chat_completion)
    return { 'chat_completion' : chat_completion, 'costs' : costs}

def calculate_cost(chat_completion):
    usage = chat_completion["usage"]
    input_prompt_token_cost = 0.0015 / 1000  # cost per input token
    output_completion_token_cost = 0.002 / 1000  # cost per output token

    input_tokens = usage["prompt_tokens"]
    output_tokens = usage["completion_tokens"]
    
    input_cost = input_tokens * input_prompt_token_cost
    output_cost = output_tokens * output_completion_token_cost

    return {'input_cost' : input_cost, 'output_cost' : output_cost}

def has_sufficient_balance(user, input_tokens, output_tokens=50):
    input_prompt_token_cost = 0.0015 / 1000  # cost per input token
    output_completion_token_cost = 0.002 / 1000  # cost per output token

    input_cost = input_tokens * input_prompt_token_cost
    output_cost = output_tokens * output_completion_token_cost

    total_cost = input_cost + output_cost

    user_balance, created = UserBalance.objects.get_or_create(user=user, defaults={'balance': Decimal('0.0')})

    return user_balance.balance >= total_cost

def get_chat_messages(session_id):
    try:
        chat_session = ChatSession.objects.get(pk=session_id)
    except ChatSession.DoesNotExist:
        return "ChatSession does not exist"

    messages = ChatMessage.objects.filter(session=chat_session).order_by('created_at')

    result = [
        {
            "role": message.role,
            "content": message.content
        }
        for message in messages
    ]

    return result

def moderation_endpoint(input_text):
    if not input_text:
        return False
    openai.api_key = settings.APIFORLLMDJANGO_OPENAI_KEY
    response = openai.Moderation.create(
        input=input_text
    )

    return response["results"][0]['flagged']

def hash_username(username):
    return hashlib.sha256(username.encode()).hexdigest()

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-16k-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3
    tokens_per_name = 1
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def get_functions_as_json(session):
    function_schemas = session.template.functions.all()
    if function_schemas.exists():
        return [function.schema for function in function_schemas]
    else:
        return []
    
def can_execute_function(function_name, session):
    if session is None:
        return False
    
    function = session.template.functions.filter(name=function_name).first()
    
    if function is None:
        return False

    if session.function_server is None:
        return False
    
    if not session.function_server.is_public and session.function_server.user != session.user:
        return False
    
    if not function.is_public and function.user != session.user:
        return False
    
    return True