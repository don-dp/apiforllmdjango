# Generated by Django 4.2.2 on 2023-07-08 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_chatsession_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='role',
            field=models.CharField(choices=[('system', 'System'), ('user', 'User'), ('assistant', 'Assistant'), ('function', 'Function')], max_length=10),
        ),
    ]