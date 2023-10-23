# Generated by Django 4.2.2 on 2023-07-07 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_functionschema'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('model', models.CharField(max_length=64)),
                ('temperature', models.FloatField()),
                ('functions', models.ManyToManyField(blank=True, to='main.functionschema')),
            ],
        ),
    ]