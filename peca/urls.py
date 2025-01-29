from django.contrib.auth.decorators import login_required
from django.urls import path

from peca.views import DetalhePeca, Peca, apagarpeca, cadastrarpeca, editarpeca, relatoriopeca

urlpatterns = [
    path('pecas/', login_required(Peca.as_view()), name='pecas'),
    path('cadastrarpeca/', login_required(cadastrarpeca), name='cadastrar-peca'),
    path('editarpeca/<int:pk>/', login_required(editarpeca), name='editar-peca'),
    path('detalhepeca/<int:pk>/', login_required(DetalhePeca.as_view()), name='detalhe-peca'),
    path('apagarpeca/<int:pk>/', login_required(apagarpeca), name='apagar-peca'),
    path('informacao-peca/', login_required(relatoriopeca), name='relatorio-peca'),


]
