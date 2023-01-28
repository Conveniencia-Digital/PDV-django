from django.urls import path
from django.contrib.auth.decorators import login_required

from servico.views import ListaServicos, cadastrarservico, apagarservico, editarservico

urlpatterns = [
    path('servicos/', login_required(ListaServicos.as_view()), name='servicos'),
    path('cadastrarservico/', login_required(cadastrarservico), name='cadastrar-servico'),
    path('editarservico/<int:pk>/', login_required(editarservico), name='editar-servico'),
    path('apagarservico/<int:pk>/', login_required(apagarservico), name='apagar-servico'),
]
