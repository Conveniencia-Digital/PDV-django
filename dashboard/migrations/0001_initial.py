# Generated by Django 4.1 on 2022-09-05 23:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Servico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_servico', models.CharField(max_length=100)),
                ('preco_servico', models.DecimalField(decimal_places=2, max_digits=9)),
            ],
        ),
    ]
