from django.db import models

class CategoriaDespesa(models.Model):
    nome_categoria_despesa = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.nome_categoria_despesa


class Despesa(models.Model):
    categoria_despesa = models.ForeignKey(CategoriaDespesa, on_delete=models.CASCADE, null=True, blank=True)
    nome_despesa = models.CharField(max_length=90)
    preco_despesa = models.DecimalField(max_digits=9, decimal_places=2)
   