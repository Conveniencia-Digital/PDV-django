# Generated by Django 4.1.5 on 2023-01-17 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fornecedor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fornecedores',
            name='observacao',
            field=models.TextField(blank=True, null=True),
        ),
    ]
