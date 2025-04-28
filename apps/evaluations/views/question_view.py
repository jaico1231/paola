from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect

from apps.base.views.genericcsvimportview import GenericCSVImportView
from apps.base.views.genericexportview import GenericExportView
from apps.base.views.genericlistview import OptimizedSecureListView
# from apps.base.mixins.questionmixin import QuestionViewMixin  # Asumiendo que crearás este mixin

from apps.evaluations.mixins.question_mixin import QuestionViewMixin
from apps.evaluations.models.evaluationsmodel import Question, Competence
# from apps.vocational.models import Question, Competence  # Ajusta la importación según tu estructura


class QuestionListView(OptimizedSecureListView):
    """
    Vista optimizada para listar preguntas con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'vocational.view_question'
    model = Question
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['text', 'competence__name']
    # Ordenamiento por defecto
    order_by = ('competence__name', 'text')
    
    # Atributos específicos
    title = _('Banco de Preguntas')
    entity = 'Preguntas'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('competence')
       
        competence_id = self.request.GET.get('competence', '')
        if competence_id:
            queryset = queryset.filter(competence_id=competence_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['PREGUNTA', 'COMPETENCIA']
        context['fields'] = ['text', 'competence.name']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Crear Pregunta',
                'icon': 'add',
                'url': 'evaluations:question_create',
                'modal': True,
            },
            {
                'name': 'import',
                'label': 'Importar Preguntas',
                'icon': 'file_upload',
                'url': 'evaluations:question-upload',
                'modal': False,
            },
            
        ]
        
        # URL para exportar preguntas si se desea implementar
        context['url_export'] = 'evaluations:question-download'
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'evaluations:question_update',
                'modal': True
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'evaluations:question_delete',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:question_list')
        
        
        
        return context


class QuestionCreateView(LoginRequiredMixin, PermissionRequiredMixin, QuestionViewMixin, CreateView):
    permission_required = 'vocational.add_question'
    model = Question
    template_name = 'core/create.html'
    fields = ['text', 'competence']
    success_url = reverse_lazy('evaluations:question_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Pregunta')
        context['entity'] = _('Preguntas')
        context['list_url'] = 'evaluations:question_list'
        context['action'] = 'add'
        
        # Obtener todas las competencias para el formulario
        context['competences'] = Competence.objects.all()
        
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Pregunta creada exitosamente'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Por favor corrija los errores en el formulario'))
        return super().form_invalid(form)

    
class QuestionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Question
    template_name = 'core/create.html'
    fields = ['text', 'competence']
    permission_required = 'vocational.change_question'
    success_url = reverse_lazy('evaluations:question_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Pregunta')
        context['entity'] = _('Preguntas')
        context['list_url'] = 'evaluations:question_list'
        context['action'] = 'update'
        
        # Obtener todas las competencias para el formulario
        context['competences'] = Competence.objects.all()
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Pregunta actualizada exitosamente'))
        return super().form_valid(form)


class QuestionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Question
    template_name = 'core/del.html'
    context_object_name = 'question'
    permission_required = 'vocational.delete_question'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Pregunta'
        context['entity'] = 'Preguntas'
        context['texto'] = f'¿Seguro de eliminar la pregunta "{self.object.text[:50]}..."?'
        context['list_url'] = 'evaluations:question_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        success_message = _(f'Pregunta eliminada exitosamente')
        
        # Guardar parte del texto antes de eliminar
        question_text = question.text[:50]
        
        # Realizar la eliminación
        self.object = question
        question.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Obtenemos la URL de éxito
            success_url = reverse_lazy('evaluations:question_list')
            return JsonResponse({
                'success': True,
                'message': _(f'Pregunta "{question_text}..." eliminada exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('evaluations:question_list')
    
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


class QuestionImportView(GenericCSVImportView):
    """
    Vista para importar preguntas desde un archivo CSV.
    """
    model = Question
    success_url = reverse_lazy('evaluations:question_list')
    additional_exclude_fields = ['last_login']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Importar Preguntas')
        context['entity'] = _('Preguntas')
        context['list_url'] = 'evaluations:question_list'
        return context
    
    def clean_row_data(self, row):
        clean_data = super().clean_row_data(row)

        if 'competence' in clean_data:
            clean_data['competence'] = Competence.objects.get(name=clean_data['competence'])
        return clean_data

class QuestionExportView(GenericExportView):
    model = Question
    success_url = reverse_lazy('evaluations:question_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)        
        context['export_formats'] = [
            {'format': 'csv', 'label': _('CSV')},
            {'format': 'pdf', 'label': _('PDF')},
            {'format': 'excel', 'label': _('Excel')}
        ]
        return context