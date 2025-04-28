from django.views.generic.edit import ModelFormMixin
from django.urls import reverse_lazy
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from apps.evaluations.models.evaluationsmodel import Option, Question

class AnswerViewMixin(ModelFormMixin):
    """
    Mixin para compartir funcionalidades comunes entre las vistas
    relacionadas con las respuestas de evaluación.
    """
    
    def get_form(self, form_class=None):
        """
        Personaliza el formulario para añadir clases CSS y atributos adicionales.
        """
        form = super().get_form(form_class)
        
        # Aplicar clases CSS para estilos uniformes
        form.fields['evaluation'].widget.attrs.update({
            'class': 'form-select',
            'id': 'id_evaluation'
        })
        
        form.fields['question'].widget.attrs.update({
            'class': 'form-select',
            'id': 'id_question',
            'onchange': 'loadOptions()'
        })
        
        return form
    
    def get_success_url(self):
        """
        Retorna la URL de redirección después de procesar un formulario válido.
        """
        # Si está en el contexto de una evaluación, volver a su detalle
        if self.object and self.object.evaluation_id:
            return reverse_lazy('evaluations:evaluation_detail', kwargs={'pk': self.object.evaluation_id})
        return reverse_lazy('evaluations:answer_list')
    
    def get_context_data(self, **kwargs):
        """
        Añade datos contextuales comunes para las vistas.
        """
        context = super().get_context_data(**kwargs)
        
        # Configuración para la vista
        context['cancel_url'] = reverse_lazy('evaluations:answer_list')
        
        return context
    
    def ajax_load_options(self, request):
        """
        Método para cargar opciones dinámicamente cuando cambia la pregunta.
        Puede ser utilizado con una URL AJAX.
        """
        question_id = request.GET.get('question_id')
        options = Option.objects.filter(question_id=question_id).order_by('position')
        
        return JsonResponse({
            'options': list(options.values('id', 'text', 'position'))
        })
    
    def form_valid(self, form):
        """
        Validación adicional para asegurarse de que no se dupliquen respuestas
        para una misma pregunta en una evaluación.
        """
        # Comprobar si ya existe una respuesta para esta combinación
        evaluation = form.cleaned_data['evaluation']
        question = form.cleaned_data['question']
        
        # Solo verificar si es una nueva respuesta (no en actualización)
        if not self.object or not self.object.pk:
            from apps.evaluations.models.evaluationsmodel import Answer
            existing = Answer.objects.filter(
                evaluation=evaluation,
                question=question
            ).exclude(pk=self.object.pk if self.object else None).exists()
            
            if existing:
                form.add_error(None, "Ya existe una respuesta para esta pregunta en esta evaluación.")
                return self.form_invalid(form)
        
        return super().form_valid(form)