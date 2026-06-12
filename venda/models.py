from decimal import ROUND_HALF_UP, Decimal
from django.db import transaction
from django.db.models import F
from django.db import models
from produto.models import Produto
from cliente.models import Cliente
from colaborador.models import Colaborador
from django.contrib.auth.models import User
from financeiro.models import CardMachine



class Vendas(models.Model):
    ENTREGUE = 'Entregue'
    CANCELADA = 'Cancelada'
    TROCA = 'Troca de produto'
    RETORNO_GARANTIA = 'Retorno garantia'
    STATUS = [
        (ENTREGUE, 'Concluida e entregue'),
        (CANCELADA, 'Cancelada e estornada'),
        (TROCA, 'Troca de produto'),
        (RETORNO_GARANTIA, 'Retorno para garantia')

    ]
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
    status = models.CharField(choices=STATUS, max_length=20, default=ENTREGUE)
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

    def __str__(self):
        return self.cliente, self.vendedor
   
    """
     # funcao do regis
    def total(self):
        qs = self.vendas_items.filter(vendas=self.pk).values_list(
            'preco', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        desc = t - self.desconto
        return desc 
    """
    def total(self):
        if self.card_final_amount is not None:
            return self.card_final_amount
        desconto = self.desconto or Decimal("0.00")
        qs = self.vendas_items.values_list("preco", "quantidade")
        total = sum(preco * qtd for preco, qtd in qs)
        return total - desconto
    
    def total_sem_desconto(self): 
        qs = self.vendas_items.values_list("preco", "quantidade")
        total = sum(preco * qtd for preco, qtd in qs)
        return total

    def valor_a_receber(self):
        qs = self.vendas_items.filter(vendas=self.pk).values_list(
            'preco', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        desc = t - self.desconto
        return desc - self.valor_entrada
    

    def lucro_total(self):
        desconto = self.desconto or Decimal('0.00')
        lucro_itens = sum((item.preco - item.produto.preco_de_custo) * item.quantidade
                        for item in self.vendas_items.select_related('produto').all())
        
        if lucro_itens == 0:
            return Decimal('0.00')
        
        receita_bruta = sum(item.preco * item.quantidade for item in self.vendas_items.all())

        if receita_bruta == 0:
            return Decimal('0.00')
        
        #desconto_proporcao = (desconto / receita_bruta) if receita_bruta else Decimal('0.00')
        lucro_liquido = lucro_itens - desconto

        return Decimal(lucro_liquido).quantize(Decimal('0.01'))

    def margem_lucro_total_vendas(self):
        if self.desconto == 0:
            return Decimal('0.00')
        margem_vendas = (self.lucro_total() / self.total()) * 100
        return round(margem_vendas, 2)
    
    def margem_lucro_total_percentual(self):
        """
        Retorna a margem de lucro total da venda em % considerando o desconto.
        """
        lucro_liquido = self.lucro_total()  # já considera desconto proporcional
        total_venda = self.total() or Decimal('0.00')

        if total_venda == 0:
            return Decimal('0.00')

        margem = (lucro_liquido / total_venda) * 100
        return margem.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    #NOVAS FUNCOES CALCULO

    def custo_total(self):
        """
        Retorna o custo total dos produtos da venda
        """
        return sum(
            (item.produto.preco_de_custo or Decimal("0.00")) * item.quantidade
            for item in self.vendas_items.select_related("produto").all()
        )
    
    def cmv(self):
        return sum(
            (item.produto.preco_de_custo or Decimal("0.00")) * item.quantidade
            for item in self.vendas_items.select_related("produto"))


class VendasSubmissionToken(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    finalidade = models.CharField(max_length=40)
    data_criacao = models.DateTimeField(auto_now_add=True)
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'finalidade', 'usado_em']),
        ]

class ItemsVenda(models.Model):
    vendas = models.ForeignKey(Vendas,
                               on_delete=models.SET_NULL,
                               related_name='vendas_items',
                               blank=True,
                               null=True,
                               )
    produto = models.ForeignKey(Produto,
                                on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f'{self.pk} - {self.vendas.pk} - {self.produto}'

    def subtotal(self):
        return self.quantidade * self.preco
    
    def lucro_unitario(self):
        return (self.preco - self.produto.preco_de_custo)
    
    def lucro_total_item(self):
        return (self.preco - self.produto.preco_de_custo) * self.quantidade

    def save(self, *args, **kwargs):
        quantidade_atual = self.quantidade or 0
        produto_atual_id = self.produto_id
        item_anterior = None

        if self.pk:
            item_anterior = (
                ItemsVenda.objects
                .filter(pk=self.pk)
                .values('produto_id', 'quantidade')
                .first()
            )

        with transaction.atomic():
            super(ItemsVenda, self).save(*args, **kwargs)

            if item_anterior:
                produto_anterior_id = item_anterior['produto_id']
                quantidade_anterior = item_anterior['quantidade'] or 0

                if produto_anterior_id == produto_atual_id:
                    diferenca = quantidade_atual - quantidade_anterior
                    if diferenca:
                        Produto.objects.filter(pk=produto_atual_id).update(quantidade=F('quantidade') - diferenca)
                else:
                    Produto.objects.filter(pk=produto_anterior_id).update(quantidade=F('quantidade') + quantidade_anterior)
                    Produto.objects.filter(pk=produto_atual_id).update(quantidade=F('quantidade') - quantidade_atual)
            else:
                Produto.objects.filter(pk=produto_atual_id).update(quantidade=F('quantidade') - quantidade_atual)

    def delete(self, *args, **kwargs):
        produto_id = self.produto_id
        quantidade = self.quantidade or 0
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            if produto_id and quantidade:
                Produto.objects.filter(pk=produto_id).update(quantidade=F('quantidade') + quantidade)
            return result

    def margem_lucro_percentual(self):
        try:
            if self.preco == 0:
                return Decimal('0.00')
            margem = ((self.preco - self.produto.preco_de_custo) / self.preco) * 100
            return margem.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            return Decimal('0.00')
    
    
        



   


    





    





