# Generated by Django 4.1.5 on 2023-01-12 22:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('servico', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servico',
            name='preco_servico',
        ),
    ]