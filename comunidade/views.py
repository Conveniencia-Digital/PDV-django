from django.shortcuts import render
from django.views.generic import ListView

from comunidade.forms import ComunidadeForms
from comunidade.models import Comunidade


class ListaMensagem(ListView):
    model = Comunidade
    template_name = 'comunidade/chat.html'


def enviarMensagem(request):
    template_name = 'comunidade/form-chat.html'
    form = ComunidadeForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            chat = form.save()
            template_name = 'comunidade/conversa-unica.html'
            context = {'object': chat}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)
