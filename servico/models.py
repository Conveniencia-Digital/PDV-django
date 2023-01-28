from django.db import models
from django.contrib.auth.models import User


class Servico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    servico = models.CharField(max_length=100)

    def __str__(self):
        return self.servico
   

