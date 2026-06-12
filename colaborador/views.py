from django.shortcuts import render
from django.views.generic import ListView, DetailView
from colaborador.models import Colaborador
from colaborador.forms import ColaboradorForms
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse


class ListaColaborador(ListView):
    model = Colaborador
    template_name = 'colaborador/pagina-inicial-colaborador.html'

    def get_queryset(self):
        return Colaborador.objects.filter(usuario=self.request.user)


def _colaborador_payload(colaborador):
    meta = colaborador.telefone_contato or colaborador.cargo or ''
    return {
        'id': colaborador.pk,
        'text': colaborador.nome_colaborador,
        'name': colaborador.nome_colaborador,
        'phone': colaborador.telefone_contato or '',
        'meta': meta,
    }


@login_required
def buscarvendedores(request):
    termo = request.GET.get('q', '').strip()
    vendedores = Colaborador.objects.filter(usuario=request.user)

    if termo:
        vendedores = vendedores.filter(
            Q(nome_colaborador__icontains=termo)
            | Q(telefone_contato__icontains=termo)
            | Q(telefone_contato_2__icontains=termo)
            | Q(cargo__icontains=termo)
        )

    vendedores = vendedores.order_by('nome_colaborador')[:30]
    return JsonResponse({'results': [_colaborador_payload(vendedor) for vendedor in vendedores]})


@login_required
def cadastrarcolaborador(request):
    template_name = 'colaborador/formularios/formulario-cadastrar-colaborador.html'
    form = ColaboradorForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            colaborador = form.save()
            template_name = 'colaborador/tabela/linhas-tabela-colaborador.html'

            context = {'object': colaborador}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)



@login_required
def editarcolaborador(request, pk):
    template_name = 'colaborador/formularios/formulario-editar-colaborador.html'
    instance = Colaborador.objects.get(pk=pk)
    form = ColaboradorForms(request.POST or None, instance=instance, initial={'usuario': request.user})

    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            colaborador = form.save()
            template_name = 'colaborador/tabela/linhas-tabela-colaborador.html'
            context = {'object': colaborador}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarcolaborador(request, pk):
    template_name = 'colaborador/tabela/tabela-colaborador.html'
    obj = Colaborador.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
    else:
        raise PermissionError
    return render(request, template_name)



class DetalheColaboradorView(DetailView):
    model = Colaborador
    template_name = 'colaborador/off-canvas/detalhe-colaborador.html'
#source /Users/convenienciadigital/Documents/GitHub/PDV-django/venv/bin/activate


@login_required
def total_colaborador(request):
    template_name = 'colaborador/informacao-colaborador.html'
    total_colaborador =  Colaborador.objects.count()
    context = {'total_colaborador': total_colaborador}
    return render(request, template_name, context)
