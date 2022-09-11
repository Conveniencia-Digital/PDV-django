from django.urls import path
from colaborador.views import ListaColaborador, cadastrarcolaborador, apagarcolaborador, editarcolaborador

urlpatterns = [
    path('colaborador/', ListaColaborador.as_view(), name='colaborador'),
    path('cadastrarcolaborador/', cadastrarcolaborador, name='cadastrar-colaborador'),
    path('editarcolaborador/<int:pk>/', editarcolaborador, name='editar-colaborador'),
    path('apagarcolaborador/<int:pk>/', apagarcolaborador, name='apagar-colaborador'),

]
