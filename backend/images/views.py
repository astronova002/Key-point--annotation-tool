from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.conf import settings
import json
import os
import logging
from .models import UploadBatch, ImageUpload
from .tasks import process_image_with_yolo, process_image_with_yolo_sync
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_upload_batch(request):
    """Create a new upload batch"""
    try:
        data = json.loads(request.body)
        total_files = data.get('total_files')
        metadata = data.get('metadata', {})
        
        if not total_files or total_files <= 0:
            return JsonResponse({'error': 'Invalid total_files'}, status=400)
        
        # Create batch
        batch = UploadBatch.objects.create(
            user=request.user,
            total_files=total_files,
            metadata=metadata,
            status='pending'
        )
        
        return JsonResponse({
            'batch_id': str(batch.id),
            'status': 'created'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """Handle individual image upload with better error handling"""
    try:
        batch_id = request.POST.get('batch_id')
        file_id = request.POST.get('file_id')
        uploaded_file = request.FILES.get('file')
        
        # Validation
        if not all([batch_id, file_id, uploaded_file]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # File size validation (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'File too large. Maximum size is 10MB'}, status=400)
        
        # File type validation
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid file type'}, status=400)
        
        # Get batch
        try:
            batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        except UploadBatch.DoesNotExist:
            return JsonResponse({'error': 'Batch not found'}, status=404)
        
        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{batch_id}/{file_id}{file_extension}"
        
        # Save file (will use cloud storage in production)
        file_path = default_storage.save(unique_filename, uploaded_file)
        
        # Create image record
        image_upload = ImageUpload.objects.create(
            batch=batch,
            file_id=file_id,
            original_filename=uploaded_file.name,
            file_path=file_path,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type,
            status='uploaded'
        )
        
        # Update batch progress
        batch.uploaded_files += 1
        if batch.status == 'pending':
            batch.status = 'uploading'
        batch.save()
        
        # Note: YOLO processing is now triggered manually via separate endpoint
        # to give users control over when processing starts
        
        return JsonResponse({
            'image_id': str(image_upload.id),
            'status': 'uploaded',
            'queued_for_processing': False,  # Manual processing now
            'message': 'Image uploaded successfully. Use /process-batch/ to start YOLO processing.'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JsonResponse({'error': 'Upload failed. Please try again.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_batch_status(request, batch_id):
    """Get batch processing status"""
    try:
        batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        
        return JsonResponse({
            'batch_id': str(batch.id),
            'status': batch.status,
            'total_files': batch.total_files,
            'uploaded_files': batch.images.count(),
            'processed_files': batch.filter(),
            'failed_files': batch.failed_files,
            'progress_percent': (batch.processed_files / batch.total_files) * 100,
            'created_at': batch.created_at.isoformat(),
            'completed_at': batch.completed_at.isoformat() if batch.completed_at else None
        })
        
    except UploadBatch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_batch_images(request, batch_id):
    """Get all images in a batch with their annotations"""
    try:
        batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        images = batch.images.all()
        
        images_data = []
        for image in images:
            images_data.append({
                'id': str(image.id),
                'original_filename': image.original_filename,
                'status': image.status,
                'annotations_count': len(image.annotations or []),
                'processing_time': image.processing_time,
                'uploaded_at': image.uploaded_at.isoformat(),
                'processed_at': image.processed_at.isoformat() if image.processed_at else None,
                'error_message': image.error_message
            })
        
        return JsonResponse({
            'batch_id': str(batch.id),
            'images': images_data,
            'total_count': len(images_data)
        })
        
    except UploadBatch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_batch(request, batch_id):
    """Cancel a batch upload/processing"""
    try:
        batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        
        # Only allow cancellation if not completed
        if batch.status in ['completed']:
            return JsonResponse({'error': 'Cannot cancel completed batch'}, status=400)
        
        # Update batch status
        batch.status = 'cancelled'
        batch.save()
        
        # Update any pending images
        pending_images = batch.images.filter(status__in=['uploaded', 'processing'])
        pending_images.update(status='cancelled')
        
        logger.info(f"Batch {batch_id} cancelled by user {request.user.username}")
        
        return JsonResponse({
            'message': 'Batch cancelled successfully',
            'batch_id': str(batch.id)
        })
        
    except UploadBatch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    except Exception as e:
        logger.error(f"Error cancelling batch {batch_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_failed_images(request, batch_id):
    """Retry processing failed images in a batch"""
    try:
        batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        failed_images = batch.images.filter(status='failed')
        
        if not failed_images.exists():
            return JsonResponse({'message': 'No failed images to retry'})
        
        # Reset failed images and requeue for processing
        retry_count = 0
        failed_count = 0
        use_async = getattr(settings, 'PROCESS_IMAGES_ASYNC', False)
        
        for image in failed_images:
            image.status = 'uploaded'
            image.error_message = None
            image.save()
            
            # Process based on async setting
            if use_async:
                # Requeue for YOLO processing
                process_image_with_yolo.delay(str(image.id))
                retry_count += 1
            else:
                # Process synchronously
                try:
                    success = process_image_with_yolo_sync(str(image.id))
                    if success:
                        retry_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error retrying image {image.id}: {str(e)}")
                    image.status = 'failed'
                    image.error_message = str(e)
                    image.save()
                    failed_count += 1
                    continue
        
        # Update batch counters
        batch.failed_files -= retry_count
        batch.save()
        
        logger.info(f"Retrying {retry_count} failed images in batch {batch_id} (failed: {failed_count})")
        
        return JsonResponse({
            'message': f'Retrying {retry_count} failed images (failed: {failed_count})',
            'retry_count': retry_count,
            'failed_count': failed_count,
            'batch_id': str(batch.id)
        })
        
    except UploadBatch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    except Exception as e:
        logger.error(f"Error retrying batch {batch_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_batch_list(request):
    """Get list of user's batches with filtering"""
    try:
        status_filter = request.GET.get('status')
        
        batches = UploadBatch.objects.filter(user=request.user)
        
        if status_filter:
            batches = batches.filter(status=status_filter)
        
        batches_data = []
        for batch in batches.order_by('-created_at'):
            batches_data.append({
                'id': str(batch.id),
                'total_files': batch.total_files,
                'uploaded_files': batch.images.count(),
                'processed_files': batch.processed_files,
                'failed_files': batch.failed_files,
                'status': batch.status,
                'progress_percent': (batch.processed_files / batch.total_files) * 100 if batch.total_files > 0 else 0,
                'created_at': batch.created_at.isoformat(),
                'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                'metadata': batch.metadata
            })
        
        return JsonResponse({
            'batches': batches_data,
            'total_count': len(batches_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting batch list: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_batch_with_yolo(request, batch_id):
    """Manually trigger YOLO processing for an entire batch"""
    try:
        batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        
        # Check if batch is in a valid status for processing
        if batch.status not in ['uploading', 'completed', 'failed']:
            return JsonResponse({
                'error': f'Cannot process batch with status: {batch.status}'
            }, status=400)
        
        # Get images that need processing (uploaded or failed status)
        processable_images = batch.images.filter(status__in=['uploaded', 'failed'])
        
        if not processable_images.exists():
            return JsonResponse({
                'message': 'No images to process in this batch',
                'batch_id': str(batch.id)
            })
        
        # Update batch status
        batch.status = 'processing'
        batch.save()
        
        # Process images based on async setting
        processed_count = 0
        failed_count = 0
        use_async = getattr(settings, 'PROCESS_IMAGES_ASYNC', False)
        
        for image in processable_images:
            # Reset error state if retrying failed images
            if image.status == 'failed':
                image.error_message = None
                batch.failed_files = max(0, batch.failed_files - 1)
            
            image.status = 'uploaded'  # Reset to uploaded for processing
            image.save()
            
            # Process image based on async setting
            if use_async:
                # Use Celery for async processing
                process_image_with_yolo.delay(str(image.id))
                processed_count += 1
            else:
                # Use synchronous processing
                try:
                    success = process_image_with_yolo_sync(str(image.id))
                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error processing image {image.id}: {str(e)}")
                    image.status = 'failed'
                    image.error_message = str(e)
                    image.save()
                    batch.failed_files += 1
                    failed_count += 1
        
        # Update batch counters and check completion
        batch.save()
        
        # For synchronous processing, check if batch is complete
        if not use_async and batch.processed_files + batch.failed_files >= batch.uploaded_files:
            batch.status = 'completed'
            batch.completed_at = timezone.now()
            batch.save()
            logger.info(f"Batch {batch_id} marked as completed after sync processing")
        
        if use_async:
            logger.info(f"Queued {processed_count} images for YOLO processing in batch {batch_id}")
            message = f"Started YOLO processing for {processed_count} images"
            status = 'processing_started'
        else:
            logger.info(f"Processed {processed_count} images synchronously in batch {batch_id} (failed: {failed_count})")
            message = f"Completed YOLO processing for {processed_count} images (failed: {failed_count})"
            status = 'processing_completed'
        
        return JsonResponse({
            'message': message,
            'batch_id': str(batch.id),
            'processing_count': processed_count,
            'failed_count': failed_count,
            'status': status
        })
        
    except UploadBatch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    except Exception as e:
        logger.error(f"Error starting YOLO processing for batch {batch_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_yolo_model_info(request):
    """Get information about the current YOLO model"""
    try:
        model_info = getattr(settings, 'YOLO_MODEL_INFO', {})
        model_path = getattr(settings, 'YOLO_MODEL_PATH', '')
        
        # Check if model file exists
        model_exists = os.path.exists(model_path) if model_path else False
        
        return JsonResponse({
            'model_info': model_info,
            'model_path': model_path,
            'model_exists': model_exists,
            'confidence_threshold': getattr(settings, 'YOLO_CONFIDENCE_THRESHOLD', 0.3),
            'processing_enabled': getattr(settings, 'ENABLE_YOLO_PROCESSING', True)
        })
        
    except Exception as e:
        logger.error(f"Error getting YOLO model info: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_single_image(request, image_id):
    """Manually trigger YOLO processing for a single image"""
    try:
        # Get the image and verify ownership through batch
        image = ImageUpload.objects.select_related('batch').get(
            id=image_id, 
            batch__user=request.user
        )
        
        # Check if image can be processed
        if image.status not in ['uploaded', 'failed']:
            return JsonResponse({
                'error': f'Cannot process image with status: {image.status}'
            }, status=400)
        
        # Reset any previous error state
        if image.status == 'failed':
            image.error_message = None
            batch = image.batch
            batch.failed_files = max(0, batch.failed_files - 1)
            batch.save()
        
        # Update image status and queue for processing
        image.status = 'uploaded'
        image.save()
        
        # Process image based on async setting
        use_async = getattr(settings, 'PROCESS_IMAGES_ASYNC', False)
        
        if use_async:
            # Use Celery for async processing
            process_image_with_yolo.delay(str(image.id))
            logger.info(f"Queued single image {image_id} for YOLO processing")
            message = 'Image queued for YOLO processing'
            status = 'processing_started'
        else:
            # Use synchronous processing
            try:
                success = process_image_with_yolo_sync(str(image.id))
                if success:
                    logger.info(f"Processed single image {image_id} synchronously")
                    message = 'Image processed successfully'
                    status = 'processing_completed'
                else:
                    logger.error(f"Failed to process image {image_id}")
                    return JsonResponse({'error': 'Image processing failed'}, status=500)
            except Exception as e:
                logger.error(f"Error processing image {image_id}: {str(e)}")
                image.status = 'failed'
                image.error_message = str(e)
                image.save()
                return JsonResponse({'error': str(e)}, status=500)
        
        return JsonResponse({
            'message': message,
            'image_id': str(image.id),
            'batch_id': str(image.batch.id),
            'status': status
        })
        
    except ImageUpload.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        logger.error(f"Error processing single image {image_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_batch(request, batch_id):
    """Delete a batch and all its associated files and data"""
    try:
        batch = UploadBatch.objects.get(id=batch_id, user=request.user)
        
        # Get all images in the batch
        images = batch.images.all()
        
        # Delete physical files from storage
        deleted_files_count = 0
        for image in images:
            try:
                # Delete the file from storage
                if default_storage.exists(image.file_path):
                    default_storage.delete(image.file_path)
                    deleted_files_count += 1
                    logger.info(f"Deleted file: {image.file_path}")
            except Exception as file_error:
                logger.warning(f"Could not delete file {image.file_path}: {str(file_error)}")
        
        # Delete all related annotations
        annotation_count = 0
        for image in images:
            # Delete legacy annotations
            legacy_annotations = image.keypoints.all()
            annotation_count += legacy_annotations.count()
            legacy_annotations.delete()
        
        # Delete all images (this will cascade to annotations)
        image_count = images.count()
        images.delete()
        
        # Delete the batch
        batch.delete()
        
        logger.info(f"Deleted batch {batch_id} with {image_count} images, {deleted_files_count} files, and {annotation_count} annotations")
        
        return JsonResponse({
            'message': f'Batch deleted successfully',
            'batch_id': str(batch_id),
            'deleted_images': image_count,
            'deleted_files': deleted_files_count,
            'deleted_annotations': annotation_count
        })
        
    except UploadBatch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting batch {batch_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)