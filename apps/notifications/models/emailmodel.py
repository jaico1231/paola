from datetime import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_cryptography.fields import encrypt
from apps.base.models.basemodel import BaseModel

class EmailConfiguration(BaseModel):
    class EmailBackend(models.TextChoices):
        SMTP = 'SMTP', _('SMTP Standard')
        SENDGRID = 'SENDGRID', _('SendGrid API')
        SES = 'SES', _('Amazon SES')
        CONSOLE = 'console', _('Console Debug')
        FILE = 'file', _('File Debug')
    
    class SecurityProtocol(models.TextChoices):
        NONE = 'none', _('None')
        TLS = 'TLS', _('TLS')
        SSL = 'SSL', _('SSL')
        STARTTLS = 'STARTTLS', _('STARTTLS')

    name = models.CharField(
        _("Configuration Name"),
        max_length=100,
        unique=True,
        help_text=_("Descriptive name for this configuration")
    )
    
    backend = models.CharField(
        _("Email Backend"),
        max_length=20,
        choices=EmailBackend.choices,
        default=EmailBackend.SMTP
    )
    
    host = models.CharField(
        _("Server Host"),
        max_length=255,
        blank=True,
        null=True
    )
    
    port = models.PositiveIntegerField(
        _("Port Number"),
        blank=True,
        null=True,
        help_text=_("Default ports: SMTP (25, 587), SSL (465), SendGrid (443)")
    )
    
    username = models.CharField(
        _("Authentication Username"),
        max_length=255,
        blank=True,
        null=True
    )
    
    password = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("For API-based services like SendGrid")
    )
    
    security_protocol = models.CharField(
        _("Security Protocol"),
        max_length=20,
        choices=SecurityProtocol.choices,
        default=SecurityProtocol.TLS
    )
    
    timeout = models.PositiveIntegerField(
        _("Connection Timeout"),
        default=10,
        help_text=_("Timeout in seconds for connection attempts")
    )
    
    from_email = models.EmailField(
        _("Default From Address"),
        max_length=255,
        help_text=_("Format: 'Name <email@example.com>'")
    )
    
    is_active = models.BooleanField(
        _("Active Configuration"),
        default=False,
        help_text=_("Only one configuration can be active at a time")
    )
    
    use_custom_headers = models.BooleanField(
        _("Use Custom Headers"),
        default=False
    )
    
    custom_headers = models.JSONField(
        _("Custom Email Headers"),
        blank=True,
        null=True,
        help_text=_("JSON format for additional headers")
    )
    
    fail_silently = models.BooleanField(
        _("Fail Silently"),
        default=False,
        help_text=_("Set to True to suppress exceptions")
    )
    
    class Meta:
        verbose_name = _("Email Configuration")
        verbose_name_plural = _("Email Configurations")
        ordering = ['-is_active', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_configuration'
            )
        ]

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    
    
    

class SMSConfiguration(BaseModel):
    class SMSBackend(models.TextChoices):
        TWILIO = 'TWILIO', _('Twilio')
        AWS_SNS = 'AWS_SNS', _('AWS SNS')
        PLIVO = 'PLIVO', _('Plivo')
        NEXMO = 'NEXMO', _('Vonage (Nexmo)')
        DEBUG = 'DEBUG', _('Debug Console')
    
    name = models.CharField(
        _("Configuration Name"),
        max_length=100,
        unique=True,
        help_text=_("Descriptive name for this configuration")
    )
    
    backend = models.CharField(
        _("SMS Backend"),
        max_length=20,
        choices=SMSBackend.choices,
        default=SMSBackend.TWILIO
    )
    
    account_sid = encrypt(models.CharField(
        _("Account SID/Key"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    auth_token = encrypt(models.CharField(
        _("Auth Token"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    phone_number = models.CharField(
        _("Sender Phone Number"),
        max_length=20,
        help_text=_("In international format (+1234567890)")
    )
    
    api_key = encrypt(models.CharField(
        _("API Key"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    region = models.CharField(
        _("AWS Region"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Only for AWS SNS (e.g., us-east-1)")
    )
    
    timeout = models.PositiveIntegerField(
        _("Connection Timeout"),
        default=10,
        help_text=_("Timeout in seconds for API requests")
    )
    
    is_active = models.BooleanField(
        _("Active Configuration"),
        default=False,
        help_text=_("Only one SMS configuration can be active")
    )


    class Meta:
        verbose_name = _("SMS Configuration")
        verbose_name_plural = _("SMS Configurations")
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_sms_config'
            )
        ]

    def clean(self):
        super().clean()
        
        if self.backend == self.SMSBackend.TWILIO and not all([self.account_sid, self.auth_token]):
            raise ValidationError({
                'account_sid': _("Twilio requires Account SID and Auth Token"),
                'auth_token': _("Twilio requires Account SID and Auth Token")
            })
            
        if self.backend == self.SMSBackend.AWS_SNS and not all([self.api_key, self.region]):
            raise ValidationError({
                'api_key': _("AWS SNS requires API Key and Region"),
                'region': _("AWS SNS requires API Key and Region")
            })

    def save(self, *args, **kwargs):
        if self.is_active:
            SMSConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def connection_params(self):
        params = {
            'backend': self.backend,
            'account_sid': self.account_sid,
            'auth_token': self.auth_token,
            'phone_number': self.phone_number,
            'api_key': self.api_key,
            'region': self.region,
            'timeout': self.timeout
        }
        return {k: v for k, v in params.items() if v}

class WhatsAppConfiguration(BaseModel):
    class WhatsAppBackend(models.TextChoices):
        TWILIO = 'TWILIO', _('Twilio')
        META = 'META', _('Meta Business')
        DEBUG = 'DEBUG', _('Debug Console')
    
    name = models.CharField(
        _("Configuration Name"),
        max_length=100,
        unique=True
    )
    
    backend = models.CharField(
        _("WhatsApp Backend"),
        max_length=20,
        choices=WhatsAppBackend.choices,
        default=WhatsAppBackend.TWILIO
    )
    
    account_sid = encrypt(models.CharField(
        _("Account SID"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    auth_token = encrypt(models.CharField(
        _("Auth Token"),
        max_length=255,
        blank=True,
        null=True
    ))
    
    whatsapp_number = models.CharField(
        _("WhatsApp Business Number"),
        max_length=20,
        help_text=_("In international format (+1234567890)")
    )
    
    business_id = models.CharField(
        _("Business ID"),
        max_length=255,
        blank=True,
        null=True
    )
    
    api_version = models.CharField(
        _("API Version"),
        max_length=10,
        default='v1',
        help_text=_("Meta API version (e.g., v15.0)")
    )
    
    timeout = models.PositiveIntegerField(
        _("Connection Timeout"),
        default=15
    )
    
    is_active = models.BooleanField(
        _("Active Configuration"),
        default=False
    )


    class Meta:
        verbose_name = _("WhatsApp Configuration")
        verbose_name_plural = _("WhatsApp Configurations")
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_whatsapp_config'
            )
        ]

    def clean(self):
        super().clean()
        
        if self.backend == self.WhatsAppBackend.TWILIO and not all([self.account_sid, self.auth_token]):
            raise ValidationError({
                'account_sid': _("Required for Twilio"),
                'auth_token': _("Required for Twilio")
            })
            
        if self.backend == self.WhatsAppBackend.META and not self.business_id:
            raise ValidationError({
                'business_id': _("Meta Business ID is required")
            })

    def save(self, *args, **kwargs):
        if self.is_active:
            WhatsAppConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def connection_params(self):
        params = {
            'backend': self.backend,
            'account_sid': self.account_sid,
            'auth_token': self.auth_token,
            'whatsapp_number': self.whatsapp_number,
            'business_id': self.business_id,
            'api_version': self.api_version,
            'timeout': self.timeout
        }
        return {k: v for k, v in params.items() if v}

    
class MessageLog(BaseModel):
    """Model to track all messages sent through the system"""
    
    class MessageType(models.TextChoices):
        EMAIL = 'EMAIL', _('Email')
        SMS = 'SMS', _('SMS')
        WHATSAPP = 'WHATSAPP', _('WhatsApp')
    
    class MessageStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        DELIVERED = 'DELIVERED', _('Delivered')
        READ = 'READ', _('Read')
        FAILED = 'FAILED', _('Failed')
    
    message_type = models.CharField(
        _("Message Type"),
        max_length=10,
        choices=MessageType.choices
    )
    
    sender = models.CharField(
        _("Sender"),
        max_length=255,
        help_text=_("Email address or phone number of sender")
    )
    
    recipient = models.CharField(
        _("Recipient"),
        max_length=255,
        help_text=_("Email address or phone number of recipient")
    )
    
    cc = models.TextField(
        _("CC Recipients"),
        blank=True,
        null=True,
        help_text=_("Comma-separated list of CC recipients (for emails)")
    )
    
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Email subject or message title")
    )
    
    message = models.TextField(
        _("Message Content"),
        help_text=_("Content of the message")
    )
    
    template_name = models.CharField(
        _("Template Name"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Name of template used, if any")
    )
    
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING
    )
    
    sent_at = models.DateTimeField(
        _("Sent Time"),
        blank=True,
        null=True
    )
    
    delivered_at = models.DateTimeField(
        _("Delivery Time"),
        blank=True,
        null=True
    )
    
    read_at = models.DateTimeField(
        _("Read Time"),
        blank=True,
        null=True
    )
    
    provider = models.CharField(
        _("Provider"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Service provider used (Twilio, SendGrid, etc.)")
    )
    
    provider_message_id = models.CharField(
        _("Provider Message ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Message ID returned by the provider")
    )
    
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        null=True,
        help_text=_("Error message if sending failed")
    )
    
    retries = models.PositiveSmallIntegerField(
        _("Retry Count"),
        default=0
    )
    
    metadata = models.JSONField(
        _("Additional Metadata"),
        blank=True,
        null=True,
        help_text=_("Any additional data related to the message")
    )
    
    class Meta:
        verbose_name = _("Message Log")
        verbose_name_plural = _("Message Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['recipient']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['provider_message_id']),
        ]
    
    def __str__(self):
        return f"{self.message_type} to {self.recipient} ({self.status})"
    
    def update_status(self, status, provider_data=None):
        """Update message status and related fields"""
        self.status = status
        
        # Update timestamps based on status
        now = timezone.now()
        
        if status == self.MessageStatus.SENT and not self.sent_at:
            self.sent_at = now
        elif status == self.MessageStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = now
        elif status == self.MessageStatus.READ and not self.read_at:
            self.read_at = now
        
        # Update provider data if provided
        if provider_data:
            if 'message_id' in provider_data:
                self.provider_message_id = provider_data['message_id']
            if 'error' in provider_data:
                self.error_message = provider_data['error']
            
            # Save any additional metadata
            if not self.metadata:
                self.metadata = {}
            
            self.metadata.update({
                f"update_{now.isoformat()}": provider_data
            })
        
        self.save()
        return self


class ScheduledMessage(BaseModel):
    """Model for scheduling messages to be sent later"""
    
    message_log = models.OneToOneField(
        MessageLog,
        on_delete=models.CASCADE,
        related_name='schedule',
        help_text=_("Associated message log entry")
    )
    
    scheduled_time = models.DateTimeField(
        _("Scheduled Time"),
        help_text=_("When the message should be sent")
    )
    
    recurring = models.BooleanField(
        _("Recurring Message"),
        default=False
    )
    
    recurrence_pattern = models.JSONField(
        _("Recurrence Pattern"),
        blank=True,
        null=True,
        help_text=_("JSON defining recurrence rules")
    )
    
    processed = models.BooleanField(
        _("Processed"),
        default=False,
        help_text=_("Whether this scheduled message has been processed")
    )
    
    canceled = models.BooleanField(
        _("Canceled"),
        default=False
    )
    
    last_run = models.DateTimeField(
        _("Last Run Time"),
        blank=True,
        null=True
    )
    
    next_run = models.DateTimeField(
        _("Next Run Time"),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _("Scheduled Message")
        verbose_name_plural = _("Scheduled Messages")
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['processed']),
            models.Index(fields=['recurring']),
            models.Index(fields=['next_run']),
        ]
    
    def __str__(self):
        status = "Scheduled"
        if self.processed:
            status = "Sent"
        if self.canceled:
            status = "Canceled"
        
        return f"{self.message_log.message_type} to {self.message_log.recipient} ({status} for {self.scheduled_time})"
    
    def cancel(self):
        """Cancel this scheduled message"""
        self.canceled = True
        self.save()
        return self
    
    def calculate_next_run(self):
        """Calculate next run time based on recurrence pattern"""
        if not self.recurring or not self.recurrence_pattern:
            return None
        
        from dateutil.relativedelta import relativedelta
        
        # Get the last run time or scheduled time if never run
        base_time = self.last_run or self.scheduled_time
        pattern = self.recurrence_pattern
        
        # Calculate next run based on pattern
        if pattern.get('frequency') == 'daily':
            next_time = base_time + relativedelta(days=pattern.get('interval', 1))
        elif pattern.get('frequency') == 'weekly':
            next_time = base_time + relativedelta(weeks=pattern.get('interval', 1))
        elif pattern.get('frequency') == 'monthly':
            next_time = base_time + relativedelta(months=pattern.get('interval', 1))
        elif pattern.get('frequency') == 'yearly':
            next_time = base_time + relativedelta(years=pattern.get('interval', 1))
        else:
            return None
        
        # Update next_run field
        self.next_run = next_time
        self.save(update_fields=['next_run'])
        
        return next_time


class MessageTemplate(BaseModel):
    """Model for storing message templates"""
    
    class TemplateType(models.TextChoices):
        EMAIL = 'EMAIL', _('Email')
        SMS = 'SMS', _('SMS')
        WHATSAPP = 'WHATSAPP', _('WhatsApp')
    
    name = models.CharField(
        _("Template Name"),
        max_length=100,
        unique=True
    )
    
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True
    )
    
    template_type = models.CharField(
        _("Template Type"),
        max_length=10,
        choices=TemplateType.choices
    )
    
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Subject line for email templates")
    )
    
    content = models.TextField(
        _("Template Content"),
        help_text=_("Template content with variable placeholders")
    )
    
    html_content = models.TextField(
        _("HTML Content"),
        blank=True,
        null=True,
        help_text=_("HTML version for email templates")
    )
    
    default_context = models.JSONField(
        _("Default Context"),
        blank=True,
        null=True,
        help_text=_("Default values for template variables")
    )
    
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )
    
    class Meta:
        verbose_name = _("Message Template")
        verbose_name_plural = _("Message Templates")
        ordering = ['name']
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render(self, context=None):
        """
        Render the template with given context
        
        Args:
            context (dict): Context variables for template
            
        Returns:
            dict: With keys 'subject', 'content', 'html_content'
        """
        from django.template import Template, Context
        
        # Merge default context with provided context
        merged_context = self.default_context or {}
        if context:
            merged_context.update(context)
        
        template_context = Context(merged_context)
        
        # Render content
        content_template = Template(self.content)
        rendered_content = content_template.render(template_context)
        
        # Render subject if present
        rendered_subject = None
        if self.subject:
            subject_template = Template(self.subject)
            rendered_subject = subject_template.render(template_context)
        
        # Render HTML content if present
        rendered_html = None
        if self.html_content:
            html_template = Template(self.html_content)
            rendered_html = html_template.render(template_context)
        
        return {
            'subject': rendered_subject,
            'content': rendered_content,
            'html_content': rendered_html
        }

