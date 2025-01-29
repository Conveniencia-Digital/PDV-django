from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from pedido.forms import PedidoForms
from pedido.models import Pedido


class ListaPedido(ListView):
    model = Pedido
    template_name = 'pedido/pagina-inicial-pedido.html'

    def get_queryset(self):
        return Pedido.objects.filter(usuario=self.request.user)


@login_required
def cadastrarpedido(request):
    template_name = 'pedido/formularios/form-cadastrar-pedido.html'
    form = PedidoForms(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == "POST":
        if form.is_valid():
            pedido = form.save()
            template_name = 'pedido/tabela/linha-tabela-pedido.html'
            context = {'object': pedido}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


@login_required
def editarpedido(request, pk):
    template_name = 'pedido/formularios/form-editar-pedido.html'
    instance = Pedido.objects.get(pk=pk)
    form = PedidoForms(request.POST or None, instance=instance, initial={'usuario': request.user}, user=request.user)

    if instance.usuario != request.user:
        raise PermissionError

    if request.method == "POST":
        if form.is_valid():
            template_name = 'pedido/tabela/linha-tabela-pedido.html'
            pedido = form.save()
            context = {'object': pedido}
            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarpedido(request, pk):
    template_name = 'pedido/tabela/tabela-pedido.html'
    obj = Pedido.objects.get(pk=pk)

    if obj.usuario == request.user:
        obj.delete()
        return render(request, template_name)
    else:
        raise PermissionError


class DetalhePedido(DetailView):
    model = Pedido
    template_name = 'pedido/off-canvas/detalhe-pedido.html'
