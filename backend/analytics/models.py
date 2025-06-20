from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class AuditLog(models.Model):
    """Comprehensive activity tracking for all user actions"""
    
    ACTION_CATEGORIES = [
        ('USER_MANAGEMENT', 'User Management'),
        ('IMAGE_PROCESSING', 'Image Processing'),
        ('ANNOTATION', 'Annotation'),
        ('VERIFICATION', 'Verification'),
        ('SYSTEM', 'System'),
    ]
    
    ACTION_STATUS = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User and action info
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(
        max_length=100,
        help_text="Specific action taken (e.g., 'BATCH_CREATED', 'ANNOTATION_SUBMITTED')"
    )
    action_category = models.CharField(
        max_length=20,
        choices=ACTION_CATEGORIES
    )
    
    # Resource information
    resource_type = models.CharField(
        max_length=50,
        help_text="Type of resource affected (e.g., 'Image', 'Annotation', 'Batch')"
    )
    resource_id = models.CharField(max_length=100)
    resource_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Change details
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Previous state of the resource"
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text="New state of the resource"
    )
    change_summary = models.TextField(blank=True, null=True)
    
    # Context information
    session_id = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    api_endpoint = models.CharField(max_length=200, null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    
    # Performance metrics
    action_duration_ms = models.IntegerField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Status and results
    status = models.CharField(
        max_length=20,
        choices=ACTION_STATUS,
        default='SUCCESS'
    )
    error_message = models.TextField(null=True, blank=True)
    warning_messages = models.JSONField(null=True, blank=True)
    
    # Additional context
    batch_context = models.JSONField(
        null=True,
        blank=True,
        help_text="Related batch information"
    )
    annotation_context = models.JSONField(
        null=True,
        blank=True,
        help_text="Related annotation details"
    )
    system_context = models.JSONField(
        null=True,
        blank=True,
        help_text="System state, versions, etc."
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['action_category']),
            models.Index(fields=['status']),
            models.Index(fields=['ip_address']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username}: {self.action} on {self.resource_type}"


class PerformanceMetrics(models.Model):
    """Analytics and reporting for user and system performance"""
    
    PERIOD_TYPES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    
    # Time period
    metrics_date = models.DateField()
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Annotation metrics (for annotators)
    images_annotated = models.IntegerField(default=0)
    annotations_created = models.IntegerField(default=0)
    annotations_revised = models.IntegerField(default=0)
    avg_time_per_annotation_minutes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    total_annotation_time_minutes = models.IntegerField(default=0)
    
    # Verification metrics (for verifiers)
    annotations_verified = models.IntegerField(default=0)
    annotations_approved = models.IntegerField(default=0)
    annotations_rejected = models.IntegerField(default=0)
    avg_verification_time_minutes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    
    # Quality metrics
    accuracy_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(1.00)]
    )
    avg_quality_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    improvement_trend = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text="Week-over-week improvement rate"
    )
    
    # Efficiency metrics
    productivity_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    consistency_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    learning_curve_indicator = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    
    # Detailed statistics
    keypoint_accuracy_breakdown = models.JSONField(
        null=True,
        blank=True,
        help_text="Per-keypoint accuracy statistics"
    )
    difficulty_distribution = models.JSONField(
        null=True,
        blank=True,
        help_text="Distribution of easy/medium/hard cases"
    )
    time_distribution = models.JSONField(
        null=True,
        blank=True,
        help_text="Time spent patterns"
    )
    error_patterns = models.JSONField(
        null=True,
        blank=True,
        help_text="Common mistake types and frequencies"
    )
    
    # Comparative metrics
    peer_comparison_percentile = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    improvement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    
    # System performance (for admins)
    system_uptime_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    avg_processing_time_ms = models.IntegerField(null=True, blank=True)
    error_rate_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Calculation metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculation_version = models.CharField(max_length=10, default='1.0')
    data_completeness = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00,
        help_text="How complete the source data was"
    )
    
    class Meta:
        db_table = 'performance_metrics'
        unique_together = ['user', 'metrics_date', 'period_type']
        indexes = [
            models.Index(fields=['user', 'metrics_date']),
            models.Index(fields=['period_type', 'period_start']),
            models.Index(fields=['accuracy_score']),
            models.Index(fields=['calculated_at']),
        ]
        ordering = ['-metrics_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.period_type} metrics for {self.metrics_date}"
