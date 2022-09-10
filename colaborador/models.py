from django.db import models


class Colaborador(models.Model):
    nome_colaborador = models.CharField(max_length=90)
