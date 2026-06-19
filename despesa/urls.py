from django.urls import path
from despesa.views import ListaDespesa, cadastrardespesa, cadastrarprolabore, cadastrardivida, editardespesa, apagardespesa, cadastrarcategoriadespesa, buscarcategoriasdespesa, ListaCategoriaDespesa, \
                         apagarcategoriadespesa, editarcatergoriadespesa, DetalheDespesaProduto, DetalheDespesaPeca, DetalheDespesa
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('despesa/', login_required(ListaDespesa.as_view()), name='despesa'),
    path('categoriadespesa/', login_required(cadastrarcategoriadespesa), name='categoria-despesa'),
    path('despesa/categorias/buscar/', login_required(buscarcategoriasdespesa), name='buscar-categorias-despesa'),
    path('cadastrardespesa/', login_required(cadastrardespesa), name='cadastrar-despesa'),
    path('cadastrarprolabore/', login_required(cadastrarprolabore), name='cadastrar-prolabore'),
    path('cadastrardivida/', login_required(cadastrardivida), name='cadastrar-divida'),
    path('editardespesa/<int:pk>/', login_required(editardespesa), name='editar-despesa'),
    path('apagardespesa/<int:pk>/', login_required(apagardespesa), name='apagar-despesa'),
    path('listacategoriadespesa/', login_required(ListaCategoriaDespesa.as_view()), name='lista-categoria-despesa'),
    path('apagarcategoriadespesa/<int:pk>/', login_required(apagarcategoriadespesa), name='apagar-categoria-despesa'),
    path('editarcategoriadespesa/<int:pk>/', login_required(editarcatergoriadespesa), name= 'editar-categoria-despesa'),
    path('detalhedespesaproduto/<int:pk>/', login_required(DetalheDespesaProduto.as_view()), name='detalhe-despesa-produto'),
    path('detalhedespesapeca/<int:pk>/', login_required(DetalheDespesaPeca.as_view()), name='detalhe-despesa-peca'),
    path('detalhedespesa/<int:pk>/', login_required(DetalheDespesa.as_view()), name='detalhe-despesa'),
   
]
