from django.views.generic import ListView
from dashboard.forms import TarefaForms
from dashboard.models import Tarefas
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


class PaginaInicialView(ListView):
    model = Tarefas
    template_name = 'dashboard/pagina-inicial.html'
    
    def get_queryset(self):
        return Tarefas.objects.filter(usuario=self.request.user)



@login_required
def cadastrartarefa(request):
    template_name = 'dashboard/formularios/form-tarefa.html'
    form = TarefaForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            tarefa = form.save()
            template_name = 'dashboard/tabela/linha-tabela-tarefa.html'
            context = {'object': tarefa}
            return render(request, template_name, context)
    
    context = {'form': form}
    return render(request, template_name, context)




@login_required       
def apagartarefa(request, pk):
    template_name = 'dashboard/tabela/tabela-tarefa.html'
    obj = Tarefas.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
        return render(request, template_name)
    else:
        raise PermissionError




@login_required
def editartarefa(request, pk):
    template_name = 'dashboard/formularios/form-editar-tarefa.html'
    instance = Tarefas.objects.get(pk=pk)
    form = TarefaForms(request.POST or None, instance=instance)
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            template_name = 'dashboard/tabela/linha-tabela-tarefa.html'
            tarefa = form.save()
            context = {'object': tarefa}
            return render(request, template_name, context)
    
    context = {'form': form, 'object': instance}
    return render(request, template_name, context)
