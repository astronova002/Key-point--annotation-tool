from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class Verification(models.Model):
    """Quality control entity for annotation verification"""
    
    VERIFICATION_DECISIONS = [
        ('APPROVED', 'Approved'),
        ('APPROVED_WITH_CORRECTIONS', 'Approved with Corrections'),
        ('MINOR_REVISION_NEEDED', 'Minor Revision Needed'),
        ('MAJOR_REVISION_NEEDED', 'Major Revision Needed'),
        ('REJECTED', 'Rejected'),
    ]
    
    REJECTION_REASONS = [
        ('POOR_IMAGE_QUALITY', 'Poor Image Quality'),
        ('INCORRECT_KEYPOINTS', 'Incorrect Keypoints'),
        ('ANATOMICAL_ERRORS', 'Anatomical Errors'),
        ('INCOMPLETE_ANNOTATION', 'Incomplete Annotation'),
        ('TECHNICAL_ISSUES', 'Technical Issues'),
        ('GUIDELINES_VIOLATION', 'Guidelines Violation'),
        ('OTHER', 'Other'),
    ]
    
    CLINICAL_RELEVANCE = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    DIAGNOSTIC_QUALITY = [
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('ADEQUATE', 'Adequate'),
        ('POOR', 'Poor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    annotation = models.OneToOneField(
        'annotations.Annotation',
        on_delete=models.CASCADE,
        related_name='verification'
    )
    verifier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verifications_performed'
    )
    
    # Verification decision
    decision = models.CharField(
        max_length=30,
        choices=VERIFICATION_DECISIONS
    )
    
    # Corrections and feedback
    corrected_keypoints = models.JSONField(
        null=True,
        blank=True,
        help_text="Verifier's corrections to keypoints"
    )
    correction_summary = models.TextField(blank=True, null=True)
    detailed_feedback = models.TextField(blank=True, null=True)
    feedback_to_annotator = models.TextField(
        blank=True,
        null=True,
        help_text="Constructive feedback for annotator improvement"
    )
    internal_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes for admin/research use"
    )
    
    # Quality assessment
    overall_quality_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Overall quality rating 1-10"
    )
    anatomical_accuracy = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    technical_precision = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    completeness_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # Specific quality metrics
    keypoint_accuracy_scores = models.JSONField(
        null=True,
        blank=True,
        help_text="Per-keypoint accuracy assessment"
    )
    problematic_keypoints = models.JSONField(
        null=True,
        blank=True,
        help_text="List of keypoint IDs with issues"
    )
    
    # Rejection handling
    rejection_reason = models.CharField(
        max_length=30,
        choices=REJECTION_REASONS,
        null=True,
        blank=True
    )
    rejection_details = models.TextField(blank=True, null=True)
    can_be_reannotated = models.BooleanField(default=True)
    requires_specialist_input = models.BooleanField(default=False)
    
    # Medical/Clinical assessment
    clinical_relevance = models.CharField(
        max_length=10,
        choices=CLINICAL_RELEVANCE,
        null=True,
        blank=True
    )
    diagnostic_quality = models.CharField(
        max_length=10,
        choices=DIAGNOSTIC_QUALITY,
        null=True,
        blank=True
    )
    research_usability = models.BooleanField(default=True)
    
    # Performance tracking
    verification_time_seconds = models.IntegerField()
    complexity_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How difficult was this to verify (1-5)"
    )
    certainty_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Verifier's confidence in their decision (1-10)"
    )
    
    # Workflow
    is_final_decision = models.BooleanField(default=True)
    requires_second_opinion = models.BooleanField(default=False)
    escalated_to_admin = models.BooleanField(default=False)
    
    # Timing
    verified_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'verifications'
        indexes = [
            models.Index(fields=['annotation']),
            models.Index(fields=['verifier']),
            models.Index(fields=['decision']),
            models.Index(fields=['overall_quality_score']),
            models.Index(fields=['verified_at']),
            models.Index(fields=['requires_second_opinion']),
        ]
        ordering = ['-verified_at']
    
    def __str__(self):
        return f"Verification: {self.annotation.image.filename} - {self.decision}"
    
    def is_approved(self):
        """Check if annotation was approved"""
        return self.decision in ['APPROVED', 'APPROVED_WITH_CORRECTIONS']
    
    def needs_revision(self):
        """Check if annotation needs revision"""
        return self.decision in ['MINOR_REVISION_NEEDED', 'MAJOR_REVISION_NEEDED']
    
    def is_rejected(self):
        """Check if annotation was rejected"""
        return self.decision == 'REJECTED'
