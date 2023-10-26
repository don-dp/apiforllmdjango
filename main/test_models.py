from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserBalance, SecretKey, FunctionServer, FunctionSchema, ChatTemplate, ChatSession, ChatMessage, RoleChoices

class UserBalanceTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user_balance = UserBalance.objects.create(user=self.user, balance=Decimal('100.0'))

    def test_credit_balance(self):
        self.user_balance.credit(Decimal('50.0'))
        self.assertEqual(self.user_balance.balance, Decimal('150.0'))

    def test_debit_balance(self):
        self.user_balance.debit(Decimal('50.0'))
        self.assertEqual(self.user_balance.balance, Decimal('50.0'))
    
    def test_reset_balance(self):
        self.user_balance.reset_balance(Decimal('0.0'))
        self.assertEqual(self.user_balance.balance, Decimal('0.0'))

    def test_insufficient_balance(self):
        with self.assertRaises(ValueError):
            self.user_balance.debit(Decimal('150.0'))

class FunctionServerTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.function_server = FunctionServer.objects.create(
            user=self.user, 
            name='Test Server', 
            ip_address='192.168.0.1',
            hostname='test.hostname',
            is_public=False
        )
    
    def test_instance_creation(self):
        self.assertTrue(isinstance(self.function_server, FunctionServer))

    def test_str_representation(self):
        self.assertEqual(str(self.function_server), 'Test Server')

    def test_ip_address(self):
        self.assertEqual(self.function_server.ip_address, '192.168.0.1')

    def test_hostname(self):
        self.assertEqual(self.function_server.hostname, 'test.hostname')

    def test_is_public(self):
        self.assertFalse(self.function_server.is_public)

class FunctionSchemaTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.secret_key = SecretKey.objects.create(user=self.user, name='Test Secret', key='test_key')
        self.function_schema = FunctionSchema.objects.create(
            name='Test Function',
            user=self.user,
            schema={"input": "text", "output": "text"},
            is_public=False,
            network_access=False,
        )
        self.function_schema.secrets.add(self.secret_key)

    def test_instance_creation(self):
        self.assertTrue(isinstance(self.function_schema, FunctionSchema))

    def test_str_representation(self):
        self.assertEqual(str(self.function_schema), 'Test Function')

    def test_schema(self):
        self.assertEqual(self.function_schema.schema, {"input": "text", "output": "text"})

    def test_is_public(self):
        self.assertFalse(self.function_schema.is_public)

    def test_network_access(self):
        self.assertFalse(self.function_schema.network_access)

    def test_secret_keys(self):
        self.assertEqual(list(self.function_schema.secrets.all()), [self.secret_key])

class SecretKeyTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.secret_key = SecretKey.objects.create(
            user=self.user,
            name='Test Key',
            key='test_key',
            is_public=False,
        )
        self.secret_key.encrypt_key('real_secret_key')

    def test_instance_creation(self):
        self.assertTrue(isinstance(self.secret_key, SecretKey))

    def test_str_representation(self):
        self.assertEqual(str(self.secret_key), f'API Key Test Key of {self.user}')

    def test_is_public(self):
        self.assertFalse(self.secret_key.is_public)

    def test_encryption_decryption(self):
        decrypted_key = self.secret_key.decrypt_key()
        self.assertEqual(decrypted_key, 'real_secret_key')

        # Test encryption again to make sure it works both ways
        self.secret_key.encrypt_key(decrypted_key)
        self.assertEqual(self.secret_key.decrypt_key(), 'real_secret_key')

class ChatTemplateTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.function_schema = FunctionSchema.objects.create(
            name='Test Function',
            user=self.user,
            schema={"input": "text", "output": "text"},
            is_public=False,
            network_access=False,
        )
        self.chat_template = ChatTemplate.objects.create(
            name='Test Template',
            model='GPT-3',
            temperature=0.7,
            system_prompt='Hello, how can I assist you today?',
            user=self.user,
            is_public=False,
        )
        self.chat_template.functions.add(self.function_schema)

    def test_instance_creation(self):
        self.assertTrue(isinstance(self.chat_template, ChatTemplate))

    def test_str_representation(self):
        self.assertEqual(str(self.chat_template), 'Test Template')

    def test_name(self):
        self.assertEqual(self.chat_template.name, 'Test Template')

    def test_model(self):
        self.assertEqual(self.chat_template.model, 'GPT-3')

    def test_temperature(self):
        self.assertEqual(self.chat_template.temperature, 0.7)

    def test_system_prompt(self):
        self.assertEqual(self.chat_template.system_prompt, 'Hello, how can I assist you today?')

    def test_is_public(self):
        self.assertFalse(self.chat_template.is_public)

    def test_functions(self):
        self.assertEqual(list(self.chat_template.functions.all()), [self.function_schema])

class ChatSessionTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.chat_template = ChatTemplate.objects.create(
            name='Test Template',
            model='GPT-3',
            temperature=0.7,
            system_prompt='Hello, how can I assist you today?',
            user=self.user,
            is_public=False
        )
        self.function_server = FunctionServer.objects.create(
            user=self.user, 
            name='Test Server', 
            ip_address='192.168.0.1',
            hostname='test.hostname',
            is_public=False
        )
        self.chat_session = ChatSession.objects.create(
            user=self.user,
            template=self.chat_template,
            title='Test Session',
            flagged=False,
            function_approval_required=True,
            function_server=self.function_server
        )

    def test_instance_creation(self):
        self.assertTrue(isinstance(self.chat_session, ChatSession))

    def test_str_representation(self):
        self.assertEqual(str(self.chat_session), 'Test Session')

    def test_title(self):
        self.assertEqual(self.chat_session.title, 'Test Session')

    def test_flagged(self):
        self.assertFalse(self.chat_session.flagged)

    def test_function_approval_required(self):
        self.assertTrue(self.chat_session.function_approval_required)

    def test_function_server(self):
        self.assertEqual(self.chat_session.function_server, self.function_server)


class ChatMessageTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.chat_template = ChatTemplate.objects.create(
            name='Test Template',
            model='GPT-3',
            temperature=0.7,
            system_prompt='Hello, how can I assist you today?',
            user=self.user,
            is_public=False
        )
        self.chat_session = ChatSession.objects.create(
            user=self.user,
            template=self.chat_template,
            title='Test Session',
            flagged=False,
            function_approval_required=True,
        )
        self.chat_message = ChatMessage.objects.create(
            session=self.chat_session,
            role=RoleChoices.USER,
            content='This is a test message',
            input_cost=Decimal('0.001'),
            output_cost=Decimal('0.002'),
        )

    def test_instance_creation(self):
        self.assertTrue(isinstance(self.chat_message, ChatMessage))

    def test_str_representation(self):
        self.assertEqual(str(self.chat_message), 'This is a test message')

    def test_role(self):
        self.assertEqual(self.chat_message.role, RoleChoices.USER)

    def test_content(self):
        self.assertEqual(self.chat_message.content, 'This is a test message')

    def test_input_cost(self):
        self.assertEqual(self.chat_message.input_cost, Decimal('0.001'))

    def test_output_cost(self):
        self.assertEqual(self.chat_message.output_cost, Decimal('0.002'))

    def test_create_initial_message(self):
        ChatSession.objects.all().delete()
        
        # Create a new chat session, triggering the post_save signal
        new_chat_session = ChatSession.objects.create(
            user=self.user,
            template=self.chat_template,
            title='New Test Session',
            flagged=False,
            function_approval_required=True,
        )
        
        # Check that a new message has been created automatically
        initial_message = ChatMessage.objects.filter(session=new_chat_session).first()
        
        self.assertEqual(initial_message.role, RoleChoices.SYSTEM)
        self.assertEqual(initial_message.content, new_chat_session.template.system_prompt)
        self.assertEqual(initial_message.input_cost, Decimal('0.0'))
        self.assertEqual(initial_message.output_cost, Decimal('0.0'))