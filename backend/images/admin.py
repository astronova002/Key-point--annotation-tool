from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import (
    ImageBatch, 
    Image, 
    UploadBatch, 
    ImageUpload, 
    Annotation
)


@admin.register(ImageBatch)
class ImageBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_name', 
        'status', 
        'total_images', 
        'progress_display',
        'uploaded_by', 
        'uploaded_at',
        'yolo_status'
    ]
    list_filter = [
        'status', 
        'uploaded_at', 
        'keypoint_schema',
        'quality_check_passed',
        'processing_priority'
    ]
    search_fields = ['batch_name', 'description', 'uploaded_by__username']
    readonly_fields = [
        'id', 
        'uploaded_at', 
        'progress_display',
        'yolo_processing_info'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'batch_name', 'description', 'uploaded_by')
        }),
        ('Configuration', {
            'fields': ('keypoint_schema', 'total_images', 'processing_priority')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_display', 'quality_check_passed')
        }),
        ('YOLO Processing', {
            'fields': ('yolo_processing_info', 'yolo_model_version', 'avg_yolo_confidence', 'failed_yolo_count'),
            'classes': ('collapse',)
        }),
        ('Quality Control', {
            'fields': ('min_image_quality_score',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('upload_metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'yolo_processing_started', 'yolo_processing_completed'),
            'classes': ('collapse',)
        })
    )
    
    def progress_display(self, obj):
        """Display progress as a visual bar"""
        progress = obj.progress_percentage
        color = 'green' if progress == 100 else 'blue'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            progress, color, int(progress)
        )
    progress_display.short_description = 'Progress'
    
    def yolo_status(self, obj):
        """Show YOLO processing status"""
        if obj.yolo_processing_completed:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.yolo_processing_started:
            return format_html('<span style="color: orange;">⏳ Processing</span>')
        else:
            return format_html('<span style="color: gray;">⏸ Pending</span>')
    yolo_status.short_description = 'YOLO Status'
    
    def yolo_processing_info(self, obj):
        """Display YOLO processing information"""
        info = []
        if obj.yolo_processing_started:
            info.append(f"Started: {obj.yolo_processing_started}")
        if obj.yolo_processing_completed:
            info.append(f"Completed: {obj.yolo_processing_completed}")
        if obj.yolo_model_version:
            info.append(f"Model: {obj.yolo_model_version}")
        if obj.avg_yolo_confidence:
            info.append(f"Avg Confidence: {obj.avg_yolo_confidence}")
        if obj.failed_yolo_count:
            info.append(f"Failed: {obj.failed_yolo_count}")
        return '\n'.join(info) if info else 'No YOLO processing data'
    yolo_processing_info.short_description = 'YOLO Processing Info'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 
        'batch_link', 
        'status', 
        'yolo_confidence',
        'image_quality_score',
        'current_annotator',
        'created_at'
    ]
    list_filter = [
        'status', 
        'batch__status',
        'has_quality_issues',
        'is_difficult_case',
        'requires_specialist_review',
        'created_at'
    ]
    search_fields = [
        'filename', 
        'original_filename', 
        'batch__batch_name',
        'current_annotator__username'
    ]
    readonly_fields = [
        'id', 
        'created_at', 
        'last_status_change',
        'file_info',
        'yolo_info',
        'keypoints_preview'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'batch', 'filename', 'original_filename')
        }),
        ('File Properties', {
            'fields': ('file_info', 'storage_path', 'thumbnail_path')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'current_annotator', 'current_verifier')
        }),
        ('YOLO Results', {
            'fields': ('yolo_info', 'keypoints_preview'),
            'classes': ('collapse',)
        }),
        ('Quality Assessment', {
            'fields': ('image_quality_score', 'has_quality_issues', 'quality_issues'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_difficult_case', 'requires_specialist_review', 'has_annotation_issues'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('infant_metadata', 'acquisition_date', 'source_institution', 'anonymization_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_status_change'),
            'classes': ('collapse',)
        })
    )
    
    def batch_link(self, obj):
        """Link to the batch admin page"""
        url = reverse('admin:images_imagebatch_change', args=[obj.batch.id])
        return format_html('<a href="{}">{}</a>', url, obj.batch.batch_name)
    batch_link.short_description = 'Batch'
    
    def file_info(self, obj):
        """Display file information"""
        return f"{obj.width}x{obj.height} | {obj.file_size} bytes | {obj.mime_type}"
    file_info.short_description = 'File Info'
    
    def yolo_info(self, obj):
        """Display YOLO processing information"""
        info = []
        if obj.yolo_confidence:
            info.append(f"Confidence: {obj.yolo_confidence}")
        if obj.yolo_processing_time_ms:
            info.append(f"Processing Time: {obj.yolo_processing_time_ms}ms")
        if obj.yolo_model_version:
            info.append(f"Model: {obj.yolo_model_version}")
        return '\n'.join(info) if info else 'No YOLO data'
    yolo_info.short_description = 'YOLO Info'
    
    def keypoints_preview(self, obj):
        """Preview keypoints data"""
        if obj.yolo_keypoints:
            try:
                keypoints = obj.yolo_keypoints
                if isinstance(keypoints, str):
                    keypoints = json.loads(keypoints)
                return f"Keypoints: {len(keypoints)} detected"
            except:
                return "Invalid keypoints data"
        return "No keypoints data"
    keypoints_preview.short_description = 'Keypoints'


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 
        'user', 
        'status', 
        'progress_display',
        'created_at',
        'files_summary'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'id']
    readonly_fields = [
        'id', 
        'created_at', 
        'completed_at',
        'progress_display',
        'metadata_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'status')
        }),
        ('File Counts', {
            'fields': ('total_files', 'uploaded_files', 'processed_files', 'failed_files')
        }),
        ('Progress', {
            'fields': ('progress_display',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        })
    )
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def progress_display(self, obj):
        """Display progress information"""
        if obj.total_files == 0:
            return "No files"
        
        progress = (obj.processed_files / obj.total_files) * 100
        color = 'green' if progress == 100 else 'blue'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px;"></div></div>'
            '<small>{}/{} processed</small>',
            progress, color, obj.processed_files, obj.total_files
        )
    progress_display.short_description = 'Progress'
    
    def files_summary(self, obj):
        """Summary of file processing"""
        return f"{obj.processed_files}/{obj.total_files} processed, {obj.failed_files} failed"
    files_summary.short_description = 'Files Summary'
    
    def metadata_display(self, obj):
        """Display metadata in readable format"""
        if obj.metadata:
            try:
                return json.dumps(obj.metadata, indent=2)
            except:
                return str(obj.metadata)
        return "No metadata"
    metadata_display.short_description = 'Metadata'


@admin.register(ImageUpload)
class ImageUploadAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 
        'batch_link',
        'status', 
        'keypoints_count',
        'avg_keypoint_confidence',
        'yolo_model_version',
        'uploaded_at'
    ]
    list_filter = [
        'status', 
        'yolo_model_version',
        'uploaded_at',
        'batch__status'
    ]
    search_fields = [
        'original_filename', 
        'file_id',
        'batch__id'
    ]
    readonly_fields = [
        'id', 
        'uploaded_at', 
        'processed_at',
        'file_info',
        'yolo_summary',
        'keypoints_details'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'batch', 'file_id', 'original_filename')
        }),
        ('File Properties', {
            'fields': ('file_info', 'file_path')
        }),
        ('Processing Status', {
            'fields': ('status', 'processing_time', 'error_message')
        }),
        ('YOLO Results', {
            'fields': ('yolo_summary', 'keypoints_details'),
            'classes': ('collapse',)
        }),
        ('Legacy Annotations', {
            'fields': ('annotations',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
    
    def batch_link(self, obj):
        """Link to the batch admin page"""
        url = reverse('admin:images_uploadbatch_change', args=[obj.batch.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.batch.id)[:8] + '...')
    batch_link.short_description = 'Batch'
    
    def file_info(self, obj):
        """Display file information"""
        return f"Size: {obj.file_size} bytes | Type: {obj.mime_type}"
    file_info.short_description = 'File Info'
    
    def yolo_summary(self, obj):
        """Display YOLO processing summary"""
        info = []
        info.append(f"Model: {obj.yolo_model_version}")
        info.append(f"Keypoints: {obj.keypoints_count}")
        if obj.avg_keypoint_confidence:
            info.append(f"Avg Confidence: {obj.avg_keypoint_confidence}")
        if obj.yolo_processing_time_ms:
            info.append(f"Processing Time: {obj.yolo_processing_time_ms}ms")
        return '\n'.join(info)
    yolo_summary.short_description = 'YOLO Summary'
    
    def keypoints_details(self, obj):
        """Display detailed keypoints information"""
        if obj.yolo_keypoints:
            try:
                keypoints = obj.yolo_keypoints
                if isinstance(keypoints, str):
                    keypoints = json.loads(keypoints)
                
                details = f"Total keypoints: {len(keypoints)}\n"
                if keypoints:
                    high_conf = sum(1 for kp in keypoints if kp.get('confidence', 0) > 0.5)
                    details += f"High confidence (>0.5): {high_conf}\n"
                    
                    # Show first few keypoints as example
                    details += "\nFirst 3 keypoints:\n"
                    for i, kp in enumerate(keypoints[:3]):
                        details += f"  {i+1}: x={kp.get('x', 0):.1f}, y={kp.get('y', 0):.1f}, conf={kp.get('confidence', 0):.3f}\n"
                
                return details
            except Exception as e:
                return f"Error parsing keypoints: {str(e)}"
        return "No keypoints data"
    keypoints_details.short_description = 'Keypoints Details'


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = [
        'image_link',
        'keypoint_type',
        'label', 
        'coordinates',
        'confidence',
        'visibility',
        'created_at'
    ]
    list_filter = [
        'keypoint_type', 
        'visibility',
        'created_at',
        'image__batch__status'
    ]
    search_fields = [
        'label',
        'keypoint_type',
        'image__original_filename'
    ]
    readonly_fields = [
        'id', 
        'created_at',
        'coordinates',
        'metadata_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'image', 'keypoint_type', 'label')
        }),
        ('Position & Quality', {
            'fields': ('coordinates', 'x_coordinate', 'y_coordinate', 'confidence', 'visibility')
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def image_link(self, obj):
        """Link to the image admin page"""
        url = reverse('admin:images_imageupload_change', args=[obj.image.id])
        return format_html('<a href="{}">{}</a>', url, obj.image.original_filename)
    image_link.short_description = 'Image'
    
    def coordinates(self, obj):
        """Display coordinates"""
        return f"({obj.x_coordinate:.1f}, {obj.y_coordinate:.1f})"
    coordinates.short_description = 'Coordinates'
    
    def metadata_display(self, obj):
        """Display metadata in readable format"""
        if obj.metadata:
            try:
                return json.dumps(obj.metadata, indent=2)
            except:
                return str(obj.metadata)
        return "No metadata"
    metadata_display.short_description = 'Metadata'


# Customize admin site headers
admin.site.site_header = "YOLO Keypoint Annotation System"
admin.site.site_title = "YOLO KPA Admin"
admin.site.index_title = "Database Management"
