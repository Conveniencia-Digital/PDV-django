from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


telefone_validator = RegexValidator(
    regex=r'^\(\d{2}\) \d{4,5}-\d{4}$',
    message='Informe um telefone no formato (00) 00000-0000 ou (00) 0000-0000.',
)


class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True, editable=False)
    data_edicao = models.DateTimeField(auto_now=True, editable=False)
    nome_cliente = models.CharField(max_length=90)
    data_nascimento = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    telefone_contato = models.CharField(max_length=15, null=True, blank=True, validators=[telefone_validator])
    telefone_contato_2 = models.CharField(max_length=15, null=True, blank=True, validators=[telefone_validator])
    rua = models.CharField(max_length=99, null=True, blank=True)
    numero_casa = models.IntegerField(null=True, blank=True)
    bairro = models.CharField(max_length=90, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nome_cliente
