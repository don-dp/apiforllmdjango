# Generated by Django 4.2.2 on 2023-07-09 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_apikey_created_at_apikey_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chattemplate',
            name='system_prompt',
            field=models.CharField(default='', max_length=10000),
            preserve_default=False,
        ),
    ]