from django.urls import path
from orcamento.views import ListaOrcamento, cadastrarorcamento, adicionarlinhas

app_name = 'orcamento'

urlpatterns = [
    path('orcamento/', ListaOrcamento.as_view(), name='orcamento'),
    path('cadastrarorcamento/', cadastrarorcamento, name='cadastrar-orcamento'),
    path('adicionarlinhas/', adicionarlinhas, name='adicionar-linhas')
]
