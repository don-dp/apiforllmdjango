from django import forms
from django.test import TestCase
from .models import SecretKey, ChatTemplate
from .forms import SecretKeyForm, ChatSessionCreateForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class SecretKeyFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.secret_key = SecretKey.objects.create(
            user=self.user,
            name='Test Key',
            key='test_key',
            is_public=False,
        )
        self.secret_key.encrypt_key('real_secret_key')

    def test_form_valid(self):
        form = SecretKeyForm({
            'user': self.user.id,
            'name': 'Another Test Key',
            'key': 'another_test_key',
            'is_public': False
        })
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = SecretKeyForm({
            'name': '',
            'key': 'another_test_key',
            'is_public': False
        })
        self.assertFalse(form.is_valid())

    def test_form_save(self):
        form = SecretKeyForm({
            'user': self.user.id,
            'name': 'Another Test Key',
            'key': 'another_test_key',
            'is_public': False
        })
        if form.is_valid():
            new_instance = form.save()
            self.assertEqual(new_instance.name, 'Another Test Key')

    def test_form_init_with_instance(self):
        form = SecretKeyForm(instance=self.secret_key)
        decrypted_key = form.initial['key']
        self.assertEqual(decrypted_key, 'real_secret_key')

class ChatSessionCreateFormTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='testpass1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass2')
        
        self.template1 = ChatTemplate.objects.create(
            name='Template1',
            model='GPT-3',
            temperature=0.7,
            system_prompt='System Prompt 1',
            user=self.user1,
            is_public=False,
        )
        self.template2 = ChatTemplate.objects.create(
            name='Template2',
            model='GPT-3',
            temperature=0.7,
            system_prompt='System Prompt 2',
            user=self.user1,
            is_public=True,
        )

    def test_form_valid(self):
        form = ChatSessionCreateForm({
            'title': 'Test Session',
            'template': self.template2.id,
            'function_approval_required': True,
        }, user=self.user2)
        self.assertTrue(form.is_valid())

    def test_form_invalid_no_title(self):
        form = ChatSessionCreateForm({
            'template': self.template2.id,
            'function_approval_required': True,
        }, user=self.user2)
        self.assertFalse(form.is_valid())

    def test_form_invalid_wrong_template(self):
        form = ChatSessionCreateForm({
            'title': 'Test Session',
            'template': self.template1.id,  # This template is not public and doesn't belong to user2
            'function_approval_required': True,
        }, user=self.user2)
        self.assertFalse(form.is_valid())

    def test_form_save(self):
        form = ChatSessionCreateForm({
            'title': 'Test Session',
            'template': self.template2.id,
            'function_approval_required': True,
        }, user=self.user2)

        if form.is_valid():
            new_instance = form.save()
            self.assertEqual(new_instance.title, 'Test Session')

    def test_form_invalid_save(self):
        form = ChatSessionCreateForm({
            'title': 'Test Session',
            'template': self.template1.id,
            'function_approval_required': True,
        }, user=self.user2)

        if form.is_valid():
            with self.assertRaises(ValidationError):
                form.save()