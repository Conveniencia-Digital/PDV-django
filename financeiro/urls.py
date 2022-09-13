from django.urls import path
from financeiro.views import ListaContasAReceber, cadastrarcontas_a_receber, editarcontas_a_receber, \
     apagarcontas_a_receber

urlpatterns = [
    path('financeiro', ListaContasAReceber.as_view(), name='financeiro'),
    path('cadastrarcontas_a_receber/', cadastrarcontas_a_receber, name='cadastrar-contas-a-receber'),
    path('editarcontas_a_receber/<int:pk>/', editarcontas_a_receber, name='editar-contas-a-receber'),
    path('apagarcontas_a_receber/<int:pk>/', apagarcontas_a_receber, name='apagar-contas-a-receber'),
]
