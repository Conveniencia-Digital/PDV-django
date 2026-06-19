from django.db import models
from fornecedor.models import Fornecedores
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP



class Pecas(models.Model):
    TELAS = 'FN'
    CONECTORES = 'CB'
    BOTOES = 'CL'
    CARCACAS = 'IP'
    BATERIAS = 'CR'
    PLACAS = 'FT'
    SUBPLACAS = 'DV'
    CAMERAS = 'CM'
    FLEX = 'FL'
    AUTOFALANTES = 'AT'
    LENTES = 'LT'
    TAMPAS = 'TP'
    OUTROS = 'OT'
    CATEGORIAS_PECA = [
        (TELAS, 'Telas'),
        (CONECTORES, 'Conectores'),
        (BOTOES, 'Botoes'),
        (CARCACAS, 'Carcaças'),
        (BATERIAS, 'Baterias'),
        (PLACAS, 'Placas'),
        (SUBPLACAS, 'Sub-placas'),
        (CAMERAS, 'Cameras'),
        (FLEX, 'Flex'),
        (AUTOFALANTES, 'Auto-falantes'),
        (LENTES, 'Lentes'),
        (TAMPAS, 'Tampas'),  
        (OUTROS, 'Outros')
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
    nome_peca = models.CharField(max_length=99)
    preco_peca = models.DecimalField(max_digits=9, decimal_places=2)
    categoria_peca = models.CharField(max_length=2, choices=CATEGORIAS_PECA, null=True, blank=True)
    quantidade = models.IntegerField()
    codigo_de_barras = models.IntegerField(null=True, blank=True)
    preco_de_custo = models.DecimalField(max_digits=9, decimal_places=2)
    margem_de_lucro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=21, default=PIX)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    fornecedor = models.ForeignKey(Fornecedores, on_delete=models.CASCADE, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nome_peca

    def lucro(self):
         return f'R$ {self.preco_peca - self.preco_de_custo}'

    def margem_lucro_und(self):
        if self.preco_peca == 0:
            return Decimal('0.00')
        margem_und = ((self.preco_peca - self.preco_de_custo) / self.preco_peca) * 100
        return round(margem_und, 2)
    
    def precototal(self):
        return self.preco_de_custo * self.quantidade
  
    def lucrototal(self):
        return (self.preco_peca - self.preco_de_custo) * self.quantidade 
    
    def precototal(self):
        return self.preco_de_custo * self.quantidade

    def vendatotal(self):
        return self.preco_peca * self.quantidade

    def despesa_total_custo(self):
        return (self.preco_de_custo or Decimal('0.00')) * (self.quantidade or 0)

    def despesa_paga(self):
        total = self.despesa_total_custo()
        if self.forma_pagamento == self.FIADO:
            return min(self.valor_entrada or Decimal('0.00'), total)
        return total

    def despesa_a_pagar(self):
        if self.forma_pagamento != self.FIADO:
            return Decimal('0.00')
        return max(self.despesa_total_custo() - (self.valor_entrada or Decimal('0.00')), Decimal('0.00'))

    def saldodespesa(self):
        return self.despesa_a_pagar()

    def margem_lucro_total_percentual(self):
        try:
            vendatotal = Decimal(self.vendatotal() or Decimal('0.00'))
            lucrototal = Decimal(self.lucrototal() or Decimal('0.00'))

            if self.preco_peca == 0:
                return Decimal('0.00')
            margem = (lucrototal / vendatotal) * 100
            return margem.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ZeroDivisionError, TypeError, ValueError):
            return Decimal('0.00')
