from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .models import TaxaPagamento
from .forms import TaxaPagamentoForm
# Create your views here.


class Configuracao(TemplateView):
    template_name = 'configuracao/pagina-inicial-configuracao.html'

# views.py



@login_required
def cadastrar_taxas(request):
    taxas, _ = TaxaPagamento.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = TaxaPagamentoForm(request.POST, instance=taxas)
        if form.is_valid():
            form.save()
            return redirect("cadastrar_taxas")
    else:
        form = TaxaPagamentoForm(instance=taxas)

    return render(request, "taxas/form_taxas.html", {"form": form})
