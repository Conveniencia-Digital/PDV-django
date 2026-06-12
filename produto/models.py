from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.db import models
from fornecedor.models import Fornecedores
from django.contrib.auth.models import User


DEFAULT_CATEGORIAS_PRODUTOS = [
    ('Fones', 'Fones'),
    ('Cabos', 'Cabos'),
    ('Capas', 'Capas'),
    ('Peliculas', 'Peliculas'),
    ('Adaptadores', 'Adaptadores'),
    ('Celulares', 'Celulares'),
    ('iPhones', 'iPhones'),
    ('Carregadores', 'Carregadores'),
    ('Fontes', 'Fontes'),
    ('Diversos', 'Diversos'),
    ('Informatica', 'Informatica'),
    ('Caixa de som', 'Caixa de som'),
    ('Copos | Garrafas', 'Copos | Garrafas'),
    ('Relogios', 'Relogios'),
    ('Brinquedos', 'Brinquedos'),
    ('Perfumes', 'Perfumes'),
]



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
    COPOS_GARRAFAS = 'Copos | Garrafas'
    RELOGIOS = 'Relogios'
    BRINQUEDOS = 'Brinquedos'
    PERFUMES = 'Perfumes'
    CATEGORIAS_PRODUTOS = DEFAULT_CATEGORIAS_PRODUTOS
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
        (FIADO, 'Fiado a pagar')
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    nome_produto = models.CharField(max_length=99)
    categoria = models.ForeignKey(
        'CategoriaProduto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
    )
    categoria_produtos = models.CharField(max_length=100, null=True, blank=True)
    quantidade = models.IntegerField()
    codigo_de_barras = models.IntegerField(null=True, blank=True)
    preco_de_custo = models.DecimalField(max_digits=9, decimal_places=2)
    margem_de_lucro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    preco = models.DecimalField(max_digits=9, decimal_places=2)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=21, default=PIX)
    fornecedor = models.ForeignKey(Fornecedores, on_delete=models.CASCADE, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)



    def __str__(self):
        return self.nome_produto

    def save(self, *args, **kwargs):
        if self.categoria_id and self.categoria:
            self.categoria_produtos = self.categoria.nome
        super().save(*args, **kwargs)

    def lucro(self):
        return self.preco - self.preco_de_custo
    
    def margem_lucro_und(self):
        if self.preco == 0:
            return Decimal('0.00')
        margem_und = ((self.preco - self.preco_de_custo) / self.preco) * 100
        return round(margem_und,2)

    def lucrototal(self):
        return (self.preco - self.preco_de_custo) * self.quantidade 
    
    def precototal(self):
        return self.preco_de_custo * self.quantidade

    def vendatotal(self):
        return self.preco * self.quantidade

    def saldodespesa(self):
        return (self.preco_de_custo * self.quantidade) - (self.valor_entrada or Decimal('0.00'))
    
    def qtdproduto(self):
        return(self.quantidade)
    
    def margem_lucro_total_percentual(self):

        try:

            vendatotal = self.vendatotal() or Decimal('0.00')
            lucrototal = self.lucrototal() or Decimal('0.00')

            vendatotal = Decimal(vendatotal)
            lucrototal = Decimal(lucrototal)

            if self.preco == 0:
                return Decimal('0.00')
            margem = (lucrototal / vendatotal) * 100
            margem = margem.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return margem
        
        except (InvalidOperation, ZeroDivisionError, TypeError, ValueError):
            return Decimal('0.00')

    
    
    


    

class CategoriaProduto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    nome = models.CharField(max_length=100)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('nome',)
        constraints = [
            models.UniqueConstraint(
                fields=('usuario', 'nome'),
                name='unique_categoria_produto_por_usuario',
            )
        ]

    def __str__(self):
        return self.nome


def ensure_default_categories(user):
    if not user or not getattr(user, 'pk', None):
        return

    existentes = set(
        CategoriaProduto.objects.filter(usuario=user).values_list('nome', flat=True)
    )
    CategoriaProduto.objects.bulk_create(
        [
            CategoriaProduto(usuario=user, nome=nome)
            for nome, _label in DEFAULT_CATEGORIAS_PRODUTOS
            if nome not in existentes
        ],
        ignore_conflicts=True,
    )
