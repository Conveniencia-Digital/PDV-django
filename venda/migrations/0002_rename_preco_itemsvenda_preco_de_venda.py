# Generated by Django 4.1 on 2023-01-08 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venda', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='itemsvenda',
            old_name='preco',
            new_name='preco_de_venda',
        ),
    ]
