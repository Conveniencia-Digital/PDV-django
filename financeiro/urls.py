from django.urls import path
from financeiro.views import ListaContasAReceber, cadastrarcontas_a_receber, editarcontas_a_receber, \
     apagarcontas_a_receber

from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('financeiro', login_required(ListaContasAReceber.as_view()), name='financeiro'),
    path('cadastrarcontas_a_receber/', login_required(cadastrarcontas_a_receber), name='cadastrar-contas-a-receber'),
    path('editarcontas_a_receber/<int:pk>/', login_required(editarcontas_a_receber), name='editar-contas-a-receber'),
    path('apagarcontas_a_receber/<int:pk>/', login_required(apagarcontas_a_receber), name='apagar-contas-a-receber'),
]
