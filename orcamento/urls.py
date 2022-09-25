from django.urls import path
from orcamento.views import ListaOrcamento, cadastrarorcamento, adicionarlinhas, apagarlinhas, precopeca

app_name = 'orcamento'

urlpatterns = [
    path('orcamento/', ListaOrcamento.as_view(), name='orcamento'),
    path('cadastrarorcamento/', cadastrarorcamento, name='cadastrar-orcamento'),
    path('adicionarlinhas/', adicionarlinhas, name='adicionar-linhas'),
    path('apagar/<int:pk>/linhasorcamento/', apagarlinhas, name='apagar-linhas'),
    path('preco/peca/', precopeca, name='preco-peca'),
]
