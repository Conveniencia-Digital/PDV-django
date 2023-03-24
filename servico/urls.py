from django.urls import path
from django.contrib.auth.decorators import login_required

from servico.views import ListaServico, cadastrarservico, editarservico, apagarservico

urlpatterns = [
    path('cadastrarservico/', login_required(cadastrarservico), name='cadastrar-servico'),
    path('editarservico/<int:pk>/', login_required(editarservico), name='editar-servico'),
    path('apagarservico/<int:pk>/', login_required(apagarservico), name='apagar-servico'),
    path('servicos/', login_required(ListaServico.as_view()), name='servicos'),
]
