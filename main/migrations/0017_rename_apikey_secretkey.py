# Generated by Django 4.2.2 on 2023-07-15 06:33

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0016_chatsession_function_approval_required'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='APIKey',
            new_name='SecretKey',
        ),
    ]
