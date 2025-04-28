from django.views.generic.edit import ModelFormMixin
from django.urls import reverse_lazy
from django.db import models
from django.utils import timezone

class ReportViewMixin(ModelFormMixin):
    """
    Mixin para compartir funcionalidades comunes entre las vistas
    relacionadas con los reportes de evaluación.
    """
    
    def get_form(self, form_class=None):
        """
        Personaliza el formulario para añadir clases CSS y atributos adicionales.
        """
        form = super().get_form(form_class)
        
        # Aplicar clases CSS para estilos uniformes
        if 'user' in form.fields:
            form.fields['user'].widget.attrs.update({
                'class': 'form-select'
            })
            
            # Si ya hay una evaluación seleccionada, restringir al usuario de esa evaluación
            if self.kwargs.get('evaluation_id') and not self.object:
                form.fields['user'].widget.attrs['readonly'] = 'readonly'
        
        if 'evaluation' in form.fields:
            form.fields['evaluation'].widget.attrs.update({
                'class': 'form-select'
            })
            
            # Si ya hay una evaluación seleccionada, restringir el campo
            if self.kwargs.get('evaluation_id') and not self.object:
                form.fields['evaluation'].widget.attrs['readonly'] = 'readonly'
        
        form.fields['report_type'].widget.attrs.update({
            'class': 'form-select'
        })
        
        return form
    
    def get_success_url(self):
        """
        Retorna la URL de redirección después de procesar un formulario válido.
        """
        return reverse_lazy('evaluations:report_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """
        Añade datos contextuales comunes para las vistas.
        """
        context = super().get_context_data(**kwargs)
        
        # Configuración para la vista
        context['cancel_url'] = reverse_lazy('evaluations:report_list')
        
        return context