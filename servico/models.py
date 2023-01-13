from django.db import models


class Servico(models.Model):
    nome_servico = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_servico
   

