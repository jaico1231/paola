# payments/models.py
from django.db import models
from django.conf import settings

from apps.base.models.basemodel import BaseModel

class Plan(BaseModel):
    """Plan model for subscription levels"""
    TYPES = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
    )
    
    name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=10, choices=TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    duration_days = models.IntegerField(default=30)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

class Payment(BaseModel):
    """Payment model for tracking user payments"""
    STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    
    def __str__(self):
        return f"Payment by {self.user.username} - {self.plan.name}"
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"