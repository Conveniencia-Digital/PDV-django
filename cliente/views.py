import json

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView

from cliente.models import Cliente
from cliente.forms import ClienteForm
from django.contrib.auth.decorators import login_required
    



class ListaCliente(ListView):
    model = Cliente
    template_name = 'cliente/pagina-inicial-cliente.html'

    def get_queryset(self):
        return Cliente.objects.filter(usuario=self.request.user)



def _cliente_payload(cliente):
    return {
        'id': cliente.pk,
        'text': cliente.nome_cliente,
        'name': cliente.nome_cliente,
        'phone': cliente.telefone_contato or '',
        'phone_secondary': cliente.telefone_contato_2 or '',
        'cpf': cliente.cpf or '',
    }


@login_required
def buscarclientes(request):
    termo = request.GET.get('q', '').strip()
    clientes = Cliente.objects.filter(usuario=request.user)

    if termo:
        clientes = clientes.filter(
            Q(nome_cliente__icontains=termo)
            | Q(telefone_contato__icontains=termo)
            | Q(telefone_contato_2__icontains=termo)
            | Q(cpf__icontains=termo)
        )

    clientes = clientes.order_by('nome_cliente')[:30]
    return JsonResponse({'results': [_cliente_payload(cliente) for cliente in clientes]})


@login_required
def cadastrarcliente(request):
    template_name = 'cliente/formularios/formulario-cadastrar-cliente.html' 
    client_picker_mode = request.GET.get('picker') == '1' or request.POST.get('client_picker') == '1'
    form = ClienteForm(request.POST or None, initial={'usuario': request.user})
    if request.method == 'POST':
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario = request.user
            cliente.save()

            if client_picker_mode:
                response = HttpResponse('')
                response['HX-Trigger'] = json.dumps({'clienteCriado': _cliente_payload(cliente)})
                return response

            template_name = 'cliente/tabela/linhas-tabela-cliente.html'
            context = {'object': cliente}
            return render(request, template_name, context)

    context = {'form': form, 'client_picker_mode': client_picker_mode}
    return render(request, template_name, context)



@login_required
def editarcliente(request, pk):
    template_name = 'cliente/formularios/formulario-editar-cliente.html'
    instance = Cliente.objects.get(pk=pk)
    form = ClienteForm(request.POST or None, instance=instance, initial={'usuario':request.user})
    
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
    total_cliente =  Cliente.objects.count()
    context = {'total_cliente': total_cliente}
    return render(request, template_name, context)
    

class DetalheClienteView(DetailView):
    model = Cliente
    template_name = 'cliente/off-canvas/detalhe-cliente.html'
    
