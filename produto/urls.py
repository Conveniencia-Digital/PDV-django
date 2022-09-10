from django.urls import path
from .views import criarprodutos, ListaProduto, editarprodutos, apagarprodutos

urlpatterns = [
    path('produtos', ListaProduto.as_view(), name='produtos'),
    path('criarprodutos/', criarprodutos, name='criar-produtos'),
    path('<int:pk>/editarprodutos/', editarprodutos, name='editar-produtos'),
    path('<int:pk>/apagarprodutos/', apagarprodutos, name='apagar-produtos'),

]
