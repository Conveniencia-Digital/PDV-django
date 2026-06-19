# Generated manually on 2026-06-18

from django.db import migrations, models
import django.core.validators


telefone_validator = django.core.validators.RegexValidator(
    regex=r'^\(\d{2}\) \d{4,5}-\d{4}$',
    message='Informe um telefone no formato (00) 00000-0000 ou (00) 0000-0000.',
)


def limpar_telefones_clientes(apps, schema_editor):
    Cliente = apps.get_model('cliente', 'Cliente')
    Cliente.objects.update(telefone_contato=None, telefone_contato_2=None)


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='telefone_contato',
            field=models.CharField(
                blank=True,
                max_length=15,
                null=True,
                validators=[telefone_validator],
            ),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='telefone_contato_2',
            field=models.CharField(
                blank=True,
                max_length=15,
                null=True,
                validators=[telefone_validator],
            ),
        ),
        migrations.RunPython(limpar_telefones_clientes, migrations.RunPython.noop),
    ]
