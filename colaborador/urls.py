from django.urls import path
from colaborador.views import ListaColaborador, cadastrarcolaborador, apagarcolaborador

urlpatterns = [
    path('colaborador/', ListaColaborador.as_view(), name='colaborador'),
    path('cadastrarcolaborador/', cadastrarcolaborador, name='cadastrar-colaborador'),
    path('apagarcolaborador/<int:pk>/', apagarcolaborador, name='apagar-colaborador'),

]
