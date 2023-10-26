from django.test import TestCase
from django.urls import reverse
from main.models import ChatSession, ChatMessage, User, RoleChoices, FunctionSchema
from django.contrib.auth.models import User
from .models import ChatSession, ChatTemplate, FunctionServer, ChatMessage, RoleChoices
from django.utils import timezone
import json

class HomePageViewTest(TestCase):

    def test_home_page_status_code(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_template_used(self):
        response = self.client.get(reverse('homepage'))
        self.assertTemplateUsed(response, 'main/homepage.html')

class ChatsViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)
        self.template = ChatTemplate.objects.create(
            name='Test Template',
            model='gpt-3.5-turbo',
            temperature=0.7,
            system_prompt='Start',
            user=self.user
        )
        self.session1 = ChatSession.objects.create(user=self.user, template=self.template, title='Session 1')
        self.session2 = ChatSession.objects.create(user=self.user, template=self.template, title='Session 2')
        ChatMessage.objects.create(session=self.session1, role='user', content='Message 1')
        ChatMessage.objects.create(session=self.session2, role='user', content='Message 2')

    def test_chats_view_logged_in(self):
        response = self.client.get(reverse('chats'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('chat_sessions' in response.context)
        self.assertTrue('chat_messages' in response.context)
        self.assertTrue(self.session1 in response.context['chat_sessions'])
        self.assertTrue(self.session2 in response.context['chat_sessions'])

    def test_chats_view_ordering(self):
        ChatMessage.objects.create(
            session=self.session1,
            role=RoleChoices.USER,
            content='New message'
        )
        
        response = self.client.get(reverse('chats'))
        sessions = list(response.context['chat_sessions'])

        self.assertEqual(sessions[0], self.session1)

    def test_chats_view_logged_out(self):
        self.client.logout()
        response = self.client.get(reverse('chats'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/chats/')

    def test_chats_view_template(self):
        response = self.client.get(reverse('chats'))
        self.assertTemplateUsed(response, 'main/chats.html')

class ChatMessageListTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        
        self.template = ChatTemplate.objects.create(
            name='Test Template',
            model='Test Model',
            temperature=0.7,
            system_prompt='Starting test...',
            user=self.user1,
            is_public=False
        )
        
        self.function_server = FunctionServer.objects.create(
            user=self.user1,
            name='Test Function Server',
            ip_address='192.168.1.1',
            is_public=False
        )
        
        self.session1 = ChatSession.objects.create(
            user=self.user1,
            template=self.template,
            title="Session 1",
            function_server=self.function_server
        )
        
        self.session2 = ChatSession.objects.create(
            user=self.user2,
            template=self.template,
            title="Session 2",
            function_server=self.function_server
        )
        
        self.message1 = ChatMessage.objects.create(
            session=self.session1,
            role=RoleChoices.USER,
            content="Message 1"
        )
        
        self.client.force_login(self.user1)
        
    def test_message_list_success(self):
        url = reverse('chat_messages', args=[self.session1.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['role'], RoleChoices.SYSTEM)
        self.assertEqual(data[1]['role'], RoleChoices.USER)
        self.assertEqual(data[1]['content'], "Message 1")


    def test_message_list_not_owner(self):
        url = reverse('chat_messages', args=[self.session2.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)

    def test_message_list_not_found(self):
        url = reverse('chat_messages', args=[999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

class FunctionsViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)
        
        self.func1 = FunctionSchema.objects.create(
            name='Function 1',
            user=self.user,
            schema={"key": "value1"},
            created_at=timezone.now()
        )
        
        self.func2 = FunctionSchema.objects.create(
            name='Function 2',
            user=self.user,
            schema={"key": "value2"},
            created_at=timezone.now() + timezone.timedelta(days=1)
        )
    
    def test_functions_view(self):
        response = self.client.get(reverse('functions'))
        self.assertEqual(response.status_code, 200)
        functions = list(response.context['functions'])
        self.assertEqual(functions[0], self.func2)
        self.assertEqual(functions[1], self.func1)

    def test_functions_view_not_logged_in(self):
        url = reverse('functions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_functions_view_pagination(self):
        for i in range(15):
            FunctionSchema.objects.create(
                name=f'Function {i + 3}',
                user=self.user,
                schema={"key": f"value{i + 3}"},
                created_at=timezone.now() + timezone.timedelta(days=i + 2)
            )
        
        response = self.client.get(reverse('functions'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        functions = list(response.context['functions'])
        self.assertEqual(len(functions), 7)

class TemplatesViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)
        
        ChatTemplate.objects.create(
            name='Template 1',
            model='model1',
            temperature=0.7,
            system_prompt='Start',
            user=self.user
        )
        
        ChatTemplate.objects.create(
            name='Template 2',
            model='model2',
            temperature=0.8,
            system_prompt='Continue',
            user=self.user
        )

    def test_templates_view_logged_in(self):
        response = self.client.get(reverse('templates'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('templates' in response.context)

    def test_templates_view_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('templates'))
        self.assertEqual(response.status_code, 200)

    def test_templates_view_pagination(self):
        for i in range(15):
            ChatTemplate.objects.create(
                name=f'Template {i + 3}',
                model=f'model{i + 3}',
                temperature=0.6,
                system_prompt='Prompt',
                user=self.user
            )
        response = self.client.get(reverse('templates') + '?page=2')
        self.assertEqual(response.status_code, 200)
        templates = response.context['templates']
        self.assertEqual(len(templates), 7)

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import ChatTemplate, FunctionServer, ChatSession
from django.core.exceptions import ObjectDoesNotExist

class CreateChatViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.template = ChatTemplate.objects.create(
            name="Test Template",
            model="Test Model",
            temperature=0.5,
            system_prompt="System Prompt",
            user=self.user,
            is_public=False,
        )
        self.function_server = FunctionServer.objects.create(
            name="Test Server",
            is_public=True,
        )

    def test_get_request_logged_in(self):
        self.client.force_login(self.user)
        url = reverse('create_chat')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="template"')
        self.assertContains(response, 'name="function_approval_required"')

    def test_post_request_form_valid(self):
        self.client.force_login(self.user)
        url = reverse('create_chat')
        data = {
            'title': 'Test Chat',
            'template': self.template.id,
            'function_approval_required': True,
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('chats'))
        self.assertEqual(ChatSession.objects.count(), 1)

    def test_not_logged_in(self):
        url = reverse('create_chat')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
