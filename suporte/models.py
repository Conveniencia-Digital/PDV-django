from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Suporte (models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    mensagem = models.TextField()

    def __str__(self):
        return self.mensagem

