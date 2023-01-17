from django.db import models

# Create your models here.

class Fornecedores(models.Model):
    data_criacao = models.DateTimeField(auto_now_add=True, editable=False)
    data_edicao = models.DateTimeField(auto_now=True, editable=False)
    nome_fornecedor = models.CharField(max_length=90)
    cnpj = models.CharField(max_length=20, null=True, blank=True)
    telefone_contato = models.CharField(max_length=15)
    telefone_contato_2 = models.CharField(max_length=15, null=True, blank=True)
    rua = models.CharField(max_length=99, null=True, blank=True)
    numero_casa = models.IntegerField(null=True, blank=True)
    bairro = models.CharField(max_length=90, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nome_fornecedor
