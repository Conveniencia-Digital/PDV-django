# Generated by Django 4.1 on 2022-08-31 18:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venda', '0002_auto_20220810_1400'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemsvenda',
            options={'ordering': ('pk',)},
        ),
    ]