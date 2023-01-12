from django.db import models


class Colaborador(models.Model):
    nome_colaborador = models.CharField(max_length=90)
    data_criacao = models.DateTimeField(auto_now_add=True, editable=False)
    data_edicao = models.DateTimeField(auto_now=True, editable=False)
    data_nascimento = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    telefone_contato = models.CharField(max_length=15)
    telefone_contato_2 = models.CharField(max_length=15, null=True, blank=True)
    rua = models.CharField(max_length=99, null=True, blank=True)
    numero_casa = models.IntegerField(null=True, blank=True)
    bairro = models.CharField(max_length=90, null=True, blank=True)
    cargo = models.CharField(max_length=90, null=True, blank=True)
    salario = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    data_pagamento = models.DateField(null=True, blank=True)


