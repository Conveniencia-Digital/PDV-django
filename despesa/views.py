import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from despesa.forms import DespesaForms, CategoriaDespesaForms
from despesa.models import Despesa, CategoriaDespesa
from despesa.services import build_expense_dashboard, filter_created_by_period, filter_expenses_by_period, resolve_expense_period
from peca.models import Pecas
from produto.models import Produto
from django.contrib.auth.decorators import login_required


def _categoria_despesa_payload(categoria):
    return {
        'id': categoria.pk,
        'text': categoria.nome_categoria_despesa,
        'name': categoria.nome_categoria_despesa,
        'meta': 'Categoria de despesa',
    }


def _dashboard_params_from_request(request):
    source = request.POST if request.method == 'POST' else request.GET
    params = {}
    periodo = source.get('dashboard_periodo') or source.get('periodo')
    data_inicio = source.get('dashboard_inicio') or source.get('dashboard_data_inicio') or source.get('inicio') or source.get('data_inicio')
    data_fim = source.get('dashboard_fim') or source.get('dashboard_data_fim') or source.get('fim') or source.get('data_fim')
    if periodo:
        params['periodo'] = periodo
    if data_inicio:
        params['inicio'] = data_inicio
        params['data_inicio'] = data_inicio
    if data_fim:
        params['fim'] = data_fim
        params['data_fim'] = data_fim
    return params


def _dashboard_form_context(request):
    params = _dashboard_params_from_request(request)
    return {
        'dashboard_periodo': params.get('periodo', ''),
        'dashboard_inicio': params.get('inicio', ''),
        'dashboard_fim': params.get('fim', ''),
        'dashboard_data_inicio': params.get('data_inicio', ''),
        'dashboard_data_fim': params.get('data_fim', ''),
    }


def _despesa_dashboard_context(user, params):
    period = resolve_expense_period(params)
    context = {
        'object_list': (
            filter_expenses_by_period(
                Despesa.objects.filter(usuario=user).select_related('categoria_despesa', 'fornecedor'),
                period,
            )
            .order_by('-data_cadastro')
        ),
        'peca': (
            filter_created_by_period(
                Pecas.objects.filter(forma_pagamento='Fiado a pagar', usuario=user),
                period,
            )
            .order_by('-data_criacao')
        ),
        'produto': (
            filter_created_by_period(
                Produto.objects.filter(forma_pagamento='Fiado a pagar', usuario=user),
                period,
            )
            .order_by('-data_criacao')
        ),
    }
    context.update(build_expense_dashboard(user, params))
    return context


def _render_dashboard_update(request, trigger=None):
    context = _despesa_dashboard_context(request.user, _dashboard_params_from_request(request))
    response = render(request, 'despesa/bloco-dados.html', context)
    response['HX-Retarget'] = '#bloco-dados'
    response['HX-Reswap'] = 'outerHTML'
    if trigger:
        response['HX-Trigger'] = trigger
    return response


def _render_modal_form(request, template_name, context):
    response = render(request, template_name, context)
    if request.headers.get('HX-Request'):
        response['HX-Retarget'] = '#adicionar-conteudo'
        response['HX-Reswap'] = 'innerHTML'
    return response


class ListaDespesa(ListView):
    model = Despesa
    template_name = 'despesa/pagina-inicial-despesa.html'
    context_object_name = 'object'

    def get_queryset(self):
        self._period = resolve_expense_period(self.request.GET)
        return (
            filter_expenses_by_period(
                Despesa.objects.filter(usuario=self.request.user).select_related('categoria_despesa', 'fornecedor'),
                self._period,
            )
            .order_by('-data_cadastro')
        )

    def get_context_data(self, **kwargs):
        context = super(ListaDespesa, self).get_context_data(**kwargs)
        period = getattr(self, '_period', resolve_expense_period(self.request.GET))
        context.update(build_expense_dashboard(self.request.user, self.request.GET))
        context['peca'] = (
            filter_created_by_period(
                Pecas.objects.filter(forma_pagamento='Fiado a pagar', usuario=self.request.user),
                period,
            )
            .order_by('-data_criacao')
        )
        context['produto'] = (
            filter_created_by_period(
                Produto.objects.filter(forma_pagamento='Fiado a pagar', usuario=self.request.user),
                period,
            )
            .order_by('-data_criacao')
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return self.response_class(
                request=self.request,
                template='despesa/bloco-dados.html',
                context=context,
                **response_kwargs,
            )
        return super().render_to_response(context, **response_kwargs)



@login_required   
def cadastrardespesa(request):
    template_name = 'despesa/formularios/formulario-cadastrar-despesa.html'
    form = DespesaForms(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.save()
            return _render_dashboard_update(request, 'despesaSalva')

    context = {'form': form}
    context.update(_dashboard_form_context(request))
    return _render_modal_form(request, template_name, context)



@login_required
def editardespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-despesa.html'
    instance = Despesa.objects.get(pk=pk)
    form = DespesaForms(request.POST or None, instance=instance, initial={'usuario': request.user}, user=request.user)
    
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.save()
            return _render_dashboard_update(request, 'despesaEditada')

    context = {'form': form, 'object': instance}
    context.update(_dashboard_form_context(request))
    return _render_modal_form(request, template_name, context)



@login_required
def apagardespesa(request, pk):
    obj = get_object_or_404(Despesa, pk=pk)
    if obj.usuario != request.user:
        raise PermissionError
    obj.delete()
    if request.headers.get('HX-Request'):
        return _render_dashboard_update(request, 'despesaExcluida')
    return redirect('despesa')




@login_required
def cadastrarcategoriadespesa(request):
    template_name = 'despesa/formularios/formulario-categoria-despesa.html'
    picker_mode = request.GET.get('picker') == '1' or request.POST.get('category_picker') == '1'
    form = CategoriaDespesaForms(request.POST or None, initial={'usuario': request.user}, user=request.user)
    
    if request.method == 'POST':
        if form.is_valid():
            categoria_despesa = form.save()

            if picker_mode:
                response = HttpResponse('')
                response['HX-Trigger'] = json.dumps({'despesaCategoriaCriada': _categoria_despesa_payload(categoria_despesa)})
                return response

            template_name = 'despesa/tabela/linha-categoria-despesa.html'
            context = {'object': categoria_despesa}
            return render(request, template_name, context)
    
    context = {'form': form, 'category_picker_mode': picker_mode}
    return render(request, template_name, context)


@login_required
def buscarcategoriasdespesa(request):
    termo = request.GET.get('q', '').strip()
    categorias = CategoriaDespesa.objects.filter(usuario=request.user)

    if termo:
        categorias = categorias.filter(nome_categoria_despesa__icontains=termo)

    categorias = categorias.order_by('nome_categoria_despesa')[:30]
    return JsonResponse({'results': [_categoria_despesa_payload(categoria) for categoria in categorias]})




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
    form = CategoriaDespesaForms(request.POST or None, initial={'usuario': request.user}, instance=instance, user=request.user)
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
