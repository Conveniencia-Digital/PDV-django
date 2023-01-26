from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True, editable=False)
    data_edicao = models.DateTimeField(auto_now=True, editable=False)
    nome_cliente = models.CharField(max_length=90)
    data_nascimento = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    telefone_contato = models.CharField(max_length=15)
    telefone_contato_2 = models.CharField(max_length=15, null=True, blank=True)
    rua = models.CharField(max_length=99, null=True, blank=True)
    numero_casa = models.IntegerField(null=True, blank=True)
    bairro = models.CharField(max_length=90, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nome_cliente
