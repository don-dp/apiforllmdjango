# Generated by Django 4.2.2 on 2023-07-07 13:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_chattemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='template',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='main.chattemplate'),
            preserve_default=False,
        ),
    ]