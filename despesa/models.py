from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from fornecedor.models import Fornecedores
from django.contrib.auth.models import User

class CategoriaDespesa(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    nome_categoria_despesa = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.nome_categoria_despesa


class Despesa(models.Model):
    TIPO_EMPRESA = 'despesa_empresa'
    TIPO_PROLABORE = 'prolabore'
    TIPO_DIVIDA = 'divida'
    TIPO_CHOICES = [
        (TIPO_EMPRESA, 'Empresa'),
        (TIPO_PROLABORE, 'Pró-labore'),
        (TIPO_DIVIDA, 'Dívida'),
    ]

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
    categoria_despesa = models.ForeignKey(CategoriaDespesa, on_delete=models.CASCADE, null=True, blank=True)
    nome_despesa = models.CharField(max_length=90)
    preco_despesa = models.DecimalField(max_digits=9, decimal_places=2)
    fornecedor = models.ForeignKey(Fornecedores, on_delete=models.CASCADE, null=True, blank=True)
    observacao = models.TextField(max_length=1000, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, editable=False)
    tipo = models.CharField(choices=TIPO_CHOICES, max_length=20, default=TIPO_EMPRESA)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=17, default=PIX)
    data_vencimento = models.DateField(null=True, blank=True)
    fiado_pago = models.BooleanField(default=False)
    despesa_fixa = models.BooleanField(default=False)
    dia_vencimento_fixo = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    qtd_parcela = models.IntegerField(null=True, blank=True)
    dia_vencimento_parcela = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    lanhouse_card_fee = models.OneToOneField(
        'lanhouse.LanhouseModel',
        on_delete=models.CASCADE,
        related_name='despesa_taxa_maquininha',
        null=True,
        blank=True,
    )
    venda_card_fee = models.OneToOneField(
        'venda.Vendas',
        on_delete=models.CASCADE,
        related_name='despesa_taxa_maquininha',
        null=True,
        blank=True,
    )
    orcamento_card_fee = models.OneToOneField(
        'orcamento.Orcamento',
        on_delete=models.CASCADE,
        related_name='despesa_taxa_maquininha',
        null=True,
        blank=True,
    )



    def saldodespesa(self):
        if self.forma_pagamento == self.FIADO and self.fiado_pago:
            return Decimal('0.00')
        return (self.preco_despesa or Decimal('0.00')) - (self.valor_entrada or Decimal('0.00'))

    def data_vencimento_fixo_no_mes(self, ano=None, mes=None):
        return self._data_vencimento_por_dia(self.dia_vencimento_fixo, ano, mes) if self.despesa_fixa else None

    def data_vencimento_parcela_no_mes(self, ano=None, mes=None):
        if not self.dia_vencimento_parcela:
            return None
        return self._data_vencimento_por_dia(self.dia_vencimento_parcela, ano, mes)

    def _data_vencimento_por_dia(self, dia_vencimento, ano=None, mes=None):
        if not dia_vencimento:
            return None
        hoje = timezone.localdate()
        ano = ano or hoje.year
        mes = mes or hoje.month
        ultimo_dia = monthrange(ano, mes)[1]
        dia = min(dia_vencimento, ultimo_dia)
        return date(ano, mes, dia)

    @property
    def data_referencia_vencimento(self):
        if self.despesa_fixa and self.dia_vencimento_fixo:
            return self.data_vencimento_fixo_no_mes()
        if self.forma_pagamento == self.FIADO and self.qtd_parcela and self.qtd_parcela > 1 and self.dia_vencimento_parcela:
            return self.data_vencimento_parcela_no_mes()
        return self.data_vencimento

    @property
    def fiado_status_label(self):
        if self.tipo == self.TIPO_DIVIDA:
            return 'Pago' if self.fiado_pago else 'Não pago'
        if self.forma_pagamento != self.FIADO:
            return ''
        return 'Pago' if self.fiado_pago else 'Não pago'

    @property
    def dias_para_vencimento(self):
        data_vencimento = self.data_referencia_vencimento
        if not data_vencimento:
            return None
        return (data_vencimento - timezone.localdate()).days

    @property
    def vencimento_status_label(self):
        if self.despesa_fixa and self.dia_vencimento_fixo:
            prefixo = 'Vencimento mensal'
        elif self.tipo == self.TIPO_DIVIDA and not self.fiado_pago:
            prefixo = 'Dívida'
        elif self.forma_pagamento == self.FIADO and self.qtd_parcela and self.qtd_parcela > 1 and not self.fiado_pago:
            prefixo = 'Fiado parcelado'
        elif self.forma_pagamento == self.FIADO and not self.fiado_pago:
            prefixo = 'Fiado'
        else:
            return ''

        dias = self.dias_para_vencimento
        if dias is None:
            return 'Sem vencimento informado'
        if dias == 0:
            return f'{prefixo}: vence hoje'
        if dias > 0:
            texto_dia = 'dia' if dias == 1 else 'dias'
            verbo = 'Falta' if dias == 1 else 'Faltam'
            return f'{prefixo}: {verbo} {dias} {texto_dia} para pagar'

        dias_atraso = abs(dias)
        texto_dia = 'dia' if dias_atraso == 1 else 'dias'
        return f'{prefixo}: {dias_atraso} {texto_dia} em atraso'
    
   
