from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView

from financeiro.cash_closing import (
    build_cash_closing_dashboard,
    calculate_cash_closing_snapshot,
    create_cash_closing,
)
from financeiro.models import CardMachine, ContasAReceber
from financeiro.forms import CardMachineFeeTableForm, ContasAReceberForms, FechamentoCaixaForm
from financeiro.services import build_financial_dashboard
from venda.models import Vendas, ItemsVenda
from orcamento.models import Orcamento, ItemsOrcamento


def dashboard_financeiro(request):
    context = build_financial_dashboard(request.user, request.GET)
    return render(request, 'financeiro/dashboard-financeiro.html', context)


def fechamento_caixa(request):
    success = request.GET.get("success") == "1"
    duplicate_allowed = False
    form = FechamentoCaixaForm(request.POST or None, user=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                create_cash_closing(
                    user=request.user,
                    closing_date=form.cleaned_data["data"],
                    counted_balance=form.cleaned_data["valor_contado"],
                    notes=form.cleaned_data.get("observacao") or "",
                    allow_duplicate=form.cleaned_data.get("allow_duplicate"),
                )
            except ValueError as error:
                form.add_error("data", str(error))
            else:
                return redirect(f"{reverse('fechamento-caixa')}?success=1")
        duplicate_allowed = form.data.get("allow_duplicate") in ("on", "true", "1")

    closing_date = form.data.get("data") if request.method == "POST" else request.GET.get("data")
    if closing_date:
        try:
            from datetime import date

            selected_date = date.fromisoformat(closing_date)
        except (TypeError, ValueError):
            selected_date = None
    else:
        selected_date = None

    if selected_date:
        snapshot = calculate_cash_closing_snapshot(request.user, selected_date)
    else:
        snapshot = None

    context = build_cash_closing_dashboard(request.user, request.GET)
    context["form"] = form
    context["form_snapshot"] = snapshot or context["today_snapshot"]
    context["success"] = success
    context["duplicate_allowed"] = duplicate_allowed
    return render(request, "financeiro/fechamento-caixa.html", context)



class ListaContasAReceber(ListView):
    model = ContasAReceber
    template_name = 'financeiro/pagina-inicial-contas-a-receber.html'

    def get_queryset(self):
        return ContasAReceber.objects.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ListaContasAReceber, self).get_context_data(**kwargs)
        context['venda'] = Vendas.objects.filter(forma_pagamento = 'Fiado a receber', usuario=self.request.user)
        context['orcamento'] = Orcamento.objects.filter(forma_pagamento = 'Fiado a receber', usuario=self.request.user)
        return context 


class ListaMaquininhaCartao(ListView):
    model = CardMachine
    template_name = 'financeiro/maquininhas/lista-maquininhas.html'
    context_object_name = 'maquininhas'

    def get_queryset(self):
        return (
            CardMachine.objects
            .filter(usuario=self.request.user)
            .prefetch_related('fees')
            .order_by('name')
        )


def cadastrarmaquininhacartao(request):
    template_name = 'financeiro/maquininhas/formulario-maquininha.html'
    form = CardMachineFeeTableForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save(request.user)
        return redirect('maquininhas-cartao')

    return render(request, template_name, {'form': form, 'titulo': 'Cadastrar maquininha'})


def editarmaquininhacartao(request, pk):
    template_name = 'financeiro/maquininhas/formulario-maquininha.html'
    machine = get_object_or_404(CardMachine, pk=pk, usuario=request.user)
    form = CardMachineFeeTableForm(request.POST or None, instance=machine, user=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save(request.user)
        return redirect('maquininhas-cartao')

    return render(request, template_name, {'form': form, 'object': machine, 'titulo': 'Editar maquininha'})


def desativarmaquininhacartao(request, pk):
    if request.method != 'POST':
        return redirect('maquininhas-cartao')

    machine = get_object_or_404(CardMachine, pk=pk, usuario=request.user)
    machine.is_active = not machine.is_active
    machine.save(update_fields=['is_active', 'updated_at'])
    return redirect('maquininhas-cartao')


def cadastrarcontas_a_receber(request):
    template_name = 'financeiro/formularios/formulario-cadastrar-contas-a-receber.html'
   
    form = ContasAReceberForms(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            contas_a_receber = form.save()
            template_name = 'financeiro/tabela/linhas-tabela-contas-a-receber.html'

            context = {'object': contas_a_receber}
            return render(request, template_name, context)
    contas_a_receber = ContasAReceber.objects.filter(usuario=request.user)
    context = {'form': form}
    return render(request, template_name, context)


def editarcontas_a_receber(request, pk):
    template_name = 'financeiro/formularios/formulario-editar-contas-a-receber.html'
    instance = ContasAReceber.objects.get(pk=pk)
    form = ContasAReceberForms(request.POST or None, instance=instance, initial={'usuario': request.user}, user=request.user)
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            contas_a_receber = form.save()
            template_name = 'financeiro/tabela/linhas-tabela-contas-a-receber.html'
            context = {'object': contas_a_receber}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagarcontas_a_receber(request, pk):
    template_name = 'financeiro/tabela/tabela-contas-a-receber.html'
    obj = ContasAReceber.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
    else:
        raise PermissionError
    return render(request, template_name)


class DetalheFinanceiro(DetailView):
    model = ContasAReceber
    template_name = 'financeiro/off-canvas/off-canvas-financeiro.html'


class DetalheFinanceiroVenda(DetailView):
    model = Vendas
    template_name = 'financeiro/off-canvas/off-canvas-financeiro-vendas.html'

    def get_context_data(self, **kwargs):
        context = super(DetalheFinanceiroVenda, self).get_context_data(**kwargs)
        context['produto'] = ItemsVenda.objects.all()   
        return context


class DetalheFinanceiroOrcamento(DetailView):
    model = Orcamento
    template_name = 'financeiro/off-canvas/off-canvas-financeiro-orcamento.html'

    def get_context_data(self, **kwargs):
        context = super(DetalheFinanceiroOrcamento, self).get_context_data(**kwargs)
        context['peca'] = ItemsOrcamento.objects.all()   
        return context
