from django.urls import path
from venda.views import cadastrarvendas, buscarpreco, addform, ListaVendas, apagaritemvenda, apagarvendas, DetalheVendas, editarvendas, valor_total_vendas, RelatorioLucro, TotalVendas, previewtaxacartaovenda

from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('vendas/', login_required(ListaVendas.as_view()), name='vendas'),
    path('cadastrarvendas/', login_required(cadastrarvendas), name='cadastrar-vendas'),
    path('editarvendas/<int:pk>/', login_required(editarvendas), name='editar-vendas'),
    path('produto/preco/', login_required(buscarpreco), name='preco-produto'),
    path('vendas/taxa-cartao/preview/', login_required(previewtaxacartaovenda), name='preview-taxa-cartao-vendas'),
    path('addform/', login_required(addform), name='addform'),
    path('apagaritemvenda/<int:pk>/', login_required(apagaritemvenda), name='apagar-item-venda'),
    path('apagarvendas/<int:pk>/', login_required(apagarvendas), name='apagar-vendas'),
    path('detalhevendas/<int:pk>', login_required(DetalheVendas.as_view()), name='detalhe-vendas'),
    path('totalvendas/', login_required(TotalVendas.as_view()), name='total-vendas' ),
    path('relatoriolucro/<int:pk>/', login_required(RelatorioLucro.as_view()), name='relatorio-lucro'),
    #path('vendas/atualizar/', login_required(atualizar_vendas), name='atualizar-vendas'),


   



]
