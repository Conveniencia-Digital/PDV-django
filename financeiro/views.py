from django.shortcuts import render
from django.views.generic import ListView

from financeiro.models import ContasAReceber
from financeiro.forms import ContasAReceberForms
from venda.models import Vendas
from orcamento.models import Orcamento



class ListaContasAReceber(ListView):
    model = ContasAReceber
    template_name = 'financeiro/pagina-inicial-contas-a-receber.html'

    def get_queryset(self):
        return ContasAReceber.objects.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ListaContasAReceber, self).get_context_data(**kwargs)
        context['venda'] = Vendas.objects.filter(forma_pagamento = 'Fiado a receber', usuario=self.request.user)
        context['orcamento'] = Orcamento.objects.filter(forma_pagamento = 'Fiado a receber', usuario=self.request.user)
        return context 


def cadastrarcontas_a_receber(request):
    template_name = 'financeiro/formularios/formulario-cadastrar-contas-a-receber.html'
    form = ContasAReceberForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            contas_a_receber = form.save()
            template_name = 'financeiro/tabela/linhas-tabela-contas-a-receber.html'

            context = {'object': contas_a_receber}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editarcontas_a_receber(request, pk):
    template_name = 'financeiro/formularios/formulario-editar-contas-a-receber.html'
    instance = ContasAReceber.objects.get(pk=pk)
    form = ContasAReceberForms(request.POST or None, instance=instance, initial={'usuario': request.user})
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            contas_a_receber = form.save()
            template_name = 'financeiro/tabela/linhas-tabela-contas-a-receber.html'
            context = {'object': contas_a_receber}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagarcontas_a_receber(request, pk):
    template_name = 'financeiro/tabela/tabela-contas-a-receber.html'
    obj = ContasAReceber.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
    else:
        raise PermissionError
    return render(request, template_name)
