from django.views.generic.edit import ModelFormMixin
from django.urls import reverse_lazy
from django.db import models
from django.utils import timezone

class EvaluationViewMixin(ModelFormMixin):
    """
    Mixin para compartir funcionalidades comunes entre las vistas
    relacionadas con las evaluaciones.
    """
    
    def get_form(self, form_class=None):
        """
        Personaliza el formulario para añadir clases CSS y atributos adicionales.
        """
        form = super().get_form(form_class)
        
        # Aplicar clases CSS para estilos uniformes
        form.fields['user'].widget.attrs.update({
            'class': 'form-select'
        })
        
        form.fields['status'].widget.attrs.update({
            'class': 'form-select'
        })
        
        # Si estamos en modo edición y el campo end_date está presente
        if 'end_date' in form.fields:
            form.fields['end_date'].widget.attrs.update({
                'class': 'form-control',
                'type': 'datetime-local'
            })
            # Si la instancia tiene un valor, formatearla para el campo datetime-local
            if self.object and self.object.end_date:
                # Formato requerido por input datetime-local: YYYY-MM-DDThh:mm
                form.fields['end_date'].initial = self.object.end_date.strftime('%Y-%m-%dT%H:%M')
        
        # Adaptación para usuarios no staff (solo pueden crear para sí mismos)
        if not self.request.user.is_staff:
            form.fields['user'].initial = self.request.user
            form.fields['user'].widget.attrs['disabled'] = 'disabled'
            form.fields['user'].required = False  # Para que el form sea válido aunque el campo esté disabled
        
        return form
    
    def form_valid(self, form):
        """
        Procesa el formulario antes de guardarlo.
        """
        # Si el usuario no es staff, asignar el usuario actual
        if not self.request.user.is_staff:
            form.instance.user = self.request.user
        
        # Si se marca como completado, añadir fecha de finalización
        if form.instance.status == 'completed' and not form.instance.end_date:
            form.instance.end_date = timezone.now()
            
        return super().form_valid(form)
    
    def get_success_url(self):
        """
        Retorna la URL de redirección después de procesar un formulario válido.
        """
        return reverse_lazy('evaluations:evaluation_list')
    
    def get_context_data(self, **kwargs):
        """
        Añade datos contextuales comunes para las vistas.
        """
        context = super().get_context_data(**kwargs)
        
        # Configuración para la vista
        context['cancel_url'] = reverse_lazy('evaluations:evaluation_list')
        
        return context