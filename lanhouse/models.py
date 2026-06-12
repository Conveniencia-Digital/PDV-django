from django.db import models
from cliente.models import Cliente
from colaborador.models import Colaborador
from django.contrib.auth.models import User
from financeiro.models import CardMachine


class LanhouseModel(models.Model):
    PIX = 'Pix'
    CARTAO_CREDITO = 'Cartāo de credito'
    CARTAO_DEBITO = 'Cartāo de debito'
    DINHEIRO = 'Dinheiro'
    FIADO = 'Fiado a receber'
    FORMA_PAGAMENTO = [
        (PIX, 'Pix'),
        (CARTAO_CREDITO, 'Cartāo de credito'),
        (CARTAO_DEBITO, 'Cartāo de debito'),
        (DINHEIRO, 'Dinheiro'),
        (FIADO, 'Fiado a receber')
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    desconto = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=20, default=PIX)
    observacao = models.TextField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    card_machine = models.ForeignKey(CardMachine, on_delete=models.PROTECT, null=True, blank=True)
    card_payment_type = models.CharField(max_length=10, null=True, blank=True)
    card_installments = models.PositiveSmallIntegerField(null=True, blank=True)
    card_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    card_fee_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    card_base_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    card_final_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    pass_card_fee_to_customer = models.BooleanField(default=False)

    class Meta:
        ordering = ('-pk',)


    def total(self):
        if self.card_final_amount is not None:
            return self.card_final_amount
        from decimal import Decimal
        desconto = self.desconto or Decimal("0.00")
        qs = self.lanhouse_items.values_list("preco", "quantidade")
        total = sum(preco * qtd for preco, qtd in qs)
        return total - desconto

    def valor_base(self):
        if self.card_base_amount is not None:
            return self.card_base_amount
        from decimal import Decimal
        return max(self.total_sem_desconto() - (self.desconto or Decimal("0.00")), Decimal("0.00"))

    def total_sem_desconto(self):
        qs = self.lanhouse_items.values_list("preco", "quantidade")
        total = sum(preco * qtd for preco, qtd in qs)
        return total

    def custo_total(self):
        from decimal import Decimal
        return sum(
            (item.servico.preco_custo or Decimal("0.00")) * item.quantidade
            for item in self.lanhouse_items.select_related("servico").all()
        )

            

class LanhouseServico(models.Model):
   usuario = models.ForeignKey(User, on_delete=models.PROTECT)
   data_criacao = models.DateTimeField(auto_now_add=True)
   data_edicao = models.DateTimeField(auto_now=True)
   servico = models.CharField(max_length=90)
   preco_custo = models.DecimalField(max_digits=9, decimal_places=2)
   margem_de_lucro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
   preco = models.DecimalField(max_digits=9, decimal_places=2)

   class Meta:
       constraints = [
           models.UniqueConstraint(fields=['usuario', 'servico'], name='unique_lanhouse_servico_por_usuario')
       ]

   def __str__(self):
       return self.servico


class LanhouseSubmissionToken(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    finalidade = models.CharField(max_length=40)
    data_criacao = models.DateTimeField(auto_now_add=True)
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'finalidade', 'usado_em']),
        ]
   

class ItemsLanhouse(models.Model):
    lanhouse = models.ForeignKey(LanhouseModel, on_delete=models.SET_NULL,
                                  related_name='lanhouse_items',
                                  blank=True,
                                  null=True)
    servico = models.ForeignKey(LanhouseServico, on_delete=models.PROTECT)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)
    
    def __str__(self) -> str:
        return f'{self.pk} - {self.lanhouse.pk} - {self.servico}'
    
    def subtotal(self):
        return self.preco * self.quantidade
