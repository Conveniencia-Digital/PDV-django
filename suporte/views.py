from django.shortcuts import render
from django.views.generic import ListView
from suporte.models import Suporte
from suporte.forms import SuporteForms

# Create your views here.

class Suporte(ListView):
    model = Suporte
    template_name = 'suporte/suporte.html'
    
    def get_queryset(self):
        return Suporte.objects.filter(usuario=self.request.user)
    


def enviarsuporte(request):
    template_name = 'suporte/form-suporte.html'
    form = SuporteForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            suporte = form.save()
            context = {'object': suporte}
            template_name = 'suporte/mensagem-suporte.html'
            return render(request, template_name, context)
    
    context = {'form': form}
    return render(request, template_name, context)