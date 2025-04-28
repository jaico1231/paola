# evaluation/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.base.models.basemodel import BaseModel

class ProfessionalArea(BaseModel):
    """Professional areas model for vocational tests"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Professional Area"
        verbose_name_plural = "Professional Areas"

class Competence(BaseModel):
    """Competences model for vocational tests"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    related_areas = models.ManyToManyField(ProfessionalArea, related_name='competences')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Competence"
        verbose_name_plural = "Competences"

class Question(BaseModel):
    """Questions for the vocational test"""
    text = models.TextField()
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='questions')
    
    
    def __str__(self):
        return self.text[:50]
    
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"

class Option(BaseModel):
    """Options for each question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    position = models.IntegerField(default=0)  # Position for ordering options
    
    def __str__(self):
        return self.text
    
    class Meta:
        verbose_name = "Option"
        verbose_name_plural = "Options"
        ordering = ['position']

class Evaluation(BaseModel):
    """Evaluation model to track user's test progress"""
    STATUS_CHOICES = (
        ('started', 'Started'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluations')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='started')
    
    def __str__(self):
        return f"Evaluation of {self.user.username} - {self.start_date}"
    
    def complete(self):
        """Mark evaluation as completed"""
        self.status = 'completed'
        self.end_date = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

class Answer(BaseModel):
    """User's answers for each question with ranking of options"""
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Answer of {self.evaluation.user.username} to {self.question.text[:30]}"
    
    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        unique_together = ('evaluation', 'question')

class OptionRanking(BaseModel):
    """Stores the ranking of options for each answer"""
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='option_rankings')
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField(help_text="1 = Most identified with, 5 = Least identified with")
    
    def __str__(self):
        return f"Rank {self.rank} for {self.option.text[:20]}"
    
    class Meta:
        verbose_name = "Option Ranking"
        verbose_name_plural = "Option Rankings"
        unique_together = ('answer', 'option')
        ordering = ['rank']

class Report(BaseModel):
    """Report model for evaluation results"""
    REPORT_TYPES = (
        ('partial', 'Partial'),
        ('complete', 'Complete'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    evaluation = models.OneToOneField(Evaluation, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    generation_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_report_type_display()} Report for {self.user.username}"
    
    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"

class AreaResult(BaseModel):
    """Results by professional area"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='area_results')
    area = models.ForeignKey(ProfessionalArea, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"Result in {self.area.name}: {self.score}%"
    
    class Meta:
        verbose_name = "Area Result"
        verbose_name_plural = "Area Results"

class CompetenceResult(BaseModel):
    """Results by competence"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='competence_results')
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"Competence {self.competence.name}: {self.score}%"
    
    class Meta:
        verbose_name = "Competence Result"
        verbose_name_plural = "Competence Results"

class Recommendation(BaseModel):
    """Recommendations based on evaluation results"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='recommendations')
    area = models.ForeignKey(ProfessionalArea, on_delete=models.CASCADE)
    text = models.TextField()
    priority = models.IntegerField(default=0)  # Higher number = higher priority
    
    def __str__(self):
        return f"Recommendation for {self.area.name}"
    
    class Meta:
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"