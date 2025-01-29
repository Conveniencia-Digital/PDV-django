from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import DetalheProduto, ListaProduto, apagarprodutos, criarprodutos, editarprodutos

urlpatterns = [
    path('produtos', login_required(ListaProduto.as_view()), name='produtos'),
    path('criarprodutos/', login_required(criarprodutos), name='criar-produtos'),
    path('<int:pk>/editarprodutos/', login_required(editarprodutos), name='editar-produtos'),
    path('<int:pk>/apagarprodutos/', login_required(apagarprodutos), name='apagar-produtos'),
    path('detalheproduto/<int:pk>/', DetalheProduto.as_view(), name='detalhe-produto'),
]
