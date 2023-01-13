# Generated by Django 4.1.5 on 2023-01-13 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peca', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pecas',
            name='categoria_peca',
            field=models.CharField(blank=True, choices=[('FN', 'Telas'), ('CB', 'Conectores'), ('CL', 'Botoes'), ('IP', 'Carcaças'), ('CR', 'Baterias'), ('FT', 'Placas'), ('DV', 'Sub-placas'), ('CM', 'Cameras'), ('FL', 'Flex'), ('AT', 'Auto-falantes'), ('LT', 'Lentes'), ('TP', 'Tampas'), ('OT', 'Outros')], max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='pecas',
            name='codigo_de_barras',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
