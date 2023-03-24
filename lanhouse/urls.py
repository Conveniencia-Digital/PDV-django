from django.urls import path 
from django.contrib.auth.decorators import login_required
from lanhouse.views import ListaLanhouse, cadastrarlanhouse, cadastrarservicolanhouse, additemlanhouse, ListaServicoLanhouse, apagarservicolanhouse, editarservicolanhouse, precoservicolanhouse

urlpatterns =  [ 
    path('lanhouse/', login_required(ListaLanhouse.as_view()), name='lanhouse'),
    path('cadastrarlanhouse/', cadastrarlanhouse, name='cadastrar-lanhouse' ),
    path('cadastrarservicolanhouse/', cadastrarservicolanhouse, name='cadastrar-servico-lanhouse'),
    path('additemlanhouse/', additemlanhouse, name='add-item-lanhouse'),
    path('listaservicolanhouse/', ListaServicoLanhouse.as_view(), name='lista-servico-lanhouse'),
    path('apagarservicolanhouse/<int:pk>/', apagarservicolanhouse, name='apagar-servico-lanhouse'),
    path('editarservicolanhouse/<int:pk>/', editarservicolanhouse, name='editar-servico-lanhouse'),
    path('servico/lanhouse/preco/', (precoservicolanhouse), name='preco-produto'),
    ]
    