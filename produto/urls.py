from django.urls import path
from .views import (
    DetalheProduto,
    ListaProduto,
    apagarprodutos,
    buscarcategoriasproduto,
    buscarprodutos,
    criarcategoriaproduto,
    criarprodutos,
    editarprodutos,
)
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('produtos', login_required(ListaProduto.as_view()), name='produtos'),
    path('produto/buscar/', login_required(buscarprodutos), name='buscar-produtos'),
    path('produto/categorias/buscar/', login_required(buscarcategoriasproduto), name='buscar-categorias-produto'),
    path('produto/categorias/criar/', login_required(criarcategoriaproduto), name='criar-categoria-produto'),
    path('criarprodutos/', login_required(criarprodutos), name='criar-produtos'),
    path('<int:pk>/editarprodutos/', login_required(editarprodutos), name='editar-produtos'),
    path('<int:pk>/apagarprodutos/', login_required(apagarprodutos), name='apagar-produtos'),
    path('detalheproduto/<int:pk>/', DetalheProduto.as_view(), name='detalhe-produto')

]
