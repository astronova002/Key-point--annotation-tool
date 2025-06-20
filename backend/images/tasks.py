from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import ImageUpload, UploadBatch, Annotation
from .yolo_processor import YOLOProcessor
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import time

logger = logging.getLogger(__name__)

def process_image_with_yolo_sync(image_id):
    """Synchronous version of image processing with 26-keypoint support"""
    try:
        image_upload = ImageUpload.objects.get(id=image_id)
        batch = image_upload.batch
        
        # Update status
        image_upload.status = 'processing'
        image_upload.save()
        
        # Send WebSocket update
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"upload_batch_{batch.id}",
                {
                    "type": "processing_progress",
                    "file_id": image_upload.file_id,
                    "progress": 0,
                    "status": "processing"
                }
            )
        except Exception as ws_error:
            logger.warning(f"WebSocket update failed: {ws_error}")
        
        # Initialize YOLO processor with 26-keypoint support
        processor = YOLOProcessor(use_26_keypoints=True)
        
        # Process image
        start_time = time.time()
        results = processor.process_image(image_upload.file_path)
        processing_time = time.time() - start_time
        processing_time_ms = int(processing_time * 1000)
        
        # Separate keypoints and other annotations
        keypoints = [r for r in results if r['type'] == 'keypoint']
        other_annotations = [r for r in results if r['type'] != 'keypoint']
        
        # Calculate statistics
        avg_confidence = sum(kp['confidence'] for kp in keypoints) / len(keypoints) if keypoints else 0
        
        # Save both legacy and enhanced formats for backward compatibility
        legacy_annotations = []
        for detection in results:
            # Create legacy annotation record
            annotation = Annotation.objects.create(
                image=image_upload,
                keypoint_type=detection['type'],
                x_coordinate=detection['x'],
                y_coordinate=detection['y'],
                confidence=detection['confidence'],
                label=detection['label'],
                metadata=detection.get('metadata', {})
            )
            legacy_annotations.append({
                'id': str(annotation.id),
                'type': detection['type'],
                'x': detection['x'],
                'y': detection['y'],
                'confidence': detection['confidence'],
                'label': detection['label']
            })
        
        # Update image record with enhanced data
        image_upload.status = 'completed'
        image_upload.annotations = legacy_annotations  # Backward compatibility
        image_upload.yolo_keypoints = results  # New enhanced format
        image_upload.keypoints_count = len(keypoints)
        image_upload.avg_keypoint_confidence = avg_confidence
        image_upload.yolo_model_version = getattr(settings, 'YOLO_MODEL_INFO', {}).get('version', 'best26.pt')
        image_upload.yolo_processing_time_ms = processing_time_ms
        image_upload.processing_time = processing_time  # Legacy field
        image_upload.processed_at = timezone.now()
        image_upload.save()
        
        # Update batch progress
        batch.processed_files += 1
        
        # Check if batch is complete
        if batch.processed_files + batch.failed_files == batch.total_files:
            batch.status = 'completed'
            batch.completed_at = timezone.now()
        
        batch.save()
        
        # Send completion update
        try:
            async_to_sync(channel_layer.group_send)(
                f"upload_batch_{batch.id}",
                {
                    "type": "processing_complete",
                    "file_id": image_upload.file_id,
                    "annotations": legacy_annotations,
                    "keypoints_count": len(keypoints),
                    "avg_confidence": round(avg_confidence, 3),
                    "processing_time": processing_time,
                    "model_version": processor.model_path
                }
            )
        except Exception as ws_error:
            logger.warning(f"WebSocket completion update failed: {ws_error}")
        
        logger.info(f"Successfully processed image {image_id} with {len(keypoints)} keypoints in {processing_time:.2f}s")
        return True
        
    except ImageUpload.DoesNotExist:
        logger.error(f"Image {image_id} not found")
        return False
        
    except Exception as e:
        logger.error(f"Error processing image {image_id}: {str(e)}")
        
        # Update image with error
        try:
            image_upload = ImageUpload.objects.get(id=image_id)
            image_upload.status = 'failed'
            image_upload.error_message = str(e)
            image_upload.save()
            
            # Update batch
            batch = image_upload.batch
            batch.failed_files += 1
            batch.save()
            
            # Send error update
            try:
                async_to_sync(channel_layer.group_send)(
                    f"upload_batch_{batch.id}",
                    {
                        "type": "processing_error",
                        "file_id": image_upload.file_id,
                        "error": str(e)
                    }
                )
            except Exception as ws_error:
                logger.warning(f"WebSocket error update failed: {ws_error}")
            
        except Exception as inner_e:
            logger.error(f"Error updating failed image {image_id}: {str(inner_e)}")
        
        return False

@shared_task(bind=True, max_retries=3)
def process_image_with_yolo(self, image_id):
    """Enhanced image processing with 26-keypoint support (Celery version)"""
    try:
        image_upload = ImageUpload.objects.get(id=image_id)
        batch = image_upload.batch
        
        # Update status
        image_upload.status = 'processing'
        image_upload.save()
        
        # Send WebSocket update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"upload_batch_{batch.id}",
            {
                "type": "processing_progress",
                "file_id": image_upload.file_id,
                "progress": 0,
                "status": "processing"
            }
        )
        
        # Initialize YOLO processor with 26-keypoint support
        processor = YOLOProcessor(use_26_keypoints=True)
        
        # Process image
        start_time = time.time()
        results = processor.process_image(image_upload.file_path)
        processing_time = time.time() - start_time
        processing_time_ms = int(processing_time * 1000)
        
        # Separate keypoints and other annotations
        keypoints = [r for r in results if r['type'] == 'keypoint']
        other_annotations = [r for r in results if r['type'] != 'keypoint']
        
        # Calculate statistics
        avg_confidence = sum(kp['confidence'] for kp in keypoints) / len(keypoints) if keypoints else 0
        
        # Save both legacy and enhanced formats for backward compatibility
        legacy_annotations = []
        for detection in results:
            # Create legacy annotation record
            annotation = Annotation.objects.create(
                image=image_upload,
                keypoint_type=detection['type'],
                x_coordinate=detection['x'],
                y_coordinate=detection['y'],
                confidence=detection['confidence'],
                label=detection['label'],
                metadata=detection.get('metadata', {})
            )
            legacy_annotations.append({
                'id': str(annotation.id),
                'type': detection['type'],
                'x': detection['x'],
                'y': detection['y'],
                'confidence': detection['confidence'],
                'label': detection['label']
            })
        
        # Update image record with enhanced data
        image_upload.status = 'completed'
        image_upload.annotations = legacy_annotations  # Backward compatibility
        image_upload.yolo_keypoints = results  # New enhanced format
        image_upload.keypoints_count = len(keypoints)
        image_upload.avg_keypoint_confidence = avg_confidence
        image_upload.yolo_model_version = getattr(settings, 'YOLO_MODEL_INFO', {}).get('version', 'best26.pt')
        image_upload.yolo_processing_time_ms = processing_time_ms
        image_upload.processing_time = processing_time  # Legacy field
        image_upload.processed_at = timezone.now()
        image_upload.save()
        
        # Update batch progress
        batch.processed_files += 1
        
        # Check if batch is complete
        if batch.processed_files + batch.failed_files == batch.total_files:
            batch.status = 'completed'
            batch.completed_at = timezone.now()
        
        batch.save()
        
        # Send completion update
        async_to_sync(channel_layer.group_send)(
            f"upload_batch_{batch.id}",
            {
                "type": "processing_complete",
                "file_id": image_upload.file_id,
                "annotations": legacy_annotations,
                "keypoints_count": len(keypoints),
                "avg_confidence": round(avg_confidence, 3),
                "processing_time": processing_time,
                "model_version": processor.model_path
            }
        )
        
        logger.info(f"Successfully processed image {image_id} with {len(keypoints)} keypoints in {processing_time:.2f}s")
        
    except ImageUpload.DoesNotExist:
        logger.error(f"Image {image_id} not found")
        
    except Exception as e:
        logger.error(f"Error processing image {image_id}: {str(e)}")
        
        # Update image with error
        try:
            image_upload = ImageUpload.objects.get(id=image_id)
            image_upload.status = 'failed'
            image_upload.error_message = str(e)
            image_upload.save()
            
            # Update batch
            batch = image_upload.batch
            batch.failed_files += 1
            batch.save()
            
            # Send error update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"upload_batch_{batch.id}",
                {
                    "type": "processing_error",
                    "file_id": image_upload.file_id,
                    "error": str(e)
                }
            )
            
        except Exception as inner_e:
            logger.error(f"Error updating failed image {image_id}: {str(inner_e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))