# Generated by Django 4.1.5 on 2023-01-12 01:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaDespesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_categoria_despesa', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Despesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_despesa', models.CharField(max_length=90)),
                ('preco_despesa', models.DecimalField(decimal_places=2, max_digits=9)),
                ('fornecedor', models.CharField(blank=True, max_length=90, null=True)),
                ('observacao', models.TextField(blank=True, max_length=1000, null=True)),
                ('data_cadastro', models.DateTimeField(auto_now_add=True)),
                ('categoria_despesa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='despesa.categoriadespesa')),
            ],
        ),
    ]
