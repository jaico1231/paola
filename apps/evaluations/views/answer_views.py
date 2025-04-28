from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.forms import inlineformset_factory, modelformset_factory
from django import forms

from apps.base.views.genericlistview import OptimizedSecureListView
from apps.evaluations.mixins.answer_mixins import AnswerViewMixin
from apps.evaluations.models.evaluationsmodel import (
    Answer, Evaluation, Question, Option, OptionRanking
)


class AnswerListView(OptimizedSecureListView):
    """
    Vista optimizada para listar respuestas con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'evaluations.view_answer'
    model = Answer
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['evaluation__user__username', 'question__text']
    # Ordenamiento por defecto
    order_by = ('-evaluation__start_date', 'question__text')
    
    # Atributos específicos
    title = _('Listado de Respuestas')
    entity = 'Respuestas'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('evaluation', 'evaluation__user', 'question')
       
        # Filtrar por evaluación
        evaluation_id = self.request.GET.get('evaluation', '')
        if evaluation_id:
            queryset = queryset.filter(evaluation_id=evaluation_id)
            
        # Filtrar por pregunta
        question_id = self.request.GET.get('question', '')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
            
        # Si el usuario no es staff, solo ver sus propias respuestas
        if not self.request.user.is_staff:
            queryset = queryset.filter(evaluation__user=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['USUARIO', 'EVALUACIÓN', 'PREGUNTA', 'OPCIONES']
        context['fields'] = ['evaluation.user.username', 'evaluation.start_date', 'question.text', 'option_rankings.count']
        
        # Configuración de botones y acciones
        if self.request.user.is_staff:
            context['Btn_Add'] = [
                {
                    'name': 'add',
                    'label': 'Crear Respuesta',
                    'icon': 'add',
                    'url': 'evaluations:answer_create',
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
                'url': 'evaluations:answer_detail'
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
                    'url': 'evaluations:answer_update',
                },
                {
                    'name': 'delete',
                    'label': '',
                    'icon': 'delete',
                    'color': 'danger',
                    'color2': 'white',
                    'url': 'evaluations:answer_delete',
                    'modal': True
                }
            ])
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('evaluations:answer_list')
        
        # Filtros adicionales
        context['filters'] = [
            {
                'name': 'evaluation',
                'label': 'Evaluación',
                'options': Evaluation.objects.all().select_related('user'),
                'value_field': 'id',
                'label_field': 'user.username'
            },
            {
                'name': 'question',
                'label': 'Pregunta',
                'options': Question.objects.all(),
                'value_field': 'id',
                'label_field': 'text'
            }
        ]
        
        return context


class OptionRankingForm(forms.ModelForm):
    """Formulario para el ranking de opciones"""
    class Meta:
        model = OptionRanking
        fields = ['option', 'rank']
        widgets = {
            'option': forms.Select(attrs={'class': 'form-select'}),
            'rank': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5})
        }


class AnswerCreateView(LoginRequiredMixin, PermissionRequiredMixin, AnswerViewMixin, CreateView):
    permission_required = 'evaluations.add_answer'
    model = Answer
    template_name = 'answers/answer_form.html'
    fields = ['evaluation', 'question']
    success_url = reverse_lazy('evaluations:answer_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Respuesta')
        context['entity'] = _('Respuestas')
        context['list_url'] = 'evaluations:answer_list'
        context['action'] = 'add'
        
        # Inicializar el formset para opciones de ranking
        if self.request.POST:
            question_id = self.request.POST.get('question', None)
            if question_id:
                question = get_object_or_404(Question, id=question_id)
                options = Option.objects.filter(question=question)
                
                OptionRankingFormSet = inlineformset_factory(
                    Answer, OptionRanking, form=OptionRankingForm,
                    extra=len(options), can_delete=False
                )
                context['options_formset'] = OptionRankingFormSet(self.request.POST)
                context['options'] = options
        else:
            # Primera carga del formulario
            OptionRankingFormSet = inlineformset_factory(
                Answer, OptionRanking, form=OptionRankingForm,
                extra=0, can_delete=False
            )
            context['options_formset'] = OptionRankingFormSet()
        
        # Obtener evaluaciones y preguntas disponibles
        context['evaluations'] = Evaluation.objects.all().select_related('user')
        context['questions'] = Question.objects.all()
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        options_formset = context['options_formset']
        
        if options_formset.is_valid():
            self.object = form.save()
            
            # Guardar el formset
            options_formset.instance = self.object
            options_formset.save()
            
            messages.success(self.request, _('Respuesta creada exitosamente'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(context)


class AnswerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AnswerViewMixin, UpdateView):
    model = Answer
    template_name = 'answers/answer_form.html'
    fields = ['evaluation', 'question']
    permission_required = 'evaluations.change_answer'
    success_url = reverse_lazy('evaluations:answer_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Actualizar Respuesta')
        context['entity'] = _('Respuestas')
        context['list_url'] = 'evaluations:answer_list'
        context['action'] = 'update'
        
        # Inicializar el formset para opciones de ranking
        OptionRankingFormSet = inlineformset_factory(
            Answer, OptionRanking, form=OptionRankingForm,
            extra=0, can_delete=True
        )
        
        if self.request.POST:
            context['options_formset'] = OptionRankingFormSet(self.request.POST, instance=self.object)
        else:
            # Asegurarse de que exista un formset para cada opción de la pregunta
            options = Option.objects.filter(question=self.object.question)
            existing_rankings = self.object.option_rankings.all()
            existing_option_ids = [r.option_id for r in existing_rankings]
            
            # Crear formset con las opciones ya existentes
            context['options_formset'] = OptionRankingFormSet(instance=self.object)
            
            # Añadir opciones faltantes
            missing_options = options.exclude(id__in=existing_option_ids)
            if missing_options.exists():
                # Esto se puede optimizar para precargar formsets adicionales
                pass
        
        # Obtener evaluaciones y preguntas disponibles
        context['evaluations'] = Evaluation.objects.all().select_related('user')
        context['questions'] = Question.objects.all()
        context['options'] = Option.objects.filter(question=self.object.question)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        options_formset = context['options_formset']
        
        if options_formset.is_valid():
            self.object = form.save()
            
            # Guardar el formset
            options_formset.instance = self.object
            options_formset.save()
            
            messages.success(self.request, _('Respuesta actualizada exitosamente'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(context)


class AnswerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Answer
    template_name = 'core/del.html'
    context_object_name = 'answer'
    permission_required = 'evaluations.delete_answer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Respuesta'
        context['entity'] = 'Respuestas'
        context['texto'] = f'¿Seguro de eliminar la respuesta de {self.object.evaluation.user.username} a la pregunta "{self.object.question.text[:50]}..."?'
        context['list_url'] = 'evaluations:answer_list'
        return context
    
    def delete(self, request, *args, **kwargs):
        answer = self.get_object()
        success_message = _('Respuesta eliminada exitosamente')
        
        # Guardar información antes de eliminar
        username = answer.evaluation.user.username
        question = answer.question.text[:30]
        evaluation_id = answer.evaluation_id
        
        # Realizar la eliminación
        self.object = answer
        answer.delete()
        
        # Respuesta mejorada para AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            success_url = reverse_lazy('evaluations:evaluation_detail', kwargs={'pk': evaluation_id})
            return JsonResponse({
                'success': True,
                'message': _(f'Respuesta de {username} a "{question}..." eliminada exitosamente'),
                'redirect': str(success_url)
            })
        
        # Para solicitudes no-AJAX
        messages.success(request, success_message)
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        evaluation_id = self.object.evaluation_id
        return reverse_lazy('evaluations:evaluation_detail', kwargs={'pk': evaluation_id})


class AnswerDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Answer
    template_name = 'answers/answer_detail.html'
    context_object_name = 'answer'
    permission_required = 'evaluations.view_answer'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'evaluation', 'evaluation__user', 'question', 'question__competence'
        )
        # Si no es staff, solo ver sus propias respuestas
        if not self.request.user.is_staff:
            queryset = queryset.filter(evaluation__user=self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de Respuesta'
        context['entity'] = 'Respuestas'
        context['list_url'] = 'evaluations:answer_list'
        
        # Obtener rankings de opciones para esta respuesta
        context['option_rankings'] = self.object.option_rankings.all().select_related('option').order_by('rank')
        
        return context