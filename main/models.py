from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from cryptography.fernet import Fernet
import base64
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class SecretKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    key = models.TextField(db_column='key')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def decrypt_key(self):
        f = Fernet(base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32]))
        return f.decrypt(self.key.encode()).decode()

    def encrypt_key(self, new_key):
        f = Fernet(base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32]))
        self.key = f.encrypt(new_key.encode()).decode()

    def __str__(self):
        return f'API Key {self.name} of {self.user}' if self.user else f'Public API Key {self.name}'

class FunctionSchema(models.Model):
    name = models.CharField(max_length=64)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    schema = models.JSONField()
    is_public = models.BooleanField(default=False)
    network_access = models.BooleanField(default=False)
    secrets = models.ManyToManyField(SecretKey, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ChatTemplate(models.Model):
    name = models.CharField(max_length=64)
    model = models.CharField(max_length=64)
    temperature = models.FloatField()
    functions = models.ManyToManyField(FunctionSchema, blank=True)
    system_prompt = models.CharField(max_length=10000)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FunctionServer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, null=True, blank=True)
    hostname = models.CharField(max_length=200, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(ChatTemplate, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    flagged = models.BooleanField(default=False)
    function_approval_required = models.BooleanField(default=True)
    function_server = models.ForeignKey(FunctionServer, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class RoleChoices(models.TextChoices):
    SYSTEM = 'system',
    USER = 'user',
    ASSISTANT = 'assistant',
    FUNCTION = 'function',

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=RoleChoices.choices)
    content = models.CharField(max_length=40000)
    input_cost = models.DecimalField(max_digits=10, decimal_places=9, default=Decimal('0.0'))
    output_cost = models.DecimalField(max_digits=10, decimal_places=9, default=Decimal('0.0'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content

    @receiver(post_save, sender=ChatSession)
    def create_initial_message(sender, instance, created, **kwargs):
        if created:  # if a new instance of ChatSession is created
            ChatMessage.objects.create(
                session=instance,
                role=RoleChoices.SYSTEM,
                content=instance.template.system_prompt,
                input_cost=Decimal('0.0'),
                output_cost=Decimal('0.0'),
            )

class UserBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=16, decimal_places=9, default=Decimal('0.0')) 
    last_credit = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def debit(self, amount):
        if self.balance > 0 and self.balance - amount >= Decimal('0.0'):
            self.balance -= amount
            self.save()
        else:
            raise ValueError("Insufficient balance")

    def credit(self, amount):
        self.balance += amount
        self.last_credit = timezone.now()
        self.save()

    def reset_balance(self, amount=Decimal('0.0')):
        self.balance = amount
        self.last_credit = timezone.now()
        self.save()