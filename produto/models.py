from django.db import models

# Create your models here.


class Produto(models.Model):
    nome = models.CharField(max_length=99)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return self.nome
