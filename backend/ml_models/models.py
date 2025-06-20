from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import json

User = get_user_model()

class KeypointSchema(models.Model):
    """Configurable keypoint schema for different annotation projects"""
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Schema name (e.g., 'infant-pose-17', 'medical-skeleton-25')"
    )
    version = models.CharField(
        max_length=10,
        help_text="Schema version (e.g., 'v1.0', 'v2.1')"
    )
    description = models.TextField(blank=True, null=True)
    
    # Schema definition stored as JSON
    schema_definition = models.JSONField(
        help_text="Complete keypoint schema definition including keypoints, connections, and metadata"
    )
    total_keypoints = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    required_keypoints = models.JSONField(
        null=True, 
        blank=True,
        help_text="List of keypoint IDs that are required for valid annotation"
    )
    
    # Validation rules
    min_visibility_threshold = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    max_missing_keypoints = models.IntegerField(
        default=3,
        validators=[MinValueValidator(0)]
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_schemas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'keypoint_schemas'
        unique_together = ['name', 'version']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} {self.version}"
    
    def get_keypoint_names(self):
        """Extract keypoint names from schema definition"""
        try:
            return [kp['name'] for kp in self.schema_definition.get('keypoints', [])]
        except (KeyError, TypeError):
            return []
    
    def validate_keypoints(self, keypoints_data):
        """Validate keypoint data against this schema"""
        # Implementation for keypoint validation
        pass


class MLModelConfig(models.Model):
    """Configuration for different ML models used in the system"""
    
    MODEL_TYPES = [
        ('YOLO', 'YOLO'),
        ('DETECTRON', 'Detectron2'),
        ('CUSTOM', 'Custom Model'),
    ]
    
    DEPLOYMENT_STATUS = [
        ('DEVELOPMENT', 'Development'),
        ('TESTING', 'Testing'),
        ('PRODUCTION', 'Production'),
        ('DEPRECATED', 'Deprecated'),
    ]
    
    model_name = models.CharField(
        max_length=100,
        help_text="Model name (e.g., 'yolo-v8-pose', 'custom-infant-detector')"
    )
    version = models.CharField(
        max_length=20,
        help_text="Model version (e.g., '1.0', '2.1-beta')"
    )
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_TYPES
    )
    
    # Schema compatibility
    keypoint_schema = models.ForeignKey(
        KeypointSchema,
        on_delete=models.CASCADE,
        related_name='compatible_models'
    )
    supports_confidence_scores = models.BooleanField(default=True)
    supports_visibility_flags = models.BooleanField(default=True)
    
    # Model configuration
    model_parameters = models.JSONField(
        help_text="Model-specific parameters (confidence thresholds, NMS settings, etc.)"
    )
    input_resolution = models.JSONField(
        help_text="Expected input resolution {'width': 640, 'height': 640}"
    )
    preprocessing_config = models.JSONField(
        null=True, 
        blank=True,
        help_text="Preprocessing configuration (normalization, augmentation, etc.)"
    )
    
    # Performance metrics
    avg_processing_time_ms = models.IntegerField(null=True, blank=True)
    avg_confidence_score = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    success_rate = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Deployment information
    model_path = models.CharField(max_length=500, null=True, blank=True)
    api_endpoint = models.URLField(null=True, blank=True)
    deployment_status = models.CharField(
        max_length=20,
        choices=DEPLOYMENT_STATUS,
        default='DEVELOPMENT'
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    training_dataset_info = models.TextField(blank=True, null=True)
    
    # Ownership and timing
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_models'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ml_model_configs'
        unique_together = ['model_name', 'version']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['model_type']),
            models.Index(fields=['keypoint_schema']),
            models.Index(fields=['deployment_status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.model_name} {self.version} ({self.model_type})"
