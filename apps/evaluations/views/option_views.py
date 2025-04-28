from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect

from apps.base.views.genericlistview import OptimizedSecureListView
from apps.evaluations.mixins.option_mixins import OptionViewMixin
from apps.evaluations.models.evaluationsmodel import Option, Question


class OptionListView(OptimizedSecureListView):
    """
    Vista optimizada para listar opciones con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'evaluations.view_option'
    model = Option
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['text', 'question__text']
    # Ordenamiento por defecto
    order_by = ('question__text', 'position')
    
    # Atributos específicos
    title = _('Listado de Opciones')
    entity = 'Opciones'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('question')
       
        question_id = self.request.GET.get('question', '')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['TEXTO', 'PREGUNTA', 'POSICIÓN']
        context['fields'] = ['text', 'question.text', 'position']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Crear Opción',
                'icon': 'add',
                'url': 'evaluations:option_create',
                'modal': True,
            }
        ]
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'evaluations:option_update',
                'modal': True
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'evaluations:option_delete',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:option_list')
        
        # Filtros adicionales
        context['filters'] = [
            {
                'name': 'question',
                'label': 'Pregunta',
                'options': Question.objects.all(),
                'value_field': 'id',
                'label_field': 'text'
            }
        ]
        
        return context


class OptionCreateView(LoginRequiredMixin, PermissionRequiredMixin, OptionViewMixin, CreateView):
    permission_required = 'evaluations.add_option'
    model = Option
    template_name = 'core/create.html'
    fields = ['question', 'text', 'position']
    success_url = reverse_lazy('evaluations:option_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Opción')
        context['entity'] = _('Opciones')
        context['list_url'] = 'evaluations:option_list'
        context['action'] = 'add'
        
        # Obtener todas las preguntas para el formulario
        context['questions'] = Question.objects.all()
        
        # Obtener la pregunta de la URL si existe
        question_id = self.request.GET.get('question', None)
        if question_id:
            context['selected_question'] = question_id
        
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Opción creada exitosamente'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Por favor corrija los errores en el formulario'))
        return super().form_invalid(form)

    
class OptionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, OptionViewMixin, UpdateView):
    model = Option
    template_name = 'core/create.html'
    fields = ['question', 'text', 'position']
    permission_required = 'evaluations.change_option'
    success_url = reverse_lazy('evaluations:option_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Opción')
        context['entity'] = _('Opciones')
        context['list_url'] = 'evaluations:option_list'
        context['action'] = 'update'
        
        # Obtener todas las preguntas para el formulario
        context['questions'] = Question.objects.all()
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Opción actualizada exitosamente'))
        return super().form_valid(form)


class OptionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Option
    template_name = 'core/del.html'
    context_object_name = 'option'
    permission_required = 'evaluations.delete_option'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Opción'
        context['entity'] = 'Opciones'
        context['texto'] = f'¿Seguro de eliminar la opción "{self.object.text}"?'
        context['list_url'] = 'evaluations:option_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        option = self.get_object()
        success_message = _('Opción eliminada exitosamente')
        
        # Guardar el texto antes de eliminar
        option_text = option.text
        question_id = option.question_id
        
        # Realizar la eliminación
        self.object = option
        option.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Redirigir a la lista filtrada por la pregunta
            success_url = reverse_lazy('evaluations:option_list') + f'?question={question_id}'
            return JsonResponse({
                'success': True,
                'message': _(f'Opción "{option_text}" eliminada exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        question_id = self.object.question_id
        return reverse_lazy('evaluations:option_list') + f'?question={question_id}'
    
    def post(self, request, *args, **kwargs):
        # Verificar si es una petición AJAX para confirmar eliminación
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                return self.delete(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
        return super().post(request, *args, **kwargs)