# Generated by Django 4.2.2 on 2023-07-13 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_chattemplate_is_public_chattemplate_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='function_approval_required',
            field=models.BooleanField(default=True),
        ),
    ]