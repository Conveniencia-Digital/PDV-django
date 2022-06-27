from django.urls import path
from .views import criarproduto, ListaProduto

urlpatterns = [
    path('produtos', ListaProduto.as_view(), name='produtos'),
    path('criarprodutos/', criarproduto, name='criar-produtos'),

]
