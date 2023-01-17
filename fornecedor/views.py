from django.shortcuts import render
from django.views.generic import ListView

from fornecedor.models import Fornecedores
from fornecedor.forms import FornecedorForm


class ListaFornecedor(ListView):
    model = Fornecedores
    template_name = 'fornecedor/pagina-inicial-fornecedor.html'


def cadastrarfornecedor(request):
    template_name = 'fornecedor/formularios/formulario-cadastrar-fornecedor.html'
    form = FornecedorForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            fornecedor = form.save()
            template_name = 'fornecedor/tabela/linhas-tabela-fornecedor.html'

            context = {'object': fornecedor}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editarfornecedor(request, pk):
    template_name = 'fornecedor/formularios/formulario-editar-fornecedor.html'
    instance = Fornecedores.objects.get(pk=pk)
    form = FornecedorForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            fornecedor = form.save()
            template_name = 'fornecedor/tabela/linhas-tabela-fornecedor.html'
            context = {'object': fornecedor}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagarfornecedor(request, pk):
    template_name = 'fornecedor/tabela/tabela-fornecedor.html'
    obj = Fornecedores.objects.get(pk=pk)
    obj.delete()
    return render(request, template_name)



def total_fornecedor(request):
    template_name = 'fornecedor/informacao-fornecedor.html'
    total_fornecedor =  Fornecedores.objects.count()
    context = {'total_fornecedor': total_fornecedor}
    return render(request, template_name, context)
    