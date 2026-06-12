import json
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from django.utils import timezone

from financeiro.card_fees import (
    apply_card_fee_to_transaction,
    calculate_card_fee,
    preview_card_fee,
    sync_card_fee_expense,
)
from orcamento.forms import (
    ItemsOrcamentoFormset,
    ItemsOrcamentoForms,
    OrcamentoForms,
    ServicoForms,
)
from orcamento.models import ItemsOrcamento, Orcamento, OrcamentoSubmissionToken, Servico
from orcamento.periodo import aplicar_filtro_periodo, build_orcamento_dashboard_charts, metricas_orcamento
from peca.models import Pecas


ZERO = Decimal("0.00")
MONEY_QUANT = Decimal("0.01")


def _money(value):
    return Decimal(value or ZERO).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _percent(part, total):
    total = _money(total)
    if total <= ZERO:
        return ZERO
    return (Decimal(part or ZERO) / total * Decimal("100")).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _criar_items_formset(user, instance=None, data=None):
    return ItemsOrcamentoFormset(
        data,
        instance=instance or Orcamento(),
        prefix='items',
        form_kwargs={'usuario': user},
    )


def _exibir_linha_servico_inicial(formset, post_data=None):
    if post_data:
        for key, value in post_data.items():
            if key.endswith('-servico') and value:
                return False

    for form in formset.forms:
        if form.instance.servico_id:
            return False
    return True


def _criar_submission_token(user, finalidade):
    return OrcamentoSubmissionToken.objects.create(
        usuario=user,
        finalidade=finalidade,
        token=uuid4().hex,
    ).token


def _consumir_submission_token(user, finalidade, token):
    if not token:
        return False
    token_obj = (
        OrcamentoSubmissionToken.objects
        .select_for_update()
        .filter(usuario=user, finalidade=finalidade, token=token, usado_em__isnull=True)
        .first()
    )
    if not token_obj:
        return False
    token_obj.usado_em = timezone.now()
    token_obj.save(update_fields=['usado_em'])
    return True


def _base_orcamento_formset(form, formset):
    total = Decimal("0.00")
    for item in formset.cleaned_data:
        if item.get('DELETE'):
            continue
        if not item.get('peca') and not item.get('servico'):
            continue
        preco = item.get('preco_orcamento') or Decimal("0.00")
        quantidade = item.get('quantidade') or 0
        total += preco * quantidade

    desconto = form.cleaned_data.get('desconto') or Decimal("0.00")
    return max(total - desconto, Decimal("0.00"))


def _add_card_fee_error(form, error):
    messages = getattr(error, 'messages', None) or [str(error)]
    for message in messages:
        form.add_error(None, message)


def _orcamento_finaliza_financeiro(orcamento):
    return orcamento.status in {
        Orcamento.FINALIZADO,
        Orcamento.FINALIZADO_ENTREGUE,
        Orcamento.GARANTIA_ENCERRADA,
    }


def _prepare_orcamento_for_save(user, form, formset):
    orcamento = form.save(commit=False)
    orcamento.usuario = user
    base_amount = _base_orcamento_formset(form, formset)

    calculation = calculate_card_fee(
        user=user,
        payment_method=orcamento.forma_pagamento,
        card_machine=orcamento.card_machine,
        installments=orcamento.card_installments,
        base_amount=base_amount,
        pass_fee_to_customer=orcamento.pass_card_fee_to_customer,
    )
    apply_card_fee_to_transaction(orcamento, calculation)
    return orcamento


def _save_orcamento_with_items(orcamento, formset):
    orcamento.save()
    formset.instance = orcamento
    formset.save()
    sync_card_fee_expense(
        orcamento,
        "orcamento_card_fee",
        "Orçamento",
        should_create=_orcamento_finaliza_financeiro(orcamento),
    )
    return orcamento


def _servico_orcamento_payload(servico):
    return {
        'id': servico.pk,
        'text': servico.servico,
        'name': servico.servico,
        'meta': 'Serviço',
    }


def _orcamento_custos_lucros_context(orcamento):
    item_rows = []
    total_bruto = ZERO
    custo_total = ZERO
    total_pecas = 0
    total_servicos = 0

    for item in orcamento.orcamento_items.select_related('peca', 'servico').all():
        quantidade = item.quantidade or 0
        subtotal = _money(item.preco_orcamento * quantidade)
        custo_unitario = _money(item.peca.preco_de_custo if item.peca_id else ZERO)
        custo_item = _money(custo_unitario * quantidade)
        lucro_item = _money(subtotal - custo_item)

        if item.peca_id:
            tipo = 'Peça'
            nome = str(item.peca)
            total_pecas += quantidade
        else:
            tipo = 'Serviço'
            nome = str(item.servico) if item.servico_id else 'Item não informado'
            total_servicos += quantidade

        item_rows.append({
            'tipo': tipo,
            'nome': nome,
            'quantidade': quantidade,
            'preco_unitario': _money(item.preco_orcamento),
            'subtotal': subtotal,
            'custo_unitario': custo_unitario,
            'custo_total': custo_item,
            'lucro': lucro_item,
            'margem': _percent(lucro_item, subtotal),
        })
        total_bruto += subtotal
        custo_total += custo_item

    desconto = _money(orcamento.desconto)
    receita_liquida_itens = max(_money(total_bruto - desconto), ZERO)
    taxa_absorvida = (
        _money(orcamento.card_fee_amount)
        if orcamento.card_payment_type and not orcamento.pass_card_fee_to_customer
        else ZERO
    )
    taxa_repassada = (
        _money(orcamento.card_fee_amount)
        if orcamento.card_payment_type and orcamento.pass_card_fee_to_customer
        else ZERO
    )
    lucro_bruto = _money(total_bruto - custo_total)
    lucro_apos_desconto = _money(receita_liquida_itens - custo_total)
    lucro_liquido = _money(lucro_apos_desconto - taxa_absorvida)
    total_cobrado = _money(orcamento.total())
    quantidade_itens = total_pecas + total_servicos

    return {
        'item_rows': item_rows,
        'total_bruto': _money(total_bruto),
        'receita_liquida_itens': receita_liquida_itens,
        'total_cobrado': total_cobrado,
        'desconto_total': desconto,
        'custo_total': _money(custo_total),
        'lucro_bruto': lucro_bruto,
        'lucro_apos_desconto': lucro_apos_desconto,
        'taxa_absorvida': taxa_absorvida,
        'taxa_repassada': taxa_repassada,
        'lucro_liquido_individual': lucro_liquido,
        'margem_lucro_individual': _percent(lucro_liquido, receita_liquida_itens),
        'markup_individual': _percent(lucro_liquido, custo_total),
        'ticket_medio_item': _money(receita_liquida_itens / quantidade_itens) if quantidade_itens else ZERO,
        'quantidade_itens': quantidade_itens,
        'quantidade_pecas': total_pecas,
        'quantidade_servicos': total_servicos,
    }


def _base_orcamento_queryset(user):
    return (
        Orcamento.objects
        .filter(usuario=user)
        .select_related('cliente', 'tecnico', 'card_machine')
        .prefetch_related('orcamento_items__peca', 'orcamento_items__servico')
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


def _orcamento_dashboard_context(user, params):
    qs = _base_orcamento_queryset(user)
    object_list, inicio, fim, periodo = aplicar_filtro_periodo(qs, SimpleNamespace(GET=params))
    context = {'object_list': object_list}
    context.update(metricas_orcamento(object_list))
    context.update(build_orcamento_dashboard_charts(user, params))
    context.update({
        'inicio': inicio or '',
        'fim': fim or '',
        'periodo': periodo or '',
    })
    return context


def _render_dashboard_update(request, trigger=None):
    context = _orcamento_dashboard_context(request.user, _dashboard_params_from_request(request))
    response = render(request, 'orcamento/bloco-dados.html', context)
    response['HX-Retarget'] = '#bloco-dados'
    response['HX-Reswap'] = 'outerHTML'
    if trigger:
        response['HX-Trigger'] = trigger
    return response


class ListaOrcamento(LoginRequiredMixin, ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento
    context_object_name = 'object_list'

    def get_queryset(self):
        qs = _base_orcamento_queryset(self.request.user)
        qs, self._inicio, self._fim, self._periodo = aplicar_filtro_periodo(qs, self.request)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        metricas = metricas_orcamento(context['object_list'])
        context.update(metricas)
        context.update(build_orcamento_dashboard_charts(self.request.user, self.request.GET))
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
                template='orcamento/bloco-dados.html',
                context=context,
                **response_kwargs,
            )
        return super().render_to_response(context, **response_kwargs)



@login_required
def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    orcamento_instance = Orcamento()

    form = OrcamentoForms(request.POST or None, usuario=request.user, initial={'usuario': request.user}, instance=orcamento_instance, prefix='main')
    formset = _criar_items_formset(request.user, orcamento_instance, request.POST or None)
    submission_token = request.POST.get('submission_token') or _criar_submission_token(request.user, 'orcamento')

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            try:
                orcamento = _prepare_orcamento_for_save(request.user, form, formset)
            except ValidationError as error:
                _add_card_fee_error(form, error)
            else:
                with transaction.atomic():
                    if not _consumir_submission_token(request.user, 'orcamento', submission_token):
                        response = HttpResponse('Este orçamento já foi processado.', status=409)
                        response['HX-Trigger'] = 'orcamentoDuplicado'
                        return response
                    orcamento = _save_orcamento_with_items(orcamento, formset)
                return _render_dashboard_update(request, 'orcamentoSalvo')

    context = {
        'form': form,
        'formset': formset,
        'submission_token': submission_token,
        'exibir_linha_servico_inicial': _exibir_linha_servico_inicial(
            formset, request.POST if request.method == 'POST' else None
        ),
    }
    context.update(_dashboard_form_context(request))
    return render(request, template_name, context)

    
@login_required
def editarorcamento(request, pk):
    template_name = 'orcamento/formularios/formulario-editar-orcamento.html'
    orcamento_instance = get_object_or_404(Orcamento, pk=pk)

    form = OrcamentoForms(request.POST or None, usuario=request.user, initial={'usuario': request.user}, instance=orcamento_instance, prefix='main')
    formset = _criar_items_formset(request.user, orcamento_instance, request.POST or None)

    if orcamento_instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            try:
                orcamento = _prepare_orcamento_for_save(request.user, form, formset)
            except ValidationError as error:
                _add_card_fee_error(form, error)
            else:
                with transaction.atomic():
                    orcamento = _save_orcamento_with_items(orcamento, formset)
                return _render_dashboard_update(request, 'orcamentoSalvo')

    context = {
        'object': orcamento_instance,
        'form': form,
        'formset': formset,
        'exibir_linha_servico_inicial': _exibir_linha_servico_inicial(
            formset, request.POST if request.method == 'POST' else None
        ),
    }
    context.update(_dashboard_form_context(request))
    return render(request, template_name, context)


@login_required
def apagarorcamento(request, pk):
    obj = get_object_or_404(Orcamento, pk=pk, usuario=request.user)
    obj.delete()
    return _render_dashboard_update(request, 'orcamentoExcluido')


@login_required
def adicionarlinhas(request):
    template_name = 'orcamento/formularios/linha-peca-orcamento.html'
    formset = _criar_items_formset(request.user)
    context = {'items_orcamento_form': formset.empty_form}
    return render(request, template_name, context)


@login_required
def adicionarlinhaservico(request):
    template_name = 'orcamento/formularios/linha-servico-orcamento.html'
    formset = _criar_items_formset(request.user)
    context = {'items_orcamento_form': formset.empty_form}
    return render(request, template_name, context)



@login_required
def preco_peca(request):
    peca_pk = None
    item_index = '0'

    for key, value in request.GET.items():
        if key.endswith('-peca') and value:
            peca_pk = value
            parts = key.split('-')
            if len(parts) >= 2:
                item_index = parts[1]
            break

    trigger = request.headers.get('HX-Trigger', '')
    if trigger.endswith('-peca'):
        parts = trigger.split('-')
        if len(parts) >= 2:
            item_index = parts[1]

    if not peca_pk:
        values = list(request.GET.values())
        if values:
            peca_pk = values[0]

    if not peca_pk:
        return HttpResponseBadRequest('Peça não informada')

    peca = get_object_or_404(Pecas, pk=peca_pk, usuario=request.user)
    return JsonResponse({
        'preco': str(peca.preco_peca),
        'index': item_index,
    })


@login_required
def buscarservicosorcamento(request):
    termo = request.GET.get('q', '').strip()
    servicos = Servico.objects.filter(usuario=request.user)

    if termo:
        servicos = servicos.filter(Q(servico__icontains=termo))

    servicos = servicos.order_by('servico')[:30]
    return JsonResponse({'results': [_servico_orcamento_payload(servico) for servico in servicos]})


@login_required
def previewtaxacartaoorcamento(request):
    forma_pagamento = request.GET.get('forma_pagamento', '')
    base_amount = request.GET.get('base_amount') or 0
    pass_fee = request.GET.get('pass_fee') in ('1', 'true', 'on', 'True')
    installments = request.GET.get('installments') or None
    machine_pk = request.GET.get('card_machine') or None

    preview = preview_card_fee(request.user, forma_pagamento, machine_pk, installments, base_amount, pass_fee)
    return JsonResponse(preview['payload'], status=preview['status'])



@login_required
def apagaritemorcamento(request, pk):
    item_orcamento = ItemsOrcamento.objects.select_related('orcamento').get(pk=pk)
    if item_orcamento.orcamento_id and item_orcamento.orcamento.usuario_id != request.user.id:
        raise PermissionError
    item_orcamento.delete()
    return HttpResponse('')


class DetalheOrcamento(DetailView):
    model = Orcamento
    template_name= 'orcamento/detalhe-orcamento.html'

    def get_queryset(self):
        return (
            Orcamento.objects
            .filter(usuario=self.request.user)
            .select_related('cliente', 'tecnico', 'usuario', 'card_machine')
            .prefetch_related('orcamento_items__peca', 'orcamento_items__servico')
        )


class RelatorioOrcamentoIndividual(DetailView):
    model = Orcamento
    template_name = 'orcamento/relatorios/relatorio-orcamento-individual.html'

    def get_queryset(self):
        return (
            Orcamento.objects
            .filter(usuario=self.request.user)
            .select_related('cliente', 'tecnico', 'usuario', 'card_machine')
            .prefetch_related('orcamento_items__peca', 'orcamento_items__servico')
        )
    

class RelatorioLucroOrcamento(DetailView):
    model = Orcamento
    template_name = 'orcamento/relatorios/relatorio-lucro-orcamento.html'

    def get_queryset(self):
        return (
            Orcamento.objects
            .filter(usuario=self.request.user)
            .select_related('cliente', 'tecnico', 'usuario', 'card_machine')
            .prefetch_related('orcamento_items__peca', 'orcamento_items__servico')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_orcamento_custos_lucros_context(self.object))
        return context



def total_orcamento(request):
    template_name = 'orcamento/relatorios/relatorio-orcamento.html'
    total = sum(tot.total() for tot in Orcamento.objects.filter(usuario=request.user, status='Finalizado e entregue'))
    qtd_orcamento = Orcamento.objects.filter(usuario=request.user).count()
    context = {'total_orcamento': total, 'qtd_orcamento': qtd_orcamento}
    return render(request, template_name, context)



@login_required
def cadastrarservico(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-servico.html'
    picker_mode = request.GET.get('picker') == '1' or request.POST.get('service_picker') == '1'
    form = ServicoForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            servico = form.save()
            if picker_mode:
                response = HttpResponse('')
                response['HX-Trigger'] = json.dumps({'orcamentoServicoCriado': _servico_orcamento_payload(servico)})
                return response

            template_name = 'orcamento/tabela/linhas-tabela-servico.html'
            context = {'object': servico}
            response = render(request, template_name, context)
            response['HX-Trigger'] = 'orcamentoServicoSalvo'
            return response
    
    context = {'form': form, 'service_picker_mode': picker_mode}
    return render(request, template_name, context)
    


class ListaServicos(ListView):
    model = Servico
    template_name = 'orcamento/lista-servico-orcamento.html'

    def get_queryset(self):
        return Servico.objects.filter(usuario=self.request.user)

def apagarservico(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    obj = get_object_or_404(Servico, pk=pk)
    if obj.usuario_id != request.user.id:
        raise PermissionError

    if ItemsOrcamento.objects.filter(servico=obj).exists():
        response = HttpResponse(
            '<td colspan="3" class="text-danger">Este serviço já possui orçamentos vinculados e não pode ser excluído.</td>',
            status=409,
        )
        response['HX-Trigger'] = 'orcamentoServicoDeleteBloqueado'
        return response

    obj.delete()
    response = HttpResponse('')
    response['HX-Trigger'] = 'orcamentoServicoExcluido'
    return response
