from django.contrib.auth.decorators import login_required
from django.urls import path

from dashboard.views import PaginaInicialView, apagartarefa, cadastrartarefa, editartarefa

urlpatterns = [
    path('', login_required(PaginaInicialView.as_view()), name='inicio'),
    path('cadastrartarefa/', login_required(cadastrartarefa), name='cadastrar-tarefa'),
    path('apagartarefa/<int:pk>/', login_required(apagartarefa), name='apagar-tarefa'),
    path('editartarefa/<int:pk>/', login_required(editartarefa), name='editar-tarefa'),
]
