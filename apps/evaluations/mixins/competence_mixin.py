from django.views.generic.edit import ModelFormMixin
from django.urls import reverse_lazy
from django.db import models

class CompetenceViewMixin(ModelFormMixin):
    """
    Mixin para compartir funcionalidades comunes entre las vistas
    relacionadas con las competencias del test vocacional.
    """
    
    def get_form(self, form_class=None):
        """
        Personaliza el formulario para añadir clases CSS y atributos adicionales.
        """
        form = super().get_form(form_class)
        
        # Aplicar clases CSS para estilos uniformes
        form.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre de la competencia'
        })
        
        form.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese una descripción detallada',
            'rows': 3
        })
        
        form.fields['related_areas'].widget.attrs.update({
            'class': 'form-select',
            'multiple': 'multiple'
        })
        
        return form
    
    def get_success_url(self):
        """
        Retorna la URL de redirección después de procesar un formulario válido.
        """
        return reverse_lazy('evaluations:competence_list')
    
    def get_context_data(self, **kwargs):
        """
        Añade datos contextuales comunes para las vistas.
        """
        context = super().get_context_data(**kwargs)
        
        # Configuración para la vista
        context['cancel_url'] = reverse_lazy('evaluations:competence_list')
        
        return context