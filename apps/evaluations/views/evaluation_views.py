from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.base.views.genericlistview import OptimizedSecureListView
from apps.evaluations.mixins.evaluation_mixins import EvaluationViewMixin
from apps.evaluations.models.evaluationsmodel import Evaluation, Answer, Report

User = get_user_model()

class EvaluationListView(OptimizedSecureListView):
    """
    Vista optimizada para listar evaluaciones con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'evaluations.view_evaluation'
    model = Evaluation
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'status']
    # Ordenamiento por defecto
    order_by = ('-start_date',)
    
    # Atributos específicos
    title = _('Listado de Evaluaciones')
    entity = 'Evaluaciones'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
       
        # Filtrar por estado
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filtrar por usuario
        user_id = self.request.GET.get('user', '')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Si el usuario no es staff, solo ver sus propias evaluaciones
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['USUARIO', 'INICIO', 'FIN', 'ESTADO', 'RESPUESTAS']
        context['fields'] = ['user.username', 'start_date', 'end_date', 'get_status_display', 'answers.count']
        
        # Configuración de botones y acciones
        if self.request.user.is_staff:
            context['Btn_Add'] = [
                {
                    'name': 'add',
                    'label': 'Crear Evaluación',
                    'icon': 'add',
                    'url': 'evaluations:evaluation_create',
                    'modal': True,
                }
            ]
        
        context['actions'] = [
            {
                'name': 'detail',
                'label': '',
                'icon': 'visibility',
                'color': 'info',
                'color2': 'white',
                'url': 'evaluations:evaluation_detail'
            },
            {
                'name': 'report',
                'label': '',
                'icon': 'assessment',
                'color': 'success',
                'color2': 'white',
                'url': 'evaluations:report_create'
            }
        ]
        
        # Solo permitir edición y eliminación a staff
        if self.request.user.is_staff:
            context['actions'].extend([
                {
                    'name': 'edit',
                    'label': '',
                    'icon': 'edit',
                    'color': 'secondary',
                    'color2': 'brown',
                    'url': 'evaluations:evaluation_update',
                    'modal': True
                },
                {
                    'name': 'delete',
                    'label': '',
                    'icon': 'delete',
                    'color': 'danger',
                    'color2': 'white',
                    'url': 'evaluations:evaluation_delete',
                    'modal': True
                }
            ])
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:evaluation_list')
        
        # Filtros adicionales
        context['filters'] = [
            {
                'name': 'status',
                'label': 'Estado',
                'options': [{'id': 'started', 'name': 'Iniciado'}, {'id': 'completed', 'name': 'Completado'}],
                'value_field': 'id',
                'label_field': 'name'
            }
        ]
        
        # Filtro de usuarios solo para staff
        if self.request.user.is_staff:
            context['filters'].append({
                'name': 'user',
                'label': 'Usuario',
                'options': User.objects.all(),
                'value_field': 'id',
                'label_field': 'username'
            })
        
        return context


class EvaluationCreateView(LoginRequiredMixin, PermissionRequiredMixin, EvaluationViewMixin, CreateView):
    permission_required = 'evaluations.add_evaluation'
    model = Evaluation
    template_name = 'core/create.html'
    fields = ['user', 'status']
    success_url = reverse_lazy('evaluations:evaluation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Evaluación')
        context['entity'] = _('Evaluaciones')
        context['list_url'] = 'evaluations:evaluation_list'
        context['action'] = 'add'
        
        # Obtener usuarios para el formulario
        context['users'] = User.objects.all()
        
        return context

    def form_valid(self, form):
        # Asegurarse de que los campos de fecha estén correctos
        if form.instance.status == 'completed' and not form.instance.end_date:
            form.instance.end_date = timezone.now()
            
        messages.success(self.request, _('Evaluación creada exitosamente'))
        return super().form_valid(form)


class EvaluationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EvaluationViewMixin, UpdateView):
    model = Evaluation
    template_name = 'core/create.html'
    fields = ['user', 'status', 'end_date']
    permission_required = 'evaluations.change_evaluation'
    success_url = reverse_lazy('evaluations:evaluation_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Evaluación')
        context['entity'] = _('Evaluaciones')
        context['list_url'] = 'evaluations:evaluation_list'
        context['action'] = 'update'
        
        # Obtener usuarios para el formulario
        context['users'] = User.objects.all()
        
        return context
    
    def form_valid(self, form):
        # Si se marca como completado, añadir fecha de finalización
        if form.instance.status == 'completed' and not form.instance.end_date:
            form.instance.end_date = timezone.now()
            
        messages.success(self.request, _('Evaluación actualizada exitosamente'))
        return super().form_valid(form)


class EvaluationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Evaluation
    template_name = 'core/del.html'
    context_object_name = 'evaluation'
    permission_required = 'evaluations.delete_evaluation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Evaluación'
        context['entity'] = 'Evaluaciones'
        context['texto'] = f'¿Seguro de eliminar la evaluación de {self.object.user.username} del {self.object.start_date.strftime("%d/%m/%Y")}?'
        context['list_url'] = 'evaluations:evaluation_list'
        
        # Advertir sobre reportes relacionados
        has_report = Report.objects.filter(evaluation=self.object).exists()
        if has_report:
            context['warning'] = 'ADVERTENCIA: Esta evaluación tiene reportes asociados que también serán eliminados.'
            
        return context
    
    def delete(self, request, *args, **kwargs):
        evaluation = self.get_object()
        success_message = _('Evaluación eliminada exitosamente')
        
        # Guardar información antes de eliminar
        username = evaluation.user.username
        date = evaluation.start_date.strftime("%d/%m/%Y")
        
        # Realizar la eliminación
        self.object = evaluation
        evaluation.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            success_url = reverse_lazy('evaluations:evaluation_list')
            return JsonResponse({
                'success': True,
                'message': _(f'Evaluación de {username} del {date} eliminada exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('evaluations:evaluation_list')


class EvaluationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Evaluation
    template_name = 'evaluations/evaluation_detail.html'
    context_object_name = 'evaluation'
    permission_required = 'evaluations.view_evaluation'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        # Si no es staff, solo ver sus propias evaluaciones
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de Evaluación'
        context['entity'] = 'Evaluaciones'
        context['list_url'] = 'evaluations:evaluation_list'
        
        # Obtener respuestas para esta evaluación
        answers = Answer.objects.filter(evaluation=self.object).select_related('question', 'question__competence')
        context['answers'] = answers
        
        # Verificar si hay un reporte asociado
        try:
            context['report'] = self.object.report
        except:
            context['report'] = None
        
        return context