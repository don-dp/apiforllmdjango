# Generated by Django 4.2.2 on 2023-07-07 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_userbalance'),
    ]

    operations = [
        migrations.CreateModel(
            name='FunctionSchema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('schema', models.JSONField()),
            ],
        ),
    ]