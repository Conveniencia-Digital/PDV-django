from django.db import models
from django.utils import timezone
from cliente.models import Cliente
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q


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


class CategoriaLancamentoFinanceiro(models.Model):
    RECEITA = "income"
    DESPESA = "expense"
    TIPOS = [
        (RECEITA, "Receita"),
        (DESPESA, "Despesa"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPOS, default=RECEITA)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nome",)
        constraints = [
            models.UniqueConstraint(
                fields=("usuario", "nome", "tipo"),
                name="unique_categoria_lancamento_financeiro_usuario",
            )
        ]

    def __str__(self):
        return self.nome


class LancamentoFinanceiro(models.Model):
    RECEITA = CategoriaLancamentoFinanceiro.RECEITA
    DESPESA = CategoriaLancamentoFinanceiro.DESPESA
    TIPOS = CategoriaLancamentoFinanceiro.TIPOS

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    categoria = models.ForeignKey(CategoriaLancamentoFinanceiro, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPOS, default=RECEITA)
    descricao = models.CharField(max_length=160)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_lancamento = models.DateField(default=timezone.localdate)
    observacao = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-data_lancamento", "-created_at")
        indexes = [
            models.Index(fields=("usuario", "tipo", "data_lancamento")),
        ]

    def __str__(self):
        return self.descricao


class FechamentoCaixa(models.Model):
    BALANCEADO = "balanced"
    SOBRA = "cash_over"
    FALTA = "cash_shortage"
    STATUS = [
        (BALANCEADO, "Balanceado"),
        (SOBRA, "Sobra de Caixa"),
        (FALTA, "Falta de Caixa"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="fechamentos_caixa")
    data = models.DateField()
    saldo_abertura = models.DecimalField(max_digits=10, decimal_places=2)
    total_receitas = models.DecimalField(max_digits=10, decimal_places=2)
    total_despesas = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_esperado = models.DecimalField(max_digits=10, decimal_places=2)
    valor_contado = models.DecimalField(max_digits=10, decimal_places=2)
    diferenca = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default=BALANCEADO)
    observacao = models.TextField(null=True, blank=True)
    lancamento_sobra = models.ForeignKey(
        LancamentoFinanceiro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_sobra",
    )
    despesa_falta = models.ForeignKey(
        "despesa.Despesa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_falta",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-data", "-created_at")
        indexes = [
            models.Index(fields=("usuario", "data")),
            models.Index(fields=("usuario", "status", "data")),
        ]

    def __str__(self):
        return f"Fechamento {self.data:%d/%m/%Y}"


class CardMachine(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=90)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=["usuario", "name"], name="unique_card_machine_por_usuario"),
        ]

    def __str__(self):
        return self.name


class CardMachineFee(models.Model):
    PAYMENT_DEBIT = "debit"
    PAYMENT_CREDIT = "credit"
    PAYMENT_TYPES = [
        (PAYMENT_DEBIT, "Débito"),
        (PAYMENT_CREDIT, "Crédito"),
    ]

    card_machine = models.ForeignKey(CardMachine, on_delete=models.CASCADE, related_name="fees")
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES)
    installments = models.PositiveSmallIntegerField(null=True, blank=True)
    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("card_machine__name", "payment_type", "installments")
        constraints = [
            models.UniqueConstraint(
                fields=["card_machine", "payment_type"],
                condition=Q(payment_type="debit"),
                name="unique_debit_fee_por_maquininha",
            ),
            models.UniqueConstraint(
                fields=["card_machine", "payment_type", "installments"],
                condition=Q(payment_type="credit"),
                name="unique_credit_fee_parcela_por_maquininha",
            ),
        ]

    def __str__(self):
        if self.payment_type == self.PAYMENT_DEBIT:
            return f"{self.card_machine} - Débito {self.fee_percentage}%"
        return f"{self.card_machine} - Crédito {self.installments}x {self.fee_percentage}%"
