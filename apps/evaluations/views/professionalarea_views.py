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
from apps.evaluations.mixins.professionalarea_mixins import ProfessionalAreaViewMixin
from apps.evaluations.models.evaluationsmodel import ProfessionalArea, Competence


class ProfessionalAreaListView(OptimizedSecureListView):
    """
    Vista optimizada para listar áreas profesionales con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'evaluations.view_professionalarea'
    model = ProfessionalArea
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['name', 'description']
    # Ordenamiento por defecto
    order_by = ('name',)
    
    # Atributos específicos
    title = _('Listado de Áreas Profesionales')
    entity = 'Áreas Profesionales'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['NOMBRE', 'DESCRIPCIÓN']
        context['fields'] = ['name', 'description']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': 'Crear Área Profesional',
                'icon': 'add',
                'url': 'evaluations:professionalarea_create',
                'modal': True,
            },
            {
                'name': 'import',
                'label': 'Importar Áreas Profesionales',
                'icon': 'upload',
                'url': 'evaluations:professionalarea-upload',
                'modal': False,
            }
        ]
        
        # URL para exportar áreas profesionales si se desea implementar
        context['url_export'] = 'evaluations:professionalarea-download'
        
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'evaluations:professionalarea_update',
                'modal': True
            },
            {
                'name': 'delete',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'evaluations:professionalarea_delete',
                'modal': True
            }
        ]
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:professionalarea_list')
        
        return context


class ProfessionalAreaCreateView(LoginRequiredMixin, PermissionRequiredMixin, ProfessionalAreaViewMixin, CreateView):
    permission_required = 'evaluations.add_professionalarea'
    model = ProfessionalArea
    template_name = 'core/create.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('evaluations:professionalarea_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Área Profesional')
        context['entity'] = _('Áreas Profesionales')
        context['list_url'] = 'evaluations:professionalarea_list'
        context['action'] = 'add'
        
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Área Profesional creada exitosamente'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Por favor corrija los errores en el formulario'))
        return super().form_invalid(form)

    
class ProfessionalAreaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ProfessionalAreaViewMixin, UpdateView):
    model = ProfessionalArea
    template_name = 'core/create.html'
    fields = ['name', 'description']
    permission_required = 'evaluations.change_professionalarea'
    success_url = reverse_lazy('evaluations:professionalarea_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Área Profesional')
        context['entity'] = _('Áreas Profesionales')
        context['list_url'] = 'evaluations:professionalarea_list'
        context['action'] = 'update'
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Área Profesional actualizada exitosamente'))
        return super().form_valid(form)


class ProfessionalAreaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ProfessionalArea
    template_name = 'core/del.html'
    context_object_name = 'professionalarea'
    permission_required = 'evaluations.delete_professionalarea'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Área Profesional'
        context['entity'] = 'Áreas Profesionales'
        context['texto'] = f'¿Seguro de eliminar el área profesional "{self.object.name}"?'
        context['list_url'] = 'evaluations:professionalarea_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        area = self.get_object()
        success_message = _(f'Área Profesional eliminada exitosamente')
        
        # Guardar el nombre antes de eliminar
        area_name = area.name
        
        # Realizar la eliminación
        self.object = area
        area.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Obtenemos la URL de éxito
            success_url = reverse_lazy('evaluations:professionalarea_list')
            return JsonResponse({
                'success': True,
                'message': _(f'Área Profesional "{area_name}" eliminada exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('evaluations:professionalarea_list')
    
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


class ProfessionalAreaDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ProfessionalArea
    template_name = 'professionalareas/professionalarea_detail.html'
    context_object_name = 'professionalarea'
    permission_required = 'evaluations.view_professionalarea'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Área Profesional'
        context['entity'] = 'Áreas Profesionales'
        context['list_url'] = 'evaluations:professionalarea_list'
        
        # Obtener competencias relacionadas con esta área profesional
        context['related_competences'] = self.object.competences.all()
        
        # Si hay resultados de evaluación relacionados con esta área profesional
        context['area_results'] = self.object.arearesult_set.all().order_by('-report__generation_date')[:10]
        
        # Recomendaciones asociadas a esta área profesional
        context['recommendations'] = self.object.recommendation_set.all()
        
        return context

class ProfessionalAreaImportView(GenericCSVImportView):
    """
    Vista para importar áreas profesionales desde un archivo CSV.
    """
    model = ProfessionalArea
    success_url = reverse_lazy('evaluations:professionalarea_list')
    permission_required = 'evaluations.add_professionalarea'  # Agregamos permiso explícitamente
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Importar Áreas Profesionales')
        context['entity'] = _('Áreas Profesionales')
        context['list_url'] = self.success_url  # Usamos self.success_url en lugar de string
        return context
    
    
    
class ProfessionalAreaExportView(GenericExportView):
    model = ProfessionalArea
    success_url = reverse_lazy('evaluations:professionalarea_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['export_formats'] = [
            {'format': 'csv', 'label': _('CSV')},
            {'format': 'xlsx', 'label': _('Excel')},
            {'format': 'pdf', 'label': _('PDF')}
        ]
        return context
    