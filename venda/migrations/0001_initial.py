# Generated by Django 4.1.5 on 2023-03-30 13:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cliente', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('colaborador', '0001_initial'),
        ('produto', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_edicao', models.DateTimeField(auto_now=True)),
                ('desconto', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ('forma_pagamento', models.CharField(choices=[('Pix', 'Pix'), ('Cartāo de credito', 'Cartāo de credito'), ('Cartāo de debito', 'Cartāo de debito'), ('Dinheiro', 'Dinheiro'), ('Fiado a receber', 'Fiado a receber')], default='Pix', max_length=20)),
                ('observacao', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Entregue', 'Concluida e entregue'), ('Cancelada', 'Cancelada e estornada'), ('Troca de produto', 'Troca de produto'), ('Retorno garantia', 'Retorno para garantia')], default='Entregue', max_length=20)),
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
            name='ItemsVenda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.IntegerField()),
                ('preco', models.DecimalField(decimal_places=2, max_digits=9)),
                ('produto', models.ForeignKey(limit_choices_to={'quantidade__gt': 0}, on_delete=django.db.models.deletion.CASCADE, to='produto.produto')),
                ('vendas', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vendas_items', to='venda.vendas')),
            ],
            options={
                'ordering': ('pk',),
            },
        ),
    ]
