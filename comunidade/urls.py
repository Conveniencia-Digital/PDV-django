from django.urls import path
from comunidade.views import enviarMensagem, ListaMensagem
from django.contrib.auth.decorators import login_required



urlpatterns = [
    path('comunidade/', login_required(ListaMensagem.as_view()), name='comunidade' ),
    path('enviarmensagem/', login_required(enviarMensagem), name='enviar-mensagem')
]