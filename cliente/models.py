from django.db import models


class Cliente(models.Model):
    nome_cliente = models.CharField(max_length=90)

    def __str__(self):
        return self.nome_cliente
