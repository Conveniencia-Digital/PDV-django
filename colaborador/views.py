from django.shortcuts import render
from django.views.generic import ListView, DetailView
from colaborador.models import Colaborador
from colaborador.forms import ColaboradorForms
from django.contrib.auth.decorators import login_required


class ListaColaborador(ListView):
    model = Colaborador
    template_name = 'colaborador/pagina-inicial-colaborador.html'

    def get_queryset(self):
        return Colaborador.objects.filter(usuario=self.request.user)


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