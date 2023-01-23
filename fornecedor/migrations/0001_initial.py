# Generated by Django 4.1.5 on 2023-01-16 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Fornecedores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_edicao', models.DateTimeField(auto_now=True)),
                ('nome_fornecedor', models.CharField(max_length=90)),
                ('cnpj', models.CharField(blank=True, max_length=14, null=True)),
                ('telefone_contato', models.CharField(max_length=15)),
                ('telefone_contato_2', models.CharField(blank=True, max_length=15, null=True)),
                ('rua', models.CharField(blank=True, max_length=99, null=True)),
                ('numero_casa', models.IntegerField(blank=True, null=True)),
                ('bairro', models.CharField(blank=True, max_length=90, null=True)),
            ],
        ),
    ]