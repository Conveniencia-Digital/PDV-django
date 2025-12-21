from django.conf import settings
from django.db import models

class TaxaPagamento(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    pix = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    debito = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    credito_1x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_2x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_3x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_4x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_5x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_6x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_7x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_8x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_9x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_10x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_11x = models.DecimalField(max_digits=5, decimal_places=2)
    credito_12x = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Taxas - {self.user}"
