from django.db import models
from django.contrib.auth.models import User
from cliente.models import Cliente

class Pedido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    produto = models.CharField(max_length=100)
    valor_produto = models.DecimalField(max_digits=9, decimal_places=2)
    data_entrega = models.DateTimeField()
    valor_pago = models.DecimalField(max_digits=9, decimal_places=2)
