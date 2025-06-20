from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        ANNOTATOR = 'ANNOTATOR', 'Annotator'
        VERIFIER = 'VERIFIER', 'Verifier'

    # Basic fields (existing)
    is_approved = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ANNOTATOR
    )
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    
    # New role-specific fields
    max_concurrent_batches = models.IntegerField(
        default=2,
        help_text="Maximum number of batches an annotator can work on simultaneously"
    )
    annotation_specialty = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Specialization area for annotators (e.g., 'upper_body', 'full_body')"
    )
    verification_expertise = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Medical expertise area for verifiers"
    )
    
    # Performance tracking fields
    total_annotations_completed = models.IntegerField(default=0)
    total_verifications_completed = models.IntegerField(default=0)
    avg_annotation_time_minutes = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00
    )
    accuracy_score = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(1.00)]
    )
    
    class Meta:
        db_table = 'auth_user'
        indexes = [
            models.Index(fields=['role', 'is_approved']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def can_annotate(self):
        """Check if user can perform annotations"""
        return self.role in [self.Role.ANNOTATOR, self.Role.ADMIN] and self.is_approved
    
    def can_verify(self):
        """Check if user can perform verifications"""
        return self.role in [self.Role.VERIFIER, self.Role.ADMIN] and self.is_approved
    
    def can_admin(self):
        """Check if user has admin privileges"""
        return self.role == self.Role.ADMIN and self.is_approved