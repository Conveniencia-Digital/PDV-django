# Generated by Django 3.2.13 on 2022-06-28 21:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('produto', '0003_alter_produto_quantidade'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nf', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ItemsVenda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.IntegerField()),
                ('preco', models.DecimalField(decimal_places=2, max_digits=9)),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='produto.produto')),
                ('vendas', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venda.vendas')),
            ],
        ),
    ]
