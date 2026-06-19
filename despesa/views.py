import json
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db import transaction
from despesa.forms import DespesaForms, CategoriaDespesaForms
from despesa.models import Despesa, CategoriaDespesa
from despesa.services import (
    build_expense_dashboard,
    filter_created_by_period,
    filter_expenses_for_period_or_fixed_due,
    filter_expenses_by_type,
    resolve_expense_period,
    resolve_expense_type_filter,
)
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
    tipo = source.get('dashboard_tipo') or source.get('tipo')
    data_inicio = source.get('dashboard_inicio') or source.get('dashboard_data_inicio') or source.get('inicio') or source.get('data_inicio')
    data_fim = source.get('dashboard_fim') or source.get('dashboard_data_fim') or source.get('fim') or source.get('data_fim')
    if periodo:
        params['periodo'] = periodo
    if tipo:
        params['tipo'] = tipo
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
        'dashboard_tipo': params.get('tipo', ''),
        'dashboard_inicio': params.get('inicio', ''),
        'dashboard_fim': params.get('fim', ''),
        'dashboard_data_inicio': params.get('data_inicio', ''),
        'dashboard_data_fim': params.get('data_fim', ''),
    }


def _despesa_dashboard_context(user, params):
    period = resolve_expense_period(params)
    type_filter = resolve_expense_type_filter(params)
    expenses = filter_expenses_for_period_or_fixed_due(
        Despesa.objects.filter(usuario=user).select_related('categoria_despesa', 'fornecedor'),
        period,
    )
    regular_expenses = _regular_expenses_for_type(expenses, type_filter)
    debt_expenses = _debt_expenses_for_type(expenses, type_filter)
    include_stock_rows = type_filter not in ('prolabore', 'divida')
    context = {
        'object_list': regular_expenses.order_by('-data_cadastro'),
        'debt_list': debt_expenses.order_by('-data_cadastro'),
        'peca': (
            filter_created_by_period(
                Pecas.objects.filter(forma_pagamento='Fiado a pagar', usuario=user),
                period,
            )
            .order_by('-data_criacao')
        ) if include_stock_rows else Pecas.objects.none(),
        'produto': (
            filter_created_by_period(
                Produto.objects.filter(forma_pagamento='Fiado a pagar', usuario=user),
                period,
            )
            .order_by('-data_criacao')
        ) if include_stock_rows else Produto.objects.none(),
    }
    context.update(_expense_section_lists(expenses, type_filter))
    context.update(build_expense_dashboard(user, params))
    return context


def _regular_expenses_for_type(queryset, type_filter):
    if type_filter == 'divida':
        return queryset.none()
    queryset = filter_expenses_by_type(queryset, type_filter)
    return queryset.exclude(tipo=Despesa.TIPO_DIVIDA)


def _debt_expenses_for_type(queryset, type_filter):
    if type_filter in ('empresa', 'prolabore'):
        return queryset.none()
    return queryset.filter(tipo=Despesa.TIPO_DIVIDA)


def _expense_section_lists(queryset, type_filter):
    empty = Despesa.objects.none()
    show_business = type_filter in ('todos', 'empresa')
    show_prolabore = type_filter in ('todos', 'prolabore')

    return {
        'business_expense_list': (
            queryset
            .filter(tipo=Despesa.TIPO_EMPRESA, despesa_fixa=False)
            .order_by('-data_cadastro')
        ) if show_business else empty,
        'fixed_expense_list': (
            queryset
            .filter(tipo=Despesa.TIPO_EMPRESA, despesa_fixa=True)
            .order_by('-data_cadastro')
        ) if show_business else empty,
        'prolabore_expense_list': (
            queryset
            .filter(tipo=Despesa.TIPO_PROLABORE)
            .order_by('-data_cadastro')
        ) if show_prolabore else empty,
    }


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


def _categoria_list_context(user):
    return {
        'object_list': CategoriaDespesa.objects.filter(usuario=user).order_by('nome_categoria_despesa')
    }


def _apply_prolabore_date(despesa, data_lancamento):
    if despesa.tipo != Despesa.TIPO_PROLABORE or not data_lancamento:
        return

    current_time = timezone.localtime(despesa.data_cadastro).time() if despesa.data_cadastro else timezone.localtime().time()
    data_cadastro = timezone.make_aware(datetime.combine(data_lancamento, current_time))
    Despesa.objects.filter(pk=despesa.pk).update(data_cadastro=data_cadastro)
    despesa.data_cadastro = data_cadastro


class ListaDespesa(ListView):
    model = Despesa
    template_name = 'despesa/pagina-inicial-despesa.html'
    context_object_name = 'object'

    def get_queryset(self):
        self._period = resolve_expense_period(self.request.GET)
        self._type_filter = resolve_expense_type_filter(self.request.GET)
        self._base_expenses = filter_expenses_for_period_or_fixed_due(
            Despesa.objects.filter(usuario=self.request.user).select_related('categoria_despesa', 'fornecedor'),
            self._period,
        )
        return _regular_expenses_for_type(self._base_expenses, self._type_filter).order_by('-data_cadastro')

    def get_context_data(self, **kwargs):
        context = super(ListaDespesa, self).get_context_data(**kwargs)
        period = getattr(self, '_period', resolve_expense_period(self.request.GET))
        type_filter = getattr(self, '_type_filter', resolve_expense_type_filter(self.request.GET))
        base_expenses = getattr(self, '_base_expenses', filter_expenses_for_period_or_fixed_due(
            Despesa.objects.filter(usuario=self.request.user).select_related('categoria_despesa', 'fornecedor'),
            period,
        ))
        include_stock_rows = type_filter not in ('prolabore', 'divida')
        context.update(build_expense_dashboard(self.request.user, self.request.GET))
        context.update(_expense_section_lists(base_expenses, type_filter))
        context['debt_list'] = _debt_expenses_for_type(base_expenses, type_filter).order_by('-data_cadastro')
        context['peca'] = (
            filter_created_by_period(
                Pecas.objects.filter(forma_pagamento='Fiado a pagar', usuario=self.request.user),
                period,
            )
            .order_by('-data_criacao')
        ) if include_stock_rows else Pecas.objects.none()
        context['produto'] = (
            filter_created_by_period(
                Produto.objects.filter(forma_pagamento='Fiado a pagar', usuario=self.request.user),
                period,
            )
            .order_by('-data_criacao')
        ) if include_stock_rows else Produto.objects.none()
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
    form = DespesaForms(
        request.POST or None,
        initial={'usuario': request.user, 'tipo': Despesa.TIPO_EMPRESA},
        user=request.user,
        tipo_forcado=Despesa.TIPO_EMPRESA,
    )

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.save()
            return _render_dashboard_update(request, 'despesaSalva')

    context = {
        'form': form,
        'form_title': 'Cadastrar despesa',
        'form_action_url': reverse('cadastrar-despesa'),
        'is_prolabore_form': False,
        'is_divida_form': False,
    }
    context.update(_dashboard_form_context(request))
    return _render_modal_form(request, template_name, context)


@login_required
def cadastrarprolabore(request):
    template_name = 'despesa/formularios/formulario-cadastrar-despesa.html'
    form = DespesaForms(
        request.POST or None,
        initial={
            'usuario': request.user,
            'tipo': Despesa.TIPO_PROLABORE,
        },
        user=request.user,
        tipo_forcado=Despesa.TIPO_PROLABORE,
    )

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.tipo = Despesa.TIPO_PROLABORE
            despesa.save()
            _apply_prolabore_date(despesa, form.cleaned_data.get('data_lancamento'))
            return _render_dashboard_update(request, 'prolaboreSalvo')

    context = {
        'form': form,
        'form_title': 'Cadastrar Pró-labore',
        'form_action_url': reverse('cadastrar-prolabore'),
        'is_prolabore_form': True,
        'is_divida_form': False,
    }
    context.update(_dashboard_form_context(request))
    return _render_modal_form(request, template_name, context)


@login_required
def cadastrardivida(request):
    template_name = 'despesa/formularios/formulario-cadastrar-despesa.html'
    form = DespesaForms(
        request.POST or None,
        initial={
            'usuario': request.user,
            'tipo': Despesa.TIPO_DIVIDA,
        },
        user=request.user,
        tipo_forcado=Despesa.TIPO_DIVIDA,
    )

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.tipo = Despesa.TIPO_DIVIDA
            despesa.save()
            return _render_dashboard_update(request, 'dividaSalva')

    context = {
        'form': form,
        'form_title': 'Cadastrar Dívida',
        'form_action_url': reverse('cadastrar-divida'),
        'is_prolabore_form': False,
        'is_divida_form': True,
    }
    context.update(_dashboard_form_context(request))
    return _render_modal_form(request, template_name, context)



@login_required
def editardespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-despesa.html'
    instance = Despesa.objects.get(pk=pk)
    form = DespesaForms(
        request.POST or None,
        instance=instance,
        initial={'usuario': request.user, 'tipo': instance.tipo},
        user=request.user,
        tipo_forcado=instance.tipo,
    )
    
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.save()
            _apply_prolabore_date(despesa, form.cleaned_data.get('data_lancamento'))
            if despesa.tipo == Despesa.TIPO_PROLABORE:
                trigger = 'prolaboreEditado'
            elif despesa.tipo == Despesa.TIPO_DIVIDA:
                trigger = 'dividaEditada'
            else:
                trigger = 'despesaEditada'
            return _render_dashboard_update(request, trigger)

    is_prolabore = instance.tipo == Despesa.TIPO_PROLABORE
    is_divida = instance.tipo == Despesa.TIPO_DIVIDA
    context = {
        'form': form,
        'object': instance,
        'form_title': 'Editar Pró-labore' if is_prolabore else ('Editar Dívida' if is_divida else f'Editar {instance.nome_despesa}'),
        'form_action_url': reverse('editar-despesa', args=[instance.pk]),
        'is_prolabore_form': is_prolabore,
        'is_divida_form': is_divida,
    }
    context.update(_dashboard_form_context(request))
    return _render_modal_form(request, template_name, context)



@login_required
def apagardespesa(request, pk):
    obj = get_object_or_404(Despesa, pk=pk)
    if obj.usuario != request.user:
        raise PermissionError
    is_prolabore = obj.tipo == Despesa.TIPO_PROLABORE
    is_divida = obj.tipo == Despesa.TIPO_DIVIDA
    obj.delete()
    if request.headers.get('HX-Request'):
        if is_prolabore:
            trigger = 'prolaboreExcluido'
        elif is_divida:
            trigger = 'dividaExcluida'
        else:
            trigger = 'despesaExcluida'
        return _render_dashboard_update(request, trigger)
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

            response = render(request, 'despesa/tabela/tabela-categoria-despesa.html', _categoria_list_context(request.user))
            response['HX-Trigger'] = 'despesaCategoriaSalva'
            return response
    
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
    obj = get_object_or_404(CategoriaDespesa, pk=pk)
    if obj.usuario != request.user:
        raise PermissionError

    with transaction.atomic():
        Despesa.objects.filter(usuario=request.user, categoria_despesa=obj).update(categoria_despesa=None)
        obj.delete()
    response = HttpResponse('')
    response['HX-Trigger'] = 'despesaCategoriaExcluida'
    return response

    

class ListaCategoriaDespesa(ListView):
    model = CategoriaDespesa
    template_name = 'despesa/tabela/tabela-categoria-despesa.html'
    context_object_name = 'object'

    def get_queryset(self):
        return CategoriaDespesa.objects.filter(usuario=self.request.user).order_by('nome_categoria_despesa')



@login_required
def editarcatergoriadespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-categoria-despesa.html'
    instance = get_object_or_404(CategoriaDespesa, pk=pk)
    form = CategoriaDespesaForms(request.POST or None, initial={'usuario': request.user}, instance=instance, user=request.user)
    if instance.usuario != request.user:
        raise PermissionError
    if request.method == 'POST':
        if form.is_valid():
            categoria_despesa = form.save()
            context = {'object': categoria_despesa}
            response = render(request, 'despesa/tabela/linha-categoria-despesa.html', context)
            response['HX-Trigger'] = 'despesaCategoriaEditada'
            return response
        response = render(request, template_name, {'form': form, 'object': instance})
        response['HX-Retarget'] = '#adicionar-conteudo2'
        response['HX-Reswap'] = 'innerHTML'
        return response
        

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
