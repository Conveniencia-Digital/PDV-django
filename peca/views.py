import json

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.http import HttpResponse, JsonResponse
from peca.models import Pecas
from peca.forms import PecasForms
from django.contrib.auth.decorators import login_required

class Peca(ListView):
    model = Pecas
    template_name = 'peca/pagina-inicial-pecas.html'

    def get_queryset(self):
        return Pecas.objects.filter(usuario=self.request.user)


def _peca_payload(peca):
    return {
        'id': peca.pk,
        'text': peca.nome_peca,
        'name': peca.nome_peca,
        'price': str(peca.preco_peca or 0),
        'cost': str(peca.preco_de_custo or 0),
        'meta': f'Estoque: {peca.quantidade} | R$ {peca.preco_peca}',
    }


@login_required
def buscarpecas(request):
    termo = request.GET.get('q', '').strip()
    pecas = Pecas.objects.filter(usuario=request.user, quantidade__gt=0)

    if termo:
        pecas = pecas.filter(
            Q(nome_peca__icontains=termo)
            | Q(categoria_peca__icontains=termo)
            | Q(codigo_de_barras__icontains=termo)
        )

    pecas = pecas.order_by('nome_peca')[:30]
    return JsonResponse({'results': [_peca_payload(peca) for peca in pecas]})


@login_required
def cadastrarpeca(request):
    template_name = 'peca/formularios/formulario-cadastrar-peca.html'
    picker_mode = request.GET.get('picker') == '1' or request.POST.get('piece_picker') == '1'
    form = PecasForms(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            peca = form.save()
            if picker_mode:
                response = HttpResponse('')
                response['HX-Trigger'] = json.dumps({'orcamentoPecaCriada': _peca_payload(peca)})
                return response

            template_name = 'peca/tabela/linhas-tabela-peca.html'
            context = {'object': peca}
            response = render(request, template_name, context)
            response['HX-Trigger'] = 'pecaSalva'
            return response

    context = {'form': form, 'piece_picker_mode': picker_mode}
    return render(request, template_name, context)



@login_required
def editarpeca(request, pk):
    template_name = 'peca/formularios/formulario-editar-peca.html'
    instance = Pecas.objects.get(pk=pk)
    form = PecasForms(request.POST or None, instance=instance, initial={'usuario': request.user}, user=request.user)
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            peca = form.save()
            template_name = 'peca/tabela/linhas-tabela-peca.html'
            context = {'object': peca}
            response = render(request, template_name, context)
            response['HX-Trigger'] = 'pecaEditada'
            return response

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarpeca(request, pk):
    template_name = 'peca/tabela/tabela-peca.html'
    objeto = Pecas.objects.get(pk=pk)
    if objeto.usuario == request.user:
        objeto.delete()
    else:
       
        raise PermissionError
    return render(request, template_name)


def relatoriopeca(request):
    template_name = 'peca/informacao-peca.html'
    preco_venda = Pecas.objects.filter(usuario=request.user).aggregate(preco_pecas=Sum('preco_peca'))
    preco_custo = Pecas.objects.filter(usuario=request.user).aggregate(preco_custo=Sum('preco_de_custo'))
    total = Pecas.objects.filter(usuario=request.user).count

    for i in preco_venda.values():
        preco_venda = i
    
    for c in preco_custo.values():
        preco_custo = c

    lucro = preco_venda - preco_custo    

    context = {'preco_venda': preco_venda, 'preco_custo': preco_custo, 'lucro': lucro, 'total': total}
    return render(request, template_name, context)


class DetalhePeca(DetailView):
    model = Pecas
    template_name = 'peca/offcanvas/detalhe-peca.html'

    def get_queryset(self):
        return Pecas.objects.filter(usuario=self.request.user)
