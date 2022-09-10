from django.urls import path

from servico.views import ListaServicos, cadastrarservico, apagarservico, editarservico

urlpatterns = [
    path('servicos/', ListaServicos.as_view(), name='servicos'),
    path('cadastrarservico/', cadastrarservico, name='cadastrar-servico'),
    path('editarservico/<int:pk>/', editarservico, name='editar-servico'),
    path('apagarservico/<int:pk>/', apagarservico, name='apagar-servico'),
]
