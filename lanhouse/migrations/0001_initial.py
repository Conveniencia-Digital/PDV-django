# Generated by Django 4.1.5 on 2023-03-10 15:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cliente', '0001_initial'),
        ('colaborador', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LanhouseServico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao_servico', models.CharField(max_length=90)),
            ],
        ),
        migrations.CreateModel(
            name='LanhouseModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_edicao', models.DateTimeField(auto_now=True)),
                ('desconto', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ('forma_pagamento', models.CharField(choices=[('Pix', 'Pix'), ('Cartāo de credito', 'Cartāo de credito'), ('Cartāo de debito', 'Cartāo de debito'), ('Dinheiro', 'Dinheiro'), ('Fiado a receber', 'Fiado a receber')], default='Pix', max_length=20)),
                ('observacao', models.TextField(blank=True, null=True)),
                ('data_vencimento', models.DateField(blank=True, null=True)),
                ('qtd_parcela', models.IntegerField(blank=True, null=True)),
                ('valor_entrada', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cliente.cliente')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('vendedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='colaborador.colaborador')),
            ],
            options={
                'ordering': ('-pk',),
            },
        ),
        migrations.CreateModel(
            name='ItemsLanhouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.IntegerField()),
                ('preco', models.DecimalField(decimal_places=2, max_digits=9)),
                ('lanhouse', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lanhouse_items', to='lanhouse.lanhousemodel')),
                ('servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lanhouse.lanhouseservico')),
            ],
            options={
                'ordering': ('pk',),
            },
        ),
    ]
