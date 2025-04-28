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
from apps.evaluations.mixins.competence_mixin import CompetenceViewMixin
from apps.evaluations.models.evaluationsmodel import Competence, ProfessionalArea


class CompetenceListView(OptimizedSecureListView):
    """
    Vista optimizada para listar competencias con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'evaluations.view_competence'
    model = Competence
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name', 'description']
    # Ordenamiento por defecto
    order_by = ('name',)
    
    # Atributos específicos
    title = _('Listado de Competencias')
    entity = 'Competencias'
    
    def get_queryset(self):
        queryset = super().get_queryset()
       
        area_id = self.request.GET.get('area', '')
        if area_id:
            queryset = queryset.filter(related_areas__id=area_id).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE', 'DESCRIPCIÓN']
        context['fields'] = ['name', 'description']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Crear Competencia',
                'icon': 'add',
                'url': 'evaluations:competence_create',
                'modal': True,
            },
            {
                'name': 'import',
                'label': 'Importar Competencias',
                'icon': 'file_upload',
                'url': 'evaluations:competence-upload',
                'modal': False,
            }
        ]
        
        # URL para exportar competencias si se desea implementar
        context['url_export'] = 'evaluations:competence-download'
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'evaluations:competence_update',
                'modal': True
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'evaluations:competence_delete',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:competence_list')
        
        # Filtros adicionales
        context['filters'] = [
            {
                'name': 'area',
                'label': 'Área Profesional',
                'options': ProfessionalArea.objects.all(),
                'value_field': 'id',
                'label_field': 'name'
            }
        ]
        
        return context


class CompetenceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompetenceViewMixin, CreateView):
    permission_required = 'evaluations.add_competence'
    model = Competence
    template_name = 'core/create.html'
    fields = ['name', 'description', 'related_areas']
    success_url = reverse_lazy('evaluations:competence_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Competencia')
        context['entity'] = _('Competencias')
        context['list_url'] = 'evaluations:competence_list'
        context['action'] = 'add'
        
        # Obtener todas las áreas profesionales para el formulario
        context['areas'] = ProfessionalArea.objects.all()
        
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Competencia creada exitosamente'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Por favor corrija los errores en el formulario'))
        return super().form_invalid(form)

    
class CompetenceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompetenceViewMixin, UpdateView):
    model = Competence
    template_name = 'core/create.html'
    fields = ['name', 'description', 'related_areas']
    permission_required = 'evaluations.change_competence'
    success_url = reverse_lazy('evaluations:competence_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Competencia')
        context['entity'] = _('Competencias')
        context['list_url'] = 'evaluations:competence_list'
        context['action'] = 'update'
        
        # Obtener todas las áreas profesionales para el formulario
        context['areas'] = ProfessionalArea.objects.all()
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Competencia actualizada exitosamente'))
        return super().form_valid(form)


class CompetenceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Competence
    template_name = 'core/del.html'
    context_object_name = 'competence'
    permission_required = 'evaluations.delete_competence'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Competencia'
        context['entity'] = 'Competencias'
        context['texto'] = f'¿Seguro de eliminar la competencia "{self.object.name}"?'
        context['list_url'] = 'evaluations:competence_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        competence = self.get_object()
        success_message = _(f'Competencia eliminada exitosamente')
        
        # Guardar el nombre antes de eliminar
        competence_name = competence.name
        
        # Realizar la eliminación
        self.object = competence
        competence.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Obtenemos la URL de éxito
            success_url = reverse_lazy('evaluations:competence_list')
            return JsonResponse({
                'success': True,
                'message': _(f'Competencia "{competence_name}" eliminada exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('evaluations:competence_list')
    
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

class CompetenceImportView(GenericCSVImportView):
    model = Competence
    success_url = reverse_lazy('evaluations:competence_list')
    # additional_exclude_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Importar Competencias')
        context['entity'] = _('Competencias')
        context['list_url'] = 'evaluations:competence_list'
        return context

    def clean_row_data(self, row):
        clean_data = super().clean_row_data(row)
        
        if 'related_areas' in clean_data:
            # Obtener las áreas profesionales relacionadas
            area_ids = clean_data['related_areas'].split(',')
            clean_data['related_areas'] = ProfessionalArea.objects.filter(id__in=area_ids)
        return clean_data

class CompetenceExportView(GenericExportView):
    model = Competence
    success_url = reverse_lazy('evaluations:competence_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['export_formats'] = [
            {'format': 'csv', 'label': _('CSV')},
            {'format': 'pdf', 'label': _('PDF')},
            {'format': 'excel', 'label': _('Excel')}
        ]
        return context