from django.contrib.auth.decorators import login_required
from django.urls import path

from comunidade.views import ListaMensagem, enviarMensagem

urlpatterns = [
    path('comunidade/', login_required(ListaMensagem.as_view()), name='comunidade'),
    path('enviarmensagem/', login_required(enviarMensagem), name='enviar-mensagem'),
]
