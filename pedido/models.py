from django.db import models
from django.contrib.auth.models import User
from cliente.models import Cliente

class Pedido(models.Model):
    ENTREGUE = 'Entregue'
    CANCELADA = 'Cancelada'
    PROCESSAMENTO = 'Em processo'
    STATUS = [
        (ENTREGUE, 'Concluida e entregue'),
        (CANCELADA, 'Cancelada e estornada'),
        (PROCESSAMENTO, 'Em processo'),

    ]
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    produto = models.CharField(max_length=100)
    valor_produto = models.DecimalField(max_digits=9, decimal_places=2)
    data_entrega = models.DateField()
    valor_pago = models.DecimalField(max_digits=9, decimal_places=2)
    observacao = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=20, default=PROCESSAMENTO)


    def valor_a_receber(self):
        return self.valor_produto - self.valor_pago