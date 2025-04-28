from django.views.generic.edit import ModelFormMixin
from django.urls import reverse_lazy
from django.db import models

class QuestionViewMixin(ModelFormMixin):
    """
    Mixin para compartir funcionalidades comunes entre las vistas
    relacionadas con las preguntas del test vocacional.
    """
    
    def get_form(self, form_class=None):
        """
        Personaliza el formulario para añadir clases CSS y atributos adicionales.
        """
        form = super().get_form(form_class)
        
        # Aplicar clases CSS para estilos uniformes
        form.fields['text'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el texto de la pregunta',
            'rows': 3
        })
        
        form.fields['competence'].widget.attrs.update({
            'class': 'form-select',
        })
        
        return form
    
    def get_success_url(self):
        """
        Retorna la URL de redirección después de procesar un formulario válido.
        """
        return reverse_lazy('vocational:question_list')
    
    def get_context_data(self, **kwargs):
        """
        Añade datos contextuales comunes para las vistas.
        """
        context = super().get_context_data(**kwargs)
        
        # Configuración para la vista
        context['cancel_url'] = reverse_lazy('vocational:question_list')
        
        return context