from django.shortcuts import render
from django.views.generic import ListView, CreateView
from despesa.forms import DespesaForms, CategoriaDespesaForms
from despesa.models import Despesa
from peca.models import Pecas
from produto.models import Produto


class ListaDespesa(ListView):
    model = Despesa
    template_name = 'despesa/pagina-inicial-despesa.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super(ListaDespesa, self).get_context_data(**kwargs)
        context['peca'] = Pecas.objects.filter(forma_pagamento='Fiado a pagar') 
        context['produto'] = Produto.objects.filter(forma_pagamento='Fiado a pagar') 
        return context

   
def cadastrardespesa(request):
    template_name = 'despesa/formularios/formulario-cadastrar-despesa.html'
    form = DespesaForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save()
            template_name = 'despesa/tabela/linhas-tabela-despesa.html'

            context = {'object': despesa}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


class CategoriaDespesa(CreateView):
    form_class = CategoriaDespesaForms
    template_name = 'despesa/formularios/formulario-categoria-despesa.html'



def editardespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-despesa.html'
    instance = Despesa.objects.get(pk=pk)
    form = DespesaForms(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save()
            template_name = 'despesa/tabela/linhas-tabela-despesa.html'
            context = {'object': despesa}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagardespesa(request, pk):
    template_name = 'despesa/tabela/tabela-despesa.html'
    obj = Despesa.objects.get(pk=pk)
    obj.delete()
    return render(request, template_name)


