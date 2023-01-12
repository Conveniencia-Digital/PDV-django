from django.shortcuts import render
from django.views.generic import ListView

from cliente.models import Cliente
from cliente.forms import ClienteForm


class ListaCliente(ListView):
    model = Cliente
    template_name = 'cliente/pagina-inicial-cliente.html'


def cadastrarcliente(request):
    template_name = 'cliente/formularios/formulario-cadastrar-cliente.html'
    form = ClienteForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            cliente = form.save()
            template_name = 'cliente/tabela/linhas-tabela-cliente.html'

            context = {'object': cliente}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editarcliente(request, pk):
    template_name = 'cliente/formularios/formulario-editar-cliente.html'
    instance = Cliente.objects.get(pk=pk)
    form = ClienteForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            cliente = form.save()
            template_name = 'cliente/tabela/linhas-tabela-cliente.html'
            context = {'object': cliente}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagarcliente(request, pk):
    template_name = 'cliente/tabela/tabela-cliente.html'
    obj = Cliente.objects.get(pk=pk)
    obj.delete()
    return render(request, template_name)



def total_clientes(request):
    template_name = 'cliente/informacao-cliente.html'
    total_cliente =  Cliente.objects.count()
    context = {'total_cliente': total_cliente}
    return render(request, template_name, context)
    