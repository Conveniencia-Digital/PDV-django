# Generated by Django 4.1.5 on 2023-01-23 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peca', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pecas',
            name='forma_pagamento',
            field=models.CharField(choices=[('Cartāo de credito', 'Pix'), ('Cartāo de credito', 'Cartāo de credito'), ('Cartāo de debito', 'Cartāo de debito'), ('Dinheiro', 'Dinheiro'), ('Fiado a pagar', 'Fiado a pagar')], default='Cartāo de credito', max_length=21),
        ),
    ]
