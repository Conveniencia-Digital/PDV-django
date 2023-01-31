from django.shortcuts import render
from django.views.generic import ListView
from suporte.models import Suporte
from suporte.forms import SuporteForms
from django.db.models import Q
from django.contrib.auth.models import User

# Create your views here.

class SuporteView(ListView):
    model = Suporte
    template_name = 'suporte/suporte.html'
    
    def get_queryset(self):
        user = self.request.user
        adm = User.objects.filter(is_staff=True)
        if user.is_staff:
            return Suporte.objects.all()
        else:
            return Suporte.objects.filter(Q(usuario=user) | Q(usuario__in=adm))
       


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