import json
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from financeiro.card_fees import (
    apply_card_fee_to_lanhouse,
    calculate_card_fee,
    preview_card_fee,
    sync_lanhouse_card_fee_expense,
)
from lanhouse.models import LanhouseModel, LanhouseServico, ItemsLanhouse
from lanhouse.models import LanhouseSubmissionToken
from lanhouse.forms import LanhouseForm, LanhouseFormset, LanhouseServicoForm, ItemsLanhouseForm
from django.contrib.auth.decorators import login_required
from lanhouse.periodo import aplicar_filtro_periodo, build_lanhouse_dashboard_charts, metricas_lanhouse


def _criar_submission_token(user, finalidade):
    return LanhouseSubmissionToken.objects.create(
        usuario=user,
        finalidade=finalidade,
        token=uuid4().hex,
    ).token


def _consumir_submission_token(user, finalidade, token):
    if not token:
        return False
    token_obj = (
        LanhouseSubmissionToken.objects
        .select_for_update()
        .filter(usuario=user, finalidade=finalidade, token=token, usado_em__isnull=True)
        .first()
    )
    if not token_obj:
        return False
    token_obj.usado_em = timezone.now()
    token_obj.save(update_fields=['usado_em'])
    return True


def _servico_lanhouse_payload(servico):
    preco = servico.preco or 0
    return {
        'id': servico.pk,
        'text': servico.servico,
        'name': servico.servico,
        'price': str(preco),
        'cost': str(servico.preco_custo or 0),
        'meta': f'R$ {preco}',
    }


def _base_lanhouse_queryset(user):
    return (
        LanhouseModel.objects
        .filter(usuario=user)
        .select_related('cliente', 'vendedor', 'card_machine')
        .prefetch_related('lanhouse_items__servico')
        .order_by('-data_criacao')
    )


def _dashboard_params_from_request(request):
    source = request.POST if request.method == 'POST' else request.GET
    params = {}
    periodo = source.get('dashboard_periodo') or source.get('periodo')
    inicio = source.get('dashboard_inicio') or source.get('inicio')
    fim = source.get('dashboard_fim') or source.get('fim')

    if periodo:
        params['periodo'] = periodo
    if inicio:
        params['inicio'] = inicio
    if fim:
        params['fim'] = fim
    return params


def _dashboard_form_context(request):
    params = _dashboard_params_from_request(request)
    return {
        'dashboard_periodo': params.get('periodo', ''),
        'dashboard_inicio': params.get('inicio', ''),
        'dashboard_fim': params.get('fim', ''),
    }


def _lanhouse_dashboard_context(user, params):
    qs = _base_lanhouse_queryset(user)
    object_list, inicio, fim, periodo = aplicar_filtro_periodo(qs, SimpleNamespace(GET=params))
    context = {'object_list': object_list}
    context.update(metricas_lanhouse(object_list))
    context.update(build_lanhouse_dashboard_charts(user, params))
    context.update({
        'inicio': inicio or '',
        'fim': fim or '',
        'periodo': periodo or '',
    })
    return context


def _render_dashboard_update(request, trigger=None):
    context = _lanhouse_dashboard_context(request.user, _dashboard_params_from_request(request))
    response = render(request, 'lanhouse/bloco-dados.html', context)
    response['HX-Retarget'] = '#bloco-dados'
    response['HX-Reswap'] = 'outerHTML'
    if trigger:
        response['HX-Trigger'] = trigger
    return response


def _base_lanhouse_formset(form, formset):
    total = Decimal("0.00")
    for item in formset.cleaned_data:
        if item.get('DELETE'):
            continue
        preco = item.get('preco') or Decimal("0.00")
        quantidade = item.get('quantidade') or 0
        total += preco * quantidade

    desconto = form.cleaned_data.get('desconto') or Decimal("0.00")
    return max(total - desconto, Decimal("0.00"))


def _add_card_fee_error(form, error):
    messages = getattr(error, 'messages', None) or [str(error)]
    for message in messages:
        form.add_error(None, message)


def _prepare_lanhouse_for_save(user, form, formset):
    lanhouse = form.save(commit=False)
    lanhouse.usuario = user
    base_amount = _base_lanhouse_formset(form, formset)

    calculation = calculate_card_fee(
        user=user,
        payment_method=lanhouse.forma_pagamento,
        card_machine=lanhouse.card_machine,
        installments=lanhouse.card_installments,
        base_amount=base_amount,
        pass_fee_to_customer=lanhouse.pass_card_fee_to_customer,
    )
    apply_card_fee_to_lanhouse(lanhouse, calculation)
    return lanhouse


def _save_lanhouse_with_items(lanhouse, formset):
    lanhouse.save()
    formset.instance = lanhouse
    items_lanhouse = formset.save()
    sync_lanhouse_card_fee_expense(lanhouse)
    return items_lanhouse


class ListaLanhouse(LoginRequiredMixin, ListView):
    model = LanhouseModel
    template_name = 'lanhouse/pagina-inicial-lanhouse.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        qs = _base_lanhouse_queryset(self.request.user)
        qs, self._inicio, self._fim, self._periodo = aplicar_filtro_periodo(qs, self.request)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        metricas = metricas_lanhouse(context['object_list'])
        context.update(metricas)
        context.update(build_lanhouse_dashboard_charts(self.request.user, self.request.GET))
        context.update({
            'inicio': self._inicio or '',
            'fim': self._fim or '',
            'periodo': self._periodo or '',
        })
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return self.response_class(
                request=self.request,
                template='lanhouse/bloco-dados.html',
                context=context,
                **response_kwargs,
            )
        return super().render_to_response(context, **response_kwargs)


@login_required
def cadastrarlanhouse(request):
    template_name = 'lanhouse/formularios/formulario-cadastrar-lanhouse.html'
    lanhouse_instance = LanhouseModel()
    form = LanhouseForm(request.POST or None, user=request.user, initial={'usuario': request.user}, instance=lanhouse_instance, prefix='main')
    formset = LanhouseFormset(request.POST or None, instance=lanhouse_instance, prefix='items', form_kwargs={'user': request.user})
    submission_token = request.POST.get('submission_token') or _criar_submission_token(request.user, 'lanhouse_venda')

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            try:
                lanhouse = _prepare_lanhouse_for_save(request.user, form, formset)
            except ValidationError as error:
                _add_card_fee_error(form, error)
            else:
                with transaction.atomic():
                    if not _consumir_submission_token(request.user, 'lanhouse_venda', submission_token):
                        response = HttpResponse('Esta venda já foi processada.', status=409)
                        response['HX-Trigger'] = 'lanhouseVendaDuplicada'
                        return response
                    items_lanhouse = _save_lanhouse_with_items(lanhouse, formset)
                return _render_dashboard_update(request, 'lanhouseVendaSalva')

    context = {'form': form, 'formset': formset, 'submission_token': submission_token}
    context.update(_dashboard_form_context(request))
    return render(request, template_name, context)


@login_required
def editarlanhouse(request, pk):
    template_name = 'lanhouse/formularios/formulario-editar-lanhouse.html'
    lanhouse_instance = LanhouseModel.objects.get(pk=pk)

    form = LanhouseForm(request.POST or None, user=request.user, initial={'usuario': request.user}, instance=lanhouse_instance, prefix='main')
    formset = LanhouseFormset(request.POST or None, form_kwargs={'user': request.user}, instance=lanhouse_instance, prefix='items')

    if lanhouse_instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            try:
                lanhouse = _prepare_lanhouse_for_save(request.user, form, formset)
            except ValidationError as error:
                _add_card_fee_error(form, error)
            else:
                with transaction.atomic():
                    items_lanhouse = _save_lanhouse_with_items(lanhouse, formset)
                return _render_dashboard_update(request, 'lanhouseVendaSalva')
        else:
            print(form.errors)
            print(formset.errors)

    context = {'object': lanhouse_instance, 'form': form, 'formset': formset}
    context.update(_dashboard_form_context(request))
    return render(request, template_name, context)


@login_required
def apagarlanhouse(request, pk):
    obj = LanhouseModel.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
        return _render_dashboard_update(request, 'lanhouseVendaExcluida')
    else:
        raise PermissionError


class DetalheLanhouse(DetailView):
    template_name = 'lanhouse/detalhe-lanhouse.html'
    model = LanhouseModel

    def get_queryset(self):
        return LanhouseModel.objects.filter(usuario=self.request.user)



@login_required
def precoservicolanhouse(request):
    template_name = 'lanhouse/formularios/preco-servico-lanhouse.html'
    servico_lanhouse_pk = None
    item_index = ''

    for key, value in request.GET.items():
        if key.startswith('items-') and key.endswith('-servico'):
            parts = key.split('-')
            if len(parts) >= 3:
                item_index = parts[1]
            servico_lanhouse_pk = value
            break
        if key == 'servico':
            servico_lanhouse_pk = value

    if not servico_lanhouse_pk:
        return HttpResponseBadRequest('Serviço não informado')

    servico = get_object_or_404(LanhouseServico, pk=servico_lanhouse_pk, usuario=request.user)
    context = {'servico': servico, 'item': item_index}
    return render(request, template_name, context)


@login_required
def buscarservicoslanhouse(request):
    termo = request.GET.get('q', '').strip()
    servicos = LanhouseServico.objects.filter(usuario=request.user)

    if termo:
        servicos = servicos.filter(
            Q(servico__icontains=termo)
            | Q(preco__icontains=termo)
            | Q(preco_custo__icontains=termo)
        )

    servicos = servicos.order_by('servico')[:30]
    return JsonResponse({'results': [_servico_lanhouse_payload(servico) for servico in servicos]})


@login_required
def previewtaxacartaolanhouse(request):
    forma_pagamento = request.GET.get('forma_pagamento', '')
    base_amount = request.GET.get('base_amount') or 0
    pass_fee = request.GET.get('pass_fee') in ('1', 'true', 'on', 'True')
    installments = request.GET.get('installments') or None
    machine_pk = request.GET.get('card_machine') or None

    preview = preview_card_fee(request.user, forma_pagamento, machine_pk, installments, base_amount, pass_fee)
    return JsonResponse(preview['payload'], status=preview['status'])



@login_required
def cadastrarservicolanhouse(request):
    template_name =  'lanhouse/formularios/formulario-cadastrar-servico-lanhouse.html'
    picker_mode = request.GET.get('picker') == '1' or request.POST.get('service_picker') == '1'
    form = LanhouseServicoForm(request.POST or None, initial={'usuario': request.user}, user=request.user)
    submission_token = request.POST.get('submission_token') or _criar_submission_token(request.user, 'lanhouse_servico')

    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    if not _consumir_submission_token(request.user, 'lanhouse_servico', submission_token):
                        response = HttpResponse('Este serviço já foi processado.', status=409)
                        response['HX-Trigger'] = 'lanhouseServicoDuplicado'
                        return response
                    servico = form.save()
            except IntegrityError:
                form.add_error('servico', 'Este serviço já está cadastrado.')
            else:
                if picker_mode:
                    response = HttpResponse('')
                    response['HX-Trigger'] = json.dumps({'lanhouseServicoCriado': _servico_lanhouse_payload(servico)})
                    return response

                response = HttpResponse('<div class="alert alert-success">Serviço cadastrado com sucesso!</div>')
                response['HX-Trigger'] = 'lanhouseServicoSalvo'
                response['HX-Retarget'] = '#addConteudo'
                response['HX-Reswap'] = 'innerHTML'
                return response
        
        if not form.is_valid():
            context = {'form': form, 'submission_token': submission_token, 'service_picker_mode': picker_mode}
            response = render(request, template_name, context)
            if not picker_mode:
                response['HX-Retarget'] = '#addConteudo'
                response['HX-Reswap'] = 'innerHTML'
            return response
        
    context = {'form': form, 'submission_token': submission_token, 'service_picker_mode': picker_mode}
    return render(request, template_name, context)



@login_required
def editarservicolanhouse(request, pk):
    template_name = 'lanhouse/formularios/formulario-editar-servico-lanhouse.html'
    instance = get_object_or_404(LanhouseServico, pk=pk, usuario=request.user)
    form = LanhouseServicoForm(request.POST or None, instance=instance, initial={'usuario':request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    servico = form.save()
            except IntegrityError:
                form.add_error('servico', 'Este serviço já está cadastrado.')
            else:
                template_name = 'lanhouse/tabela/linhas-tabela-servico.html'
                context = {'object': servico}
                response = render(request, template_name, context)
                response['HX-Trigger'] = 'lanhouseServicoEditado'
                return response
    
    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarservicolanhouse(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    servico = get_object_or_404(LanhouseServico, pk=pk, usuario=request.user)
    if ItemsLanhouse.objects.filter(servico=servico).exists():
        response = HttpResponse(
            '<td colspan="5" class="text-danger">Este serviço já possui vendas vinculadas e não pode ser excluído.</td>',
            status=409,
        )
        response['HX-Trigger'] = 'lanhouseServicoDeleteBloqueado'
        return response

    servico.delete()
    response = HttpResponse('')
    response['HX-Trigger'] = 'lanhouseServicoExcluido'
    return response


@login_required
def additemlanhouse(request):
    template_name = 'lanhouse/formularios/add-item-lanhouse.html'
    form = ItemsLanhouseForm(user=request.user)
    context = {'itemslanhouse': form}
    return render(request, template_name, context)




class ListaServicoLanhouse(ListView):
    model = LanhouseServico
    template_name = 'lanhouse/lista-servico-lanhouse.html'

    def get_queryset(self):
        return LanhouseServico.objects.filter(usuario=self.request.user)


def relatorio_lanhouse(request):
    template_name = 'lanhouse/relatorios/relatorio-lanhouse.html'
    qtd_lanhouse = LanhouseModel.objects.filter(usuario=request.user).count()
    valor_total = sum(qtd.total() for qtd in LanhouseModel.objects.filter(usuario=request.user))
    context = {'qtd_lanhouse': qtd_lanhouse, 'valor_total': valor_total}
    return render(request, template_name, context)
