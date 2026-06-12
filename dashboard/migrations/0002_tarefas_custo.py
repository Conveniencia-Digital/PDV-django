from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarefas',
            name='custo',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=9),
        ),
    ]
