from django.db import models
from fornecedor.models import Fornecedores
from django.contrib.auth.models import User

class CategoriaDespesa(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    nome_categoria_despesa = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.nome_categoria_despesa


class Despesa(models.Model):
    PIX = 'Pix'
    CARTAO_CREDITO = 'Cartāo de credito'
    CARTAO_DEBITO = 'Cartāo de debito'
    DINHEIRO = 'Dinheiro'
    FIADO = 'Fiado a pagar'
    FORMA_PAGAMENTO = [
        (PIX, 'Pix'),
        (CARTAO_CREDITO, 'Cartāo de credito'),
        (CARTAO_DEBITO, 'Cartāo de debito'),
        (DINHEIRO, 'Dinheiro'),
        (FIADO, 'Fiado')
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    categoria_despesa = models.ForeignKey(CategoriaDespesa, on_delete=models.CASCADE, null=True, blank=True)
    nome_despesa = models.CharField(max_length=90)
    preco_despesa = models.DecimalField(max_digits=9, decimal_places=2)
    fornecedor = models.ForeignKey(Fornecedores, on_delete=models.CASCADE, null=True, blank=True)
    observacao = models.TextField(max_length=1000, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, editable=False)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=17, default=PIX)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    
   