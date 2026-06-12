from django.urls import path
from django.contrib.auth.decorators import login_required
from lanhouse.views import ListaLanhouse, cadastrarlanhouse, cadastrarservicolanhouse, additemlanhouse,\
      ListaServicoLanhouse, apagarservicolanhouse, editarservicolanhouse, precoservicolanhouse, relatorio_lanhouse, editarlanhouse, DetalheLanhouse, apagarlanhouse, buscarservicoslanhouse, previewtaxacartaolanhouse

urlpatterns =  [
    path('lanhouse/', login_required(ListaLanhouse.as_view()), name='lanhouse'),
    path('cadastrarlanhouse/', login_required(cadastrarlanhouse), name='cadastrar-lanhouse' ),
    path('editarlanhouse/<int:pk>/', login_required(editarlanhouse), name='editar-lanhouse'),
    path('apagarlanhouse/<int:pk>/', login_required(apagarlanhouse), name='apagar-lanhouse'),
    path('detalhelanhouse/<int:pk>', login_required(DetalheLanhouse.as_view()), name='detalhe-lanhouse'),
    path('cadastrarservicolanhouse/', login_required(cadastrarservicolanhouse), name='cadastrar-servico-lanhouse'),
    path('servico/lanhouse/buscar/', login_required(buscarservicoslanhouse), name='buscar-servicos-lanhouse'),
    path('lanhouse/taxa-cartao/preview/', login_required(previewtaxacartaolanhouse), name='preview-taxa-cartao-lanhouse'),
    path('additemlanhouse/', login_required(additemlanhouse), name='add-item-lanhouse'),
    path('listaservicolanhouse/', login_required(ListaServicoLanhouse.as_view()), name='lista-servico-lanhouse'),
    path('apagarservicolanhouse/<int:pk>/', login_required(apagarservicolanhouse), name='apagar-servico-lanhouse'),
    path('editarservicolanhouse/<int:pk>/', login_required(editarservicolanhouse), name='editar-servico-lanhouse'),
    path('servico/lanhouse/preco/', login_required(precoservicolanhouse), name='preco-produto'),
    path('relatoriolanhouse/', relatorio_lanhouse, name='relatorio-lanhouse'),
    ]
    
