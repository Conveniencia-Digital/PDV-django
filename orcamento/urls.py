from django.urls import path
from orcamento.views import ListaOrcamento, cadastrarorcamento, adicionarlinhas, preco_peca, apagaritemorcamento, DetalheOrcamento, adicionarlinhaservico

urlpatterns = [
    path('orcamento/', ListaOrcamento.as_view(), name='orcamento'),
    path('cadastrarorcamento/', cadastrarorcamento, name='cadastrar-orcamento'),
    path('adicionarlinhas/', adicionarlinhas, name='adicionar-linhas'),
    path('adicionarlinhaservico/', adicionarlinhaservico, name='adicionar-linha-servico'),
    path('peca/preco/', preco_peca, name='preco-peca'),
    path('apagar-item/<int:pk>/orcamento/', apagaritemorcamento, name='apagar-item-orcamento'),
    path('detalheorcamento/<int:pk>', DetalheOrcamento.as_view(), name='detalhe-orcamento'),
]
