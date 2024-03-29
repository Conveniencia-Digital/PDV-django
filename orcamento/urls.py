from django.urls import path
from django.contrib.auth.decorators import login_required
from orcamento.views import ListaOrcamento, cadastrarorcamento, adicionarlinhas, preco_peca, apagaritemorcamento, \
      DetalheOrcamento, adicionarlinhaservico, editarorcamento, total_orcamento, cadastrarservico, ListaServicos

urlpatterns = [
    path('orcamento/', login_required(ListaOrcamento.as_view()), name='orcamento'),
    path('cadastrarorcamento/', login_required(cadastrarorcamento), name='cadastrar-orcamento'),
    path('editarorcamento/<int:pk>/', login_required(editarorcamento), name='editar-orcamento'),
    path('adicionarlinhas/', login_required(adicionarlinhas), name='adicionar-linhas'),
    path('adicionarlinhaservico/', login_required(adicionarlinhaservico), name='adicionar-linha-servico'),
    path('peca/preco/', login_required(preco_peca), name='preco-peca'),
    path('apagar-item/<int:pk>/orcamento/', login_required(apagaritemorcamento), name='apagar-item-orcamento'),
    path('detalheorcamento/<int:pk>', login_required(DetalheOrcamento.as_view()), name='detalhe-orcamento'),
    path('relatorioorcaamento/', total_orcamento, name='relatorio-orcamento'),
    path('cadastrarservico/', cadastrarservico, name='cadastrar-servico'),
    path('servico', ListaServicos.as_view(), name='servico')
    
]
