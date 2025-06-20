from django.urls import path
from . import views

urlpatterns = [
    # Batch management
    path('create-batch/', views.create_upload_batch, name='create-upload-batch'),
    path('batches/', views.get_batch_list, name='batch-list'),
    path('batch/<uuid:batch_id>/status/', views.get_batch_status, name='batch-status'),
    path('batch/<uuid:batch_id>/images/', views.get_batch_images, name='batch-images'),
    path('batch/<uuid:batch_id>/cancel/', views.cancel_batch, name='cancel-batch'),
    path('batch/<uuid:batch_id>/retry/', views.retry_failed_images, name='retry-batch'),
    path('batch/<uuid:batch_id>/delete/', views.delete_batch, name='delete-batch'),
    
    # YOLO Processing (Manual Control)
    path('batch/<uuid:batch_id>/process/', views.process_batch_with_yolo, name='process-batch-yolo'),
    path('image/<uuid:image_id>/process/', views.process_single_image, name='process-single-image'),
    path('yolo-model-info/', views.get_yolo_model_info, name='yolo-model-info'),
    
    # Image upload
    path('upload/', views.upload_image, name='upload-image'),
]