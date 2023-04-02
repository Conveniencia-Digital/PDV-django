from django.db import models
from cliente.models import Cliente
from django.contrib.auth.models import User


class ContasAReceber(models.Model):
    PAGO = 'Pago'
    A_RECEBER = 'A receber'
    CALOTE = 'Calote'
    STATUS = [
        (PAGO, 'Pago'),
        (A_RECEBER, 'A receber'),
        (CALOTE, 'Calote'),
        
    ]
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nome_contas_a_receber = models.CharField(max_length=90)
    preco_contas_a_receber = models.DecimalField(max_digits=9, decimal_places=2)
    observacao = models.TextField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=20, default=A_RECEBER)


    def valorareceber(self):
        return self.preco_contas_a_receber - self.valor_entrada

