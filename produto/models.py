from django.db import models
from fornecedor.models import Fornecedores


class Produto(models.Model):
    FONES = 'FN'
    CAPAS = 'CP'
    PELICULAS = 'PL'
    ADAPTADORES = 'AD'
    CABOS = 'CB'
    CELULARES = 'CL'
    IPHONES = 'IP'
    CARREGADORES = 'CR'
    FONTES = 'FT'
    DIVERSOS = 'DV'
    INFORMATICA = 'IN'
    CATEGORIAS_PRODUTOS = [
        (FONES, 'Fones'),
        (CABOS, 'Cabos'),
        (CAPAS, 'Capas'),
        (PELICULAS, 'Peliculas'),
        (ADAPTADORES, 'Adaptadores'),
        (CELULARES, 'Celulares'),
        (IPHONES, 'iPhones'),
        (CARREGADORES, 'Carregadores'),
        (FONTES, 'Fontes'),
        (DIVERSOS, 'Diversos'),
        (INFORMATICA, 'Informatica')     
    ]
    PIX = 'Cartāo de credito'
    CARTAO_CREDITO = 'Cartāo de credito'
    CARTAO_DEBITO = 'Cartāo de debito'
    DINHEIRO = 'Dinheiro'
    FIADO = 'Fiado a pagar'
    FORMA_PAGAMENTO = [
        (PIX, 'Pix'),
        (CARTAO_CREDITO, 'Cartāo de credito'),
        (CARTAO_DEBITO, 'Cartāo de debito'),
        (DINHEIRO, 'Dinheiro'),
        (FIADO, 'Fiado a pagar')
    ]
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    nome_produto = models.CharField(max_length=99)
    categoria_produtos = models.CharField(max_length=2, choices=CATEGORIAS_PRODUTOS, null=True, blank=True)
    quantidade = models.IntegerField()
    codigo_de_barras = models.IntegerField(null=True, blank=True)
    preco_de_custo = models.DecimalField(max_digits=9, decimal_places=2)
    preco = models.DecimalField(max_digits=9, decimal_places=2)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=21, default=PIX)
    fornecedor = models.ForeignKey(Fornecedores, on_delete=models.CASCADE, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.nome_produto

    def lucro(self):
        return self.preco - self.preco_de_custo 
