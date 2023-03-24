from django.db import models
from cliente.models import Cliente
from colaborador.models import Colaborador
from django.contrib.auth.models import User


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

    class Meta:
        ordering = ('-pk',)

    
    def total(self):
        qs = self.lanhouse_items.filter(lanhouse=self.pk).values_list(
            'preco', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        desc = t - self.desconto
        return desc

            

class LanhouseServico(models.Model):
   usuario = models.ForeignKey(User, on_delete=models.PROTECT)
   data_criacao = models.DateTimeField(auto_now_add=True)
   data_edicao = models.DateTimeField(auto_now=True)
   servico = models.CharField(max_length=90)
   preco_custo = models.DecimalField(max_digits=9, decimal_places=2)
   preco = models.DecimalField(max_digits=9, decimal_places=2)


   def __str__(self):
       return self.servico
   

class ItemsLanhouse(models.Model):
    lanhouse = models.ForeignKey(LanhouseModel, on_delete=models.SET_NULL,
                                  related_name='lanhouse_items',
                                  blank=True,
                                  null=True)
    servico = models.ForeignKey(LanhouseServico, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)
    
    def __str__(self) -> str:
        return f'{self.pk} - {self.lanhouse.pk} - {self.servico}'
    
    def subtotal(self):
        return self.preco * self.quantidade

