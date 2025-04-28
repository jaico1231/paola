from django.views.generic.edit import ModelFormMixin
from django.urls import reverse_lazy
from django.db import models

class OptionViewMixin(ModelFormMixin):
    """
    Mixin para compartir funcionalidades comunes entre las vistas
    relacionadas con las opciones de preguntas.
    """
    
    def get_form(self, form_class=None):
        """
        Personaliza el formulario para añadir clases CSS y atributos adicionales.
        """
        form = super().get_form(form_class)
        
        # Aplicar clases CSS para estilos uniformes
        form.fields['text'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el texto de la opción'
        })
        
        form.fields['question'].widget.attrs.update({
            'class': 'form-select'
        })
        
        form.fields['position'].widget.attrs.update({
            'class': 'form-control',
            'min': '0',
            'type': 'number'
        })
        
        # Si hay una pregunta seleccionada desde la URL
        selected_question = self.request.GET.get('question', None)
        if selected_question and not self.object:  # Solo para nueva creación
            form.fields['question'].initial = selected_question
        
        return form
    
    def get_success_url(self):
        """
        Retorna la URL de redirección después de procesar un formulario válido.
        """
        # Redireccionar a la lista filtrada por la pregunta
        if self.object and self.object.question_id:
            return reverse_lazy('evaluations:option_list') + f'?question={self.object.question_id}'
        return reverse_lazy('evaluations:option_list')
    
    def get_context_data(self, **kwargs):
        """
        Añade datos contextuales comunes para las vistas.
        """
        context = super().get_context_data(**kwargs)
        
        # Configuración para la vista
        context['cancel_url'] = reverse_lazy('evaluations:option_list')
        
        return context