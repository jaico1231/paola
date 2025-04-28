from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model

from apps.base.views.genericlistview import OptimizedSecureListView
from apps.evaluations.mixins.report_mixins import ReportViewMixin
from apps.evaluations.models.evaluationsmodel import (
    Report, Evaluation, AreaResult, CompetenceResult, 
    Recommendation, ProfessionalArea, Competence
)

User = get_user_model()

class ReportListView(OptimizedSecureListView):
    """
    Vista optimizada para listar reportes con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'evaluations.view_report'
    model = Report
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'report_type']
    # Ordenamiento por defecto
    order_by = ('-generation_date',)
    
    # Atributos específicos
    title = _('Listado de Reportes')
    entity = 'Reportes'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'evaluation')
       
        # Filtrar por tipo de reporte
        report_type = self.request.GET.get('report_type', '')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
            
        # Filtrar por usuario
        user_id = self.request.GET.get('user', '')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Si el usuario no es staff, solo ver sus propios reportes
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['USUARIO', 'TIPO', 'FECHA GENERACIÓN', 'ÁREAS', 'COMPETENCIAS']
        context['fields'] = ['user.username', 'get_report_type_display', 'generation_date', 'area_results.count', 'competence_results.count']
        
        # Configuración de botones y acciones
        if self.request.user.is_staff:
            context['Btn_Add'] = [
                {
                    'name': 'add',
                    'label': 'Crear Reporte',
                    'icon': 'add',
                    'url': 'evaluations:report_create_select',
                }
            ]
        
        context['actions'] = [
            {
                'name': 'detail',
                'label': '',
                'icon': 'visibility',
                'color': 'info',
                'color2': 'white',
                'url': 'evaluations:report_detail'
            },
            {
                'name': 'pdf',
                'label': '',
                'icon': 'file_download',
                'color': 'success',
                'color2': 'white',
                'url': 'evaluations:report_pdf'
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
                    'url': 'evaluations:report_update',
                },
                {
                    'name': 'delete',
                    'label': '',
                    'icon': 'delete',
                    'color': 'danger',
                    'color2': 'white',
                    'url': 'evaluations:report_delete',
                    'modal': True
                }
            ])
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:report_list')
        
        # Filtros adicionales
        context['filters'] = [
            {
                'name': 'report_type',
                'label': 'Tipo',
                'options': [{'id': 'partial', 'name': 'Parcial'}, {'id': 'complete', 'name': 'Completo'}],
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


class ReportCreateSelectView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para seleccionar una evaluación para crear un reporte"""
    permission_required = 'evaluations.add_report'
    model = Evaluation
    template_name = 'reports/select_evaluation.html'
    context_object_name = 'evaluations'
    
    def get_queryset(self):
        # Obtener evaluaciones completadas sin reporte
        return Evaluation.objects.filter(
            status='completed'
        ).exclude(
            id__in=Report.objects.values_list('evaluation_id', flat=True)
        ).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Seleccionar Evaluación para Reporte'
        context['entity'] = 'Reportes'
        context['list_url'] = 'evaluations:report_list'
        return context


class ReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, ReportViewMixin, CreateView):
    permission_required = 'evaluations.add_report'
    model = Report
    template_name = 'reports/report_form.html'
    fields = ['user', 'evaluation', 'report_type']
    
    def get_initial(self):
        initial = super().get_initial()
        # Si se especifica una evaluación en la URL, usarla
        evaluation_id = self.kwargs.get('evaluation_id')
        if evaluation_id:
            evaluation = get_object_or_404(Evaluation, id=evaluation_id)
            initial['evaluation'] = evaluation
            initial['user'] = evaluation.user
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Reporte')
        context['entity'] = _('Reportes')
        context['list_url'] = 'evaluations:report_list'
        context['action'] = 'add'
        
        # Obtener usuarios y evaluaciones disponibles
        context['users'] = User.objects.all()
        
        # Evaluaciones completadas sin reporte (excepto si ya se seleccionó una)
        evaluation_id = self.kwargs.get('evaluation_id')
        if evaluation_id:
            context['evaluations'] = Evaluation.objects.filter(id=evaluation_id)
        else:
            context['evaluations'] = Evaluation.objects.filter(
                status='completed'
            ).exclude(
                id__in=Report.objects.values_list('evaluation_id', flat=True)
            )
        
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Generar los resultados por áreas y competencias
        self.generate_report_results()
        
        messages.success(self.request, _('Reporte generado exitosamente'))
        return response
    
    def generate_report_results(self):
        """Genera los resultados del reporte basado en las respuestas de la evaluación"""
        report = self.object
        evaluation = report.evaluation
        
        # Generar resultados por área profesional
        self.generate_area_results(report, evaluation)
        
        # Generar resultados por competencia
        self.generate_competence_results(report, evaluation)
        
        # Generar recomendaciones basadas en los resultados de áreas
        self.generate_recommendations(report)
    
    def generate_area_results(self, report, evaluation):
        """Genera los resultados por área profesional"""
        # Lógica básica para calcular resultados por área
        # En una implementación real, esta lógica sería más compleja
        areas = ProfessionalArea.objects.all()
        
        for area in areas:
            # Cálculo simulado (en un caso real, sería basado en respuestas)
            # Se asigna un puntaje aleatorio entre 60 y 95 para demostración
            import random
            score = random.uniform(60.0, 95.0)
            
            AreaResult.objects.create(
                report=report,
                area=area,
                score=round(score, 2)
            )
    
    def generate_competence_results(self, report, evaluation):
        """Genera los resultados por competencia"""
        # Similar a la generación de áreas, pero para competencias
        competences = Competence.objects.all()
        
        for competence in competences:
            # Cálculo simulado
            import random
            score = random.uniform(50.0, 90.0)
            
            CompetenceResult.objects.create(
                report=report,
                competence=competence,
                score=round(score, 2)
            )
    
    def generate_recommendations(self, report):
        """Genera recomendaciones basadas en los resultados de áreas"""
        # Obtener las 3 áreas con mayor puntaje
        top_areas = AreaResult.objects.filter(
            report=report
        ).order_by('-score')[:3]
        
        # Crear recomendaciones para estas áreas
        for i, area_result in enumerate(top_areas):
            Recommendation.objects.create(
                report=report,
                area=area_result.area,
                text=f"Se recomienda explorar carreras relacionadas con {area_result.area.name} ya que muestra una fuerte afinidad con esta área.",
                priority=3-i  # Mayor prioridad para mayor puntaje
            )


class ReportUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ReportViewMixin, UpdateView):
    model = Report
    template_name = 'reports/report_form.html'
    fields = ['report_type']
    permission_required = 'evaluations.change_report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Reporte')
        context['entity'] = _('Reportes')
        context['list_url'] = 'evaluations:report_list'
        context['action'] = 'update'
        
        # Mostrar resultados actuales
        context['area_results'] = self.object.area_results.all()
        context['competence_results'] = self.object.competence_results.all()
        context['recommendations'] = self.object.recommendations.all()
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Reporte actualizado exitosamente'))
        return super().form_valid(form)


class ReportDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Report
    template_name = 'core/del.html'
    context_object_name = 'report'
    permission_required = 'evaluations.delete_report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Reporte'
        context['entity'] = 'Reportes'
        context['texto'] = f'¿Seguro de eliminar el reporte de {self.object.user.username} generado el {self.object.generation_date.strftime("%d/%m/%Y")}?'
        context['list_url'] = 'evaluations:report_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        report = self.get_object()
        success_message = _('Reporte eliminado exitosamente')
        
        # Guardar información antes de eliminar
        username = report.user.username
        date = report.generation_date.strftime("%d/%m/%Y")
        
        # Realizar la eliminación
        self.object = report
        report.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            success_url = reverse_lazy('evaluations:report_list')
            return JsonResponse({
                'success': True,
                'message': _(f'Reporte de {username} del {date} eliminado exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('evaluations:report_list')


class ReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    permission_required = 'evaluations.view_report'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'evaluation')
        # Si no es staff, solo ver sus propios reportes
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de Reporte'
        context['entity'] = 'Reportes'
        context['list_url'] = 'evaluations:report_list'
        
        # Obtener resultados para este reporte
        context['area_results'] = self.object.area_results.all().select_related('area').order_by('-score')
        context['competence_results'] = self.object.competence_results.all().select_related('competence').order_by('-score')
        context['recommendations'] = self.object.recommendations.all().select_related('area').order_by('-priority')
        
        return context