from django.urls import path
from django.contrib.auth.decorators import login_required
from orcamento.views import ListaOrcamento, cadastrarorcamento, adicionarlinhas, preco_peca, apagaritemorcamento, \
      DetalheOrcamento, adicionarlinhaservico, editarorcamento, total_orcamento, cadastrarservico, ListaServicos, \
      apagarservico, apagarorcamento, buscarservicosorcamento, previewtaxacartaoorcamento, RelatorioOrcamentoIndividual, \
      RelatorioLucroOrcamento

urlpatterns = [
    path('orcamento/', login_required(ListaOrcamento.as_view()), name='orcamento'),
    path('cadastrarorcamento/', login_required(cadastrarorcamento), name='cadastrar-orcamento'),
    path('editarorcamento/<int:pk>/', login_required(editarorcamento), name='editar-orcamento'),
    path('apagarorcamento/<int:pk>/', login_required(apagarorcamento), name='apagar-orcamento'),
    path('adicionarlinhas/', login_required(adicionarlinhas), name='adicionar-linhas'),
    path('adicionarlinhaservico/', login_required(adicionarlinhaservico), name='adicionar-linha-servico'),
    path('peca/preco/', login_required(preco_peca), name='preco-peca'),
    path('orcamento/servico/buscar/', login_required(buscarservicosorcamento), name='buscar-servicos-orcamento'),
    path('orcamento/taxa-cartao/preview/', login_required(previewtaxacartaoorcamento), name='preview-taxa-cartao-orcamento'),
    path('apagar-item/<int:pk>/orcamento/', login_required(apagaritemorcamento), name='apagar-item-orcamento'),
    path('detalheorcamento/<int:pk>', login_required(DetalheOrcamento.as_view()), name='detalhe-orcamento'),
    path('orcamento/<int:pk>/relatorio/', login_required(RelatorioOrcamentoIndividual.as_view()), name='relatorio-orcamento-individual'),
    path('orcamento/<int:pk>/lucro/', login_required(RelatorioLucroOrcamento.as_view()), name='relatorio-lucro-orcamento'),
    path('relatorioorcaamento/', total_orcamento, name='relatorio-orcamento'),
    path('cadastrarservico/', login_required(cadastrarservico), name='cadastrar-servico'),
    path('servico', login_required(ListaServicos.as_view()), name='servico'),
    path('apagarservico/<int:pk>/', login_required(apagarservico), name='apagarservico')
    
]
