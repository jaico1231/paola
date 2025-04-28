from django.urls import path
from apps.base.templatetags.menu_decorador import add_menu_name
from django.contrib.auth.decorators import login_required
from apps.evaluations.views.competence_view import (
    CompetenceCreateView,
    CompetenceDeleteView,
    CompetenceExportView,
    CompetenceImportView,
    CompetenceListView,
    CompetenceUpdateView,
    )
from apps.evaluations.views.question_view import (
    QuestionExportView,
    QuestionImportView,
    QuestionListView,
    QuestionCreateView,
    QuestionUpdateView,
    QuestionDeleteView,
)
from apps.evaluations.views.professionalarea_views import (
    ProfessionalAreaCreateView,
    ProfessionalAreaDeleteView,
    ProfessionalAreaExportView,
    ProfessionalAreaImportView,
    ProfessionalAreaListView,
    ProfessionalAreaUpdateView,
)
from apps.evaluations.views.option_views import (
    OptionListView,
    OptionCreateView,
    OptionUpdateView,
    OptionDeleteView,
)
from apps.evaluations.views.answer_views import (
    AnswerListView,
    AnswerCreateView,
    AnswerUpdateView,
    AnswerDeleteView,
)
from apps.evaluations.views.report_views import (
    ReportListView,
    ReportCreateView,
    ReportUpdateView,
    ReportDeleteView,
)
app_name = 'evaluations'
app_icon = 'question_answer'

urlpatterns = [
    # URLs para el banco de preguntas
    path('questions/', add_menu_name('BANCO DE PREGUNTAS','question_answer')(QuestionListView.as_view()), name='question_list'),
    path('questions/add/', (QuestionCreateView.as_view()), name='question_create'),
    path('questions/update/<int:pk>/', (QuestionUpdateView.as_view()), name='question_update'),
    path('questions/delete/<int:pk>/', (QuestionDeleteView.as_view()), name='question_delete'),
    path('questions/upload/', (QuestionImportView.as_view()), name='question-upload'),
    path('questions/export/', (QuestionExportView.as_view()), name='question-download'),
    # Competence
    path('competences/', add_menu_name('COMPETENCIAS','question_answer')(CompetenceListView.as_view()), name='competence_list'),
    path('competences/add/', (CompetenceCreateView.as_view()), name='competence_create'),
    path('competences/update/<int:pk>/', (CompetenceUpdateView.as_view()), name='competence_update'),
    path('competences/delete/<int:pk>/', (CompetenceDeleteView.as_view()), name='competence_delete'),
    path('competences/export/', (CompetenceExportView.as_view()), name='competence-download'),
    path('competences/import/', (CompetenceImportView.as_view()), name='competence-upload'),
    # URLs para las áreas profesionales
    path('professionalareas/', add_menu_name('AREA PROFECIONAL','question_answer')(ProfessionalAreaListView.as_view()), name='professionalarea_list'),
    path('professionalareas/add/', (ProfessionalAreaCreateView.as_view()), name='professionalarea_create'),
    path('professionalareas/update/<int:pk>/', (ProfessionalAreaUpdateView.as_view()), name='professionalarea_update'),
    path('professionalareas/delete/<int:pk>/', (ProfessionalAreaDeleteView.as_view()), name='professionalarea_delete'),
    path('professionalareas/upload/', (ProfessionalAreaImportView.as_view()), name='professionalarea-upload'),
    path('professionalareas/export/', (ProfessionalAreaExportView.as_view()), name='professionalarea-download'),
    # Options
    path('options/', login_required(add_menu_name('OPCIONES','question_answer')(OptionListView.as_view())), name='option_list'),
    path('options/add/', login_required((OptionCreateView.as_view())), name='option_create'),
    path('options/update/<int:pk>/', login_required((OptionUpdateView.as_view())), name='option_update'),
    path('options/delete/<int:pk>/', login_required((OptionDeleteView.as_view())), name='option_delete'),
    # Answer
    path('answers/', login_required(add_menu_name('RESPUESTAS','question_answer')(AnswerListView.as_view())), name='answer_list'),
    path('answers/add/', login_required((AnswerCreateView.as_view())), name='answer_create'),
    path('answers/update/<int:pk>/', login_required((AnswerUpdateView.as_view())), name='answer_update'),
    path('answers/delete/<int:pk>/', login_required((AnswerDeleteView.as_view())), name='answer_delete'),
    # Reports
    path('reports/', login_required(add_menu_name('REPORTES','question_answer')(ReportListView.as_view())), name='report_list'),
    path('reports/add/', login_required((ReportCreateView.as_view())), name='report_create'),
    path('reports/update/<int:pk>/', login_required((ReportUpdateView.as_view())), name='report_update'),
    path('reports/delete/<int:pk>/', login_required((ReportDeleteView.as_view())), name='report_delete'),


]