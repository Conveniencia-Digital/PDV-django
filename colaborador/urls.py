from django.urls import path
from colaborador.views import ListaColaborador, cadastrarcolaborador, apagarcolaborador, editarcolaborador, DetalheColaboradorView, total_colaborador
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('colaborador/', login_required(ListaColaborador.as_view()), name='colaborador'),
    path('cadastrarcolaborador/', login_required(cadastrarcolaborador), name='cadastrar-colaborador'),
    path('editarcolaborador/<int:pk>/', login_required(editarcolaborador), name='editar-colaborador'),
    path('apagarcolaborador/<int:pk>/', login_required(apagarcolaborador), name='apagar-colaborador'),
    path('detalhecolaborador/<int:pk>/', login_required(DetalheColaboradorView.as_view()), name='detalhe-colaborador'),
    path('totalcolaboradores/', login_required(total_colaborador), name='total-colaborador'),

]
