from channels.generic.websocket import JsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import ChatSession
from asgiref.sync import async_to_sync
from .tasks import openai_api_call
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.exceptions import ObjectDoesNotExist

class ChatConsumer(JsonWebsocketConsumer):
    def connect(self):
        user = self.scope["user"]
        if user == AnonymousUser():
            self.close(code=4401)
            return
        
        session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.session_id = session_id
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            self.close(code=4404)
            return
        
        if user != session.user:
            self.close(code=4403)
            return
        
        flagged_sessions_count = ChatSession.objects.filter(user=user, flagged=True).count()
        if session.flagged or flagged_sessions_count >= 3:
            self.close(code=4405)
            return
        
        self.accept()
        async_to_sync(self.channel_layer.group_add)(self.session_id, self.channel_name)

    def receive_json(self, content, **kwargs):
        user = self.scope["user"]
        if user == AnonymousUser():
            self.send_json({"role" : "system", "content" : "You do not have access."})
            self.close(code=4401)
            return

        session_id = self.scope["url_route"]["kwargs"]["session_id"]
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            self.send_json({"role" : "system", "content" : "Invalid chat session."})
            self.close(code=4404)
            return

        if user != session.user:
            self.send_json({"role" : "system", "content" : "You can only access your chat sessions."})
            return

        flagged_sessions_count = ChatSession.objects.filter(user=user, flagged=True).count()
        if session.flagged or flagged_sessions_count >= 3:
            self.send_json({
                "role": "system",
                "content": "This chat session has been flagged or you have too many flagged chat sessions. Please email dinesh@apiforllm.com if you think there's been an error."
            })
            self.close(code=4405)
            return

        if 'content' in content or 'invoke_ai' in content or 'invoke_function' in content:
            openai_api_call.delay(session.id, user.id, content)
        else:
            self.send_json({"role" : "system", "content" : "Invalid request."})
    
    def send_group_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.session_id,
            {
                'type': 'receive_group_message',  
                'message': message,
            }
        )

    def receive_group_message(self, event):
        self.send_json(event['message'])


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.session_id, self.channel_name)

class FunctionResultConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.token = self.scope['query_string'].decode('utf8').split('=')[1]

        signer = TimestampSigner()
        try:
            original_session_id = signer.unsign(self.token, max_age=120)
        except SignatureExpired:
            print("Token has expired")
            self.close(code=4001)
            return
        except BadSignature:
            print("Bad token signature")
            self.close(code=4002)
            return

        if original_session_id != self.session_id:
            print("Token session ID does not match URL session ID")
            self.close(code=4003)
            return

        self.accept()

    def disconnect(self, close_code):
        pass

    def receive_json(self, content):
        output = content.get('output')
        error = content.get('error')

        try:
            session_exists = ChatSession.objects.filter(id=self.session_id).exists()
        except ObjectDoesNotExist:
            session_exists = False
        
        if output is not None and session_exists:
            session = ChatSession.objects.get(id=self.session_id)
            openai_api_call.delay(session.id, session.user.id, {"content" : output})
        elif error is not None:
            async_to_sync(self.channel_layer.group_send)(
                self.session_id,
                {
                    'type': 'receive_group_message',  
                    'message': {"role" : "system", "content" : error },
                }
                )