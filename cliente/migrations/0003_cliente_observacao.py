# Generated by Django 4.1.5 on 2023-01-17 03:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0002_alter_cliente_data_criacao_alter_cliente_data_edicao'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='observacao',
            field=models.TextField(blank=True, null=True),
        ),
    ]
