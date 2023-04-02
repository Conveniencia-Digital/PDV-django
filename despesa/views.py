from django.shortcuts import render
from django.views.generic import ListView, DetailView
from despesa.forms import DespesaForms, CategoriaDespesaForms
from despesa.models import Despesa, CategoriaDespesa
from peca.models import Pecas
from produto.models import Produto
from django.contrib.auth.decorators import login_required


class ListaDespesa(ListView):
    model = Despesa
    template_name = 'despesa/pagina-inicial-despesa.html'
    context_object_name = 'object'

    def get_queryset(self):
        return Despesa.objects.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ListaDespesa, self).get_context_data(**kwargs)
        context['peca'] = Pecas.objects.filter(forma_pagamento='Fiado a pagar', usuario=self.request.user) 
        context['produto'] = Produto.objects.filter(forma_pagamento='Fiado a pagar', usuario=self.request.user) 
        return context



@login_required   
def cadastrardespesa(request):
    template_name = 'despesa/formularios/formulario-cadastrar-despesa.html'
    form = DespesaForms(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save()
            template_name = 'despesa/tabela/linhas-tabela-despesa.html'

            context = {'object': despesa}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)



@login_required
def editardespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-despesa.html'
    instance = Despesa.objects.get(pk=pk)
    form = DespesaForms(request.POST or None, instance=instance, initial={'usuario': request.user}, user=request.user)
    
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save()
            template_name = 'despesa/tabela/linhas-tabela-despesa.html'
            context = {'object': despesa}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)



@login_required
def apagardespesa(request, pk):
    template_name = 'despesa/tabela/tabela-despesa.html'
    obj = Despesa.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
    else:
        raise PermissionError
    return render(request, template_name)




@login_required
def cadastrarcategoriadespesa(request):
    template_name = 'despesa/formularios/formulario-categoria-despesa.html'
    form = CategoriaDespesaForms(request.POST or None, initial={'usuario':request.user})
    
    if request.method == 'POST':
        if form.is_valid():
            template_name = 'despesa/tabela/linha-categoria-despesa.html'
            categoria_despesa = form.save()
            context = {'object': categoria_despesa}
            return render(request, template_name, context)
    
    context = {'form': form}
    return render(request, template_name, context)




@login_required
def apagarcategoriadespesa(request, pk):
    template_name = 'despesa/tabela/categoria-despesa.html'
    obj = CategoriaDespesa.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
        return render(request, template_name)
    else:
        raise PermissionError

    

class ListaCategoriaDespesa(ListView):
    model = CategoriaDespesa
    template_name = 'despesa/tabela/tabela-categoria-despesa.html'
    context_object_name = 'object'

    def get_queryset(self):
        return CategoriaDespesa.objects.filter(usuario=self.request.user)



@login_required
def editarcatergoriadespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-categoria-despesa.html'
    instance = CategoriaDespesa.objects.get(pk=pk)
    form = CategoriaDespesaForms(request.POST or None, initial={'usuario': request.user}, instance=instance)
    if instance.usuario != request.user:
        raise PermissionError
    if request.method == 'POST':
        if form.is_valid():
            template_name = 'despesa/tabela/linha-categoria-despesa.html'
            categoria_despesa = form.save()
            context = {'object': categoria_despesa}
            return render(request, template_name, context)
        

    context = {'form': form, 'object':instance}
    return render(request, template_name, context)


class DetalheDespesaProduto(DetailView):
    model = Produto
    template_name = 'despesa/off-canvas/canvas-despesa-produto.html'



class DetalheDespesaPeca(DetailView):
    model = Pecas
    template_name = 'despesa/off-canvas/canvas-despesa-peca.html'



class DetalheDespesa(DetailView):
    model = Despesa
    template_name = 'despesa/off-canvas/canvas-despesa.html'

