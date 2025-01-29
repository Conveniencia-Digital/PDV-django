from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from cliente.forms import ClienteForm
from cliente.models import Cliente


class ListaCliente(ListView):
    model = Cliente
    template_name = 'cliente/pagina-inicial-cliente.html'

    def get_queryset(self):
        return Cliente.objects.filter(usuario=self.request.user)


@login_required
def cadastrarcliente(request):
    template_name = 'cliente/formularios/formulario-cadastrar-cliente.html'
    form = ClienteForm(request.POST or None, initial={'usuario': request.user})
    if request.method == 'POST':
        if form.is_valid():
            cliente = form.save()
            template_name = 'cliente/tabela/linhas-tabela-cliente.html'
            context = {'object': cliente}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


@login_required
def editarcliente(request, pk):
    template_name = 'cliente/formularios/formulario-editar-cliente.html'
    instance = Cliente.objects.get(pk=pk)
    form = ClienteForm(request.POST or None, instance=instance, initial={'usuario': request.user})

    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            cliente = form.save()
            template_name = 'cliente/tabela/linhas-tabela-cliente.html'
            context = {'object': cliente}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarcliente(request, pk):
    template_name = 'cliente/tabela/tabela-cliente.html'
    obj = Cliente.objects.get(pk=pk)
    if obj.usuario != request.user:
        raise PermissionError
    else:
        obj.delete()
    return render(request, template_name)


@login_required
def total_clientes(request):
    template_name = 'cliente/informacao-cliente.html'
    total_cliente = Cliente.objects.count()
    context = {'total_cliente': total_cliente}
    return render(request, template_name, context)


class DetalheClienteView(DetailView):
    model = Cliente
    template_name = 'cliente/off-canvas/detalhe-cliente.html'
