from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()

class ImageBatch(models.Model):
    """Organized batch management for image uploads"""
    
    BATCH_STATUS = [
        ('UPLOADED', 'Uploaded'),
        ('YOLO_PROCESSING', 'YOLO Processing'),
        ('YOLO_COMPLETED', 'YOLO Completed'),
        ('READY_FOR_ANNOTATION', 'Ready for Annotation'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Configuration
    keypoint_schema = models.ForeignKey(
        'ml_models.KeypointSchema',
        on_delete=models.CASCADE,
        related_name='image_batches'
    )
    total_images = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Processing status
    status = models.CharField(
        max_length=30,
        choices=BATCH_STATUS,
        default='UPLOADED'
    )
    
    # YOLO processing metrics
    yolo_processing_started = models.DateTimeField(null=True, blank=True)
    yolo_processing_completed = models.DateTimeField(null=True, blank=True)
    yolo_model_version = models.CharField(max_length=20, null=True, blank=True)
    avg_yolo_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    failed_yolo_count = models.IntegerField(default=0)
    
    # Quality control
    quality_check_passed = models.BooleanField(default=False)
    min_image_quality_score = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=7.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)]
    )
    
    # Metadata
    upload_metadata = models.JSONField(
        default=dict,
        help_text="Source info, session details, etc."
    )
    processing_priority = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1-10, higher = more urgent"
    )
    
    # Ownership and timing
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_batches'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Progress tracking
    assigned_count = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    approved_count = models.IntegerField(default=0)
    rejected_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'image_batches'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['keypoint_schema']),
            models.Index(fields=['processing_priority', 'uploaded_at']),
            models.Index(fields=['uploaded_at']),
        ]
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.batch_name} ({self.total_images} images)"
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        if self.total_images == 0:
            return 0
        return (self.completed_count / self.total_images) * 100
    
    def update_progress(self):
        """Update progress counters based on related images"""
        from .models import Image  # Avoid circular import
        
        images = self.images.all()
        self.assigned_count = images.filter(status__in=['ASSIGNED', 'IN_PROGRESS', 'ANNOTATED', 'SUBMITTED']).count()
        self.completed_count = images.filter(status__in=['APPROVED', 'REJECTED']).count()
        self.approved_count = images.filter(status='APPROVED').count()
        self.rejected_count = images.filter(status='REJECTED').count()
        self.save(update_fields=['assigned_count', 'completed_count', 'approved_count', 'rejected_count'])


class Image(models.Model):
    """Individual image with metadata and processing results"""
    
    IMAGE_STATUS = [
        ('UPLOADED', 'Uploaded'),
        ('YOLO_PROCESSED', 'YOLO Processed'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('ANNOTATED', 'Annotated'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REQUIRES_REVISION', 'Requires Revision'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        ImageBatch,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    # File information
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    storage_path = models.CharField(max_length=500)
    thumbnail_path = models.CharField(max_length=500, null=True, blank=True)
    
    # Image properties
    width = models.IntegerField(validators=[MinValueValidator(1)])
    height = models.IntegerField(validators=[MinValueValidator(1)])
    file_size = models.BigIntegerField(validators=[MinValueValidator(1)])
    mime_type = models.CharField(max_length=50)
    format = models.CharField(max_length=10)  # 'JPEG', 'PNG'
    
    # Medical/Research metadata
    infant_metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Age in months, gender, session type, etc."
    )
    acquisition_date = models.DateField(null=True, blank=True)
    source_institution = models.CharField(max_length=100, null=True, blank=True)
    anonymization_status = models.BooleanField(default=False)
    
    # YOLO processing results
    yolo_keypoints = models.JSONField(
        null=True,
        blank=True,
        help_text="Initial AI detection coordinates"
    )
    yolo_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    yolo_processing_time_ms = models.IntegerField(null=True, blank=True)
    yolo_model_version = models.CharField(max_length=20, null=True, blank=True)
    
    # Quality assessment
    image_quality_score = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)]
    )
    has_quality_issues = models.BooleanField(default=False)
    quality_issues = models.JSONField(
        null=True,
        blank=True,
        help_text="List of quality issues like ['blur', 'poor_lighting', 'occlusion']"
    )
    
    # Workflow status
    status = models.CharField(
        max_length=20,
        choices=IMAGE_STATUS,
        default='UPLOADED'
    )
    
    # Assignment tracking
    current_annotator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_images'
    )
    current_verifier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='images_to_verify'
    )
    
    # Flags
    is_difficult_case = models.BooleanField(default=False)
    requires_specialist_review = models.BooleanField(default=False)
    has_annotation_issues = models.BooleanField(default=False)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    last_status_change = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'images'
        indexes = [
            models.Index(fields=['batch', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['current_annotator']),
            models.Index(fields=['current_verifier']),
            models.Index(fields=['image_quality_score']),
            models.Index(fields=['created_at']),
            models.Index(fields=['yolo_confidence']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.status})"
    
    def can_be_assigned(self):
        """Check if image can be assigned for annotation"""
        return self.status in ['YOLO_PROCESSED', 'REQUIRES_REVISION']
    
    def get_annotation(self):
        """Get the current annotation for this image"""
        return self.annotations.filter(status='SUBMITTED').first()


# Keep existing models for backward compatibility, but they will be replaced
class UploadBatch(models.Model):
    """Legacy model - will be replaced by ImageBatch"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_files = models.IntegerField()
    uploaded_files = models.IntegerField(default=0)
    processed_files = models.IntegerField(default=0)
    failed_files = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),  # Add this line
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'upload_batches'
        ordering = ['-created_at']


class ImageUpload(models.Model):
    """Enhanced legacy model with 26-keypoint support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(UploadBatch, related_name='images', on_delete=models.CASCADE)
    file_id = models.CharField(max_length=100)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    
    status = models.CharField(max_length=20, choices=[
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='uploaded')
    
    # Enhanced annotation storage for 26-keypoint system
    annotations = models.JSONField(null=True, blank=True, help_text="Legacy annotation format")
    yolo_keypoints = models.JSONField(
        null=True, 
        blank=True,
        help_text="YOLO detected 26 keypoints with corrections"
    )
    keypoints_count = models.IntegerField(
        default=0,
        help_text="Number of detected keypoints"
    )
    avg_keypoint_confidence = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Average confidence across all keypoints"
    )
    yolo_model_version = models.CharField(
        max_length=50,
        default="best26.pt",
        help_text="YOLO model version used"
    )
    yolo_processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Processing time in milliseconds"
    )
    
    # Existing fields
    processing_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def get_keypoints_by_type(self, keypoint_type='keypoint'):
        """Get keypoints of specific type from YOLO results"""
        if not self.yolo_keypoints:
            return []
        return [kp for kp in self.yolo_keypoints if kp.get('type') == keypoint_type]
    
    def has_sufficient_keypoints(self, min_confidence=0.3):
        """Check if image has sufficient high-confidence keypoints"""
        keypoints = self.get_keypoints_by_type('keypoint')
        high_conf_keypoints = [kp for kp in keypoints if kp.get('confidence', 0) > min_confidence]
        return len(high_conf_keypoints) >= 15  # At least 15 out of 26 keypoints
    
    def get_keypoint_schema_version(self):
        """Get the keypoint schema version"""
        if self.yolo_keypoints and len(self.get_keypoints_by_type('keypoint')) > 17:
            return "infant_26kp"
        elif self.annotations:
            return "legacy_17kp"
        return None

    class Meta:
        db_table = 'image_uploads'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['batch', 'status']),
            models.Index(fields=['status']),
        ]


class Annotation(models.Model):
    """Legacy model - will be replaced by new annotation system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(ImageUpload, related_name='keypoints', on_delete=models.CASCADE)
    
    keypoint_type = models.CharField(max_length=50)
    x_coordinate = models.FloatField()
    y_coordinate = models.FloatField()
    confidence = models.FloatField()
    visibility = models.BooleanField(default=True)
    
    label = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'legacy_annotations'  # Changed from 'annotations' to 'legacy_annotations'
        ordering = ['keypoint_type', 'label']