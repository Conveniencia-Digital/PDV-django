from django.db import models


class Produto(models.Model):
    FONES = 'FN'
    CABOS = 'CB'
    CELULARES = 'CL'
    IPHONES = 'IP'
    CARREGADORES = 'CR'
    FONTES = 'FT'
    DIVERSOS = 'DV'
    CATEGORIAS_PRODUTOS = [
        (FONES, 'Fones'),
        (CABOS, 'Cabos'),
        (CELULARES, 'Celulares'),
        (IPHONES, 'iPhones'),
        (CARREGADORES, 'Carregadores'),
        (FONTES, 'Fontes'),
        (DIVERSOS, 'Diversos')     
    ]

    nome_produto = models.CharField(max_length=99)
    categoria_produtos = models.CharField(max_length=2, choices=CATEGORIAS_PRODUTOS)
    quantidade = models.IntegerField()
    codigo_de_barras = models.IntegerField()
    preco_de_custo = models.DecimalField(max_digits=9, decimal_places=2)
    preco = models.DecimalField(max_digits=9, decimal_places=2)
    fornecedor = models.CharField(max_length=99, null=True, blank=True)


    def __str__(self):
        return self.nome_produto
