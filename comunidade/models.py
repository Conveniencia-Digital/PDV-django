from django.contrib.auth.models import User
from django.db import models


class Comunidade(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    mensagem = models.TextField()

    def __str__(self) -> str:
        return self.mensagem
