from django.db import models
from fornecedor.models import Fornecedores
from django.contrib.auth.models import User



class Produto(models.Model):
    FONES = 'Fones'
    CAPAS = 'Capas'
    PELICULAS = 'Peliculas'
    ADAPTADORES = 'Adaptadores'
    CABOS = 'Cabos'
    CELULARES = 'Celulares'
    IPHONES = 'iPhones'
    CARREGADORES = 'Carregadores'
    FONTES = 'Fontes'
    DIVERSOS = 'Diversos'
    INFORMATICA = 'Informatica'
    CAIXA_SOM = 'Caixa de som'
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
        (INFORMATICA, 'Informatica'),    
        (CAIXA_SOM, 'Caixa de som')     
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

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    nome_produto = models.CharField(max_length=99)
    categoria_produtos = models.CharField(max_length=20, choices=CATEGORIAS_PRODUTOS, null=True, blank=True)
    quantidade = models.IntegerField()
    codigo_de_barras = models.IntegerField(null=True, blank=True)
    preco_de_custo = models.DecimalField(max_digits=9, decimal_places=2)
    preco = models.DecimalField(max_digits=9, decimal_places=2)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=21, default=PIX)
    fornecedor = models.ForeignKey(Fornecedores, on_delete=models.CASCADE, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)



    def __str__(self):
        return self.nome_produto

    def lucro(self):
        return self.preco - self.preco_de_custo

    def lucrototal(self):
        return (self.preco - self.preco_de_custo) * self.quantidade 
    
    def precototal(self):
        return self.preco_de_custo * self.quantidade

    def vendatotal(self):
        return self.preco * self.quantidade

    def saldodespesa(self):
        return (self.preco_de_custo * self.quantidade) - self.valor_entrada


    
