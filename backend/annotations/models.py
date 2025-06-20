from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class BatchAssignment(models.Model):
    """Task management for batch assignments to annotators"""
    
    ASSIGNMENT_TYPES = [
        ('INITIAL', 'Initial Assignment'),
        ('REVISION', 'Revision Assignment'),
        ('QUALITY_CHECK', 'Quality Check'),
        ('SECOND_OPINION', 'Second Opinion'),
    ]
    
    ASSIGNMENT_STATUS = [
        ('ASSIGNED', 'Assigned'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SUBMITTED', 'Submitted'),
        ('OVERDUE', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        'images.ImageBatch',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    annotator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='batch_assignments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assignments'
    )
    
    # Assignment configuration
    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPES,
        default='INITIAL'
    )
    priority = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1-10, higher = more urgent"
    )
    special_instructions = models.TextField(blank=True, null=True)
    estimated_completion_hours = models.IntegerField(null=True, blank=True)
    
    # Status and progress
    status = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_STATUS,
        default='ASSIGNED'
    )
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    images_completed = models.IntegerField(default=0)
    images_total = models.IntegerField()
    
    # Timing
    assigned_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Performance tracking
    total_time_spent_minutes = models.IntegerField(default=0)
    avg_time_per_image_minutes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    pause_count = models.IntegerField(default=0)
    
    # Quality metrics
    self_reported_difficulty = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 scale"
    )
    completion_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.00), MaxValueValidator(1.00)]
    )
    
    class Meta:
        db_table = 'batch_assignments'
        indexes = [
            models.Index(fields=['annotator', 'status']),
            models.Index(fields=['batch']),
            models.Index(fields=['due_date']),
            models.Index(fields=['assigned_at']),
            models.Index(fields=['priority', 'assigned_at']),
        ]
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"Assignment: {self.batch.batch_name} -> {self.annotator.username}"
    
    def update_progress(self):
        """Update progress based on completed annotations"""
        completed = self.annotations.filter(status='SUBMITTED').count()
        self.images_completed = completed
        if self.images_total > 0:
            self.progress_percentage = (completed / self.images_total) * 100
        self.save(update_fields=['images_completed', 'progress_percentage'])
    
    def is_overdue(self):
        """Check if assignment is overdue"""
        from django.utils import timezone
        return self.due_date and timezone.now() > self.due_date


class Annotation(models.Model):
    """Core annotation entity - refined keypoint data"""
    
    ANNOTATION_STATUS = [
        ('DRAFT', 'Draft'),
        ('COMPLETED', 'Completed'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REVISION_REQUESTED', 'Revision Requested'),
    ]
    
    DIFFICULTY_RATINGS = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
        ('VERY_HARD', 'Very Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(
        'images.Image',
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    batch_assignment = models.ForeignKey(
        BatchAssignment,
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    
    # Keypoint data (Primary output)
    refined_keypoints = models.JSONField(
        help_text="Final annotator coordinates and metadata"
    )
    keypoint_confidence = models.JSONField(
        null=True,
        blank=True,
        help_text="Per-keypoint confidence scores 0-1"
    )
    keypoint_visibility = models.JSONField(
        null=True,
        blank=True,
        help_text="Per-keypoint visibility flags"
    )
    keypoint_notes = models.JSONField(
        null=True,
        blank=True,
        help_text="Per-keypoint specific notes"
    )
    
    # Quality and difficulty assessment
    annotation_quality_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.00), MaxValueValidator(1.00)],
        help_text="Self-assessment 0-1"
    )
    difficulty_rating = models.CharField(
        max_length=10,
        choices=DIFFICULTY_RATINGS,
        null=True,
        blank=True
    )
    difficulty_reasons = models.JSONField(
        null=True,
        blank=True,
        help_text="List of difficulty reasons"
    )
    
    # Technical metadata
    annotation_tool_version = models.CharField(max_length=20, null=True, blank=True)
    total_keypoints_modified = models.IntegerField(
        default=0,
        help_text="Number of keypoints modified from YOLO baseline"
    )
    major_corrections_made = models.BooleanField(default=False)
    used_ai_suggestions = models.BooleanField(default=False)
    
    # Annotator feedback
    general_notes = models.TextField(blank=True, null=True)
    image_quality_feedback = models.TextField(blank=True, null=True)
    suggested_improvements = models.TextField(blank=True, null=True)
    
    # Versioning and revision
    version = models.IntegerField(default=1)
    is_revision = models.BooleanField(default=False)
    original_annotation = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='revisions'
    )
    revision_reason = models.TextField(blank=True, null=True)
    
    # Performance data
    time_spent_seconds = models.IntegerField()
    pause_count = models.IntegerField(default=0)
    zoom_level_used = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True
    )
    
    # Status and timing
    status = models.CharField(
        max_length=20,
        choices=ANNOTATION_STATUS,
        default='DRAFT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'annotations'
        indexes = [
            models.Index(fields=['image']),
            models.Index(fields=['batch_assignment']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['annotation_quality_score']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Annotation: {self.image.filename} - {self.status}"
    
    def get_annotator(self):
        """Get the annotator for this annotation"""
        return self.batch_assignment.annotator
    
    def get_keypoint_count(self):
        """Get total number of keypoints in this annotation"""
        try:
            return len(self.refined_keypoints.get('keypoints', []))
        except (AttributeError, TypeError):
            return 0
