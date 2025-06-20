from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from user_auth.models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import json
import uuid
import logging
import requests
import os
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validate required fields
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        if not password:
            return JsonResponse({'error': 'Password is required'}, status=400)
        
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
            
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_approved=False
            
        )
        
        return JsonResponse({
            'message': 'Registration successful. Waiting for admin approval.',
            'user_id': user.id
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_approved:
                login(request, user)
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                
                return JsonResponse({
                    'message': 'Login successful',
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_approved': user.is_approved,
                    'role': user.role,
                    'accessToken': str(access_token),
                    'refreshToken': str(refresh)
                })
            else:
                return JsonResponse({'error': 'Account pending approval'}, status=403)
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logout successful'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def get_user_status(request):
    return JsonResponse({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_approved': request.user.is_approved
        }
    })

@login_required
def approve_user(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_approved = True
        user.save()
        return JsonResponse({'message': 'User approved successfully'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
def get_pending_users(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    pending_users = CustomUser.objects.filter(is_approved=False)
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined,
        'role': user.role
    } for user in pending_users]
    
    return JsonResponse({'pending_users': users_data})

@login_required
@csrf_exempt
def delete_user(request, user_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Prevent admin from deleting themselves
    if request.user.id == int(user_id):
        return JsonResponse({'error': 'Cannot delete your own account'}, status=400)
    
    try:
        user = CustomUser.objects.get(id=user_id)
        username = user.username
        user.delete()
        return JsonResponse({'message': f'User {username} deleted successfully'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
@csrf_exempt
def pause_user(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Prevent admin from pausing themselves
    if request.user.id == int(user_id):
        return JsonResponse({'error': 'Cannot pause your own account'}, status=400)
    
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_approved = not user.is_approved  # Toggle approval status
        user.save()
        
        action = 'paused' if not user.is_approved else 'unpaused'
        return JsonResponse({'message': f'User {user.username} {action} successfully'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_batch(request):
    """Create a new upload batch"""
    try:
        data = json.loads(request.body)
        total_files = data.get('total_files', 0)
        metadata = data.get('metadata', {})
        
        if total_files <= 0:
            return JsonResponse({'error': 'total_files must be greater than 0'}, status=400)
        
        # Generate a unique batch ID
        batch_id = str(uuid.uuid4())
        
        # You can store batch information in database if needed
        # For now, we'll just return the batch_id
        
        logger.info(f"Created batch {batch_id} for {total_files} files by user {request.user.username}")
        
        return JsonResponse({
            'batch_id': batch_id,
            'message': 'Batch created successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Batch creation error: {str(e)}")
        return JsonResponse({'error': 'Failed to create batch'}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """Handle individual image upload"""
    try:
        batch_id = request.POST.get('batch_id')
        file_id = request.POST.get('file_id')
        uploaded_file = request.FILES.get('file')
        
        if not batch_id:
            return JsonResponse({'error': 'batch_id is required'}, status=400)
        
        if not file_id:
            return JsonResponse({'error': 'file_id is required'}, status=400)
            
        if not uploaded_file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
            
        # Validate UUID format
        try:
            uuid.UUID(batch_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid batch_id format'}, status=400)
        
        # Validate file type
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({'error': f'File type {file_extension} not allowed'}, status=400)
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', batch_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, f"{file_id}_{uploaded_file.name}")
        
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        logger.info(f"File {uploaded_file.name} uploaded successfully for batch {batch_id}")
        
        # Here you can add your YOLO processing logic
        # For now, we'll just return success
        
        return JsonResponse({
            'message': 'File uploaded successfully',
            'file_id': file_id,
            'batch_id': batch_id,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JsonResponse({'error': 'Upload failed. Please try again.'}, status=500)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_batches(request):
    """"Create new upload batches"""
    try:
        data = json.loads(request.body)
        total_files = data.get('total_files', 0)
        metadata = data.get('metadata',{})

        if total_files <= 0:
            return JsonResponse({'error': 'total_files must be greater than 0'}, status=400)
        
        batch_id = str(uuid.uuid4())

        logger.info(f'created batch {batch_id} for {total_files} files by user  {request.user.username} ')

        return JsonResponse({
            'batch_id': batch_id,
            'message': 'Batch created successfully' 
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f'Batch creation error: {str(e)}')
        return JsonResponse({'error': 'Failed to create batch'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """Handle individual image upload and prevent duplicate uploads in the same batch"""
    try:
        batch_id = request.POST.get('batch_id')
        file_id = request.POST.get('file_id')
        uploaded_file = request.FILES.get('file')

        if not batch_id:
            return JsonResponse({'error': 'batch_id is required'}, status=400)

        if not file_id:
            return JsonResponse({'error': 'file_id is required'}, status=400)

        if not uploaded_file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)

        # Validate UUID format
        try:
            uuid.UUID(batch_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid batch_id format'}, status=400)

        # Validate file type
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        if file_extension not in allowed_extensions:
            return JsonResponse({'error': f'File type {file_extension} not allowed'}, status=400)

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', batch_id)
        os.makedirs(upload_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(upload_dir, f"{file_id}_{uploaded_file.name}")

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        logger.info(f"File {uploaded_file.name} uploaded successfully for batch {batch_id}")

        # Here you can add your YOLO processing logic
        # For now, we'll just return success

        return JsonResponse({
            'message': 'File uploaded successfully',
            'file_id': file_id,
            'batch_id': batch_id,
            'file_path': file_path
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JsonResponse({'error': 'Upload failed. Please try again.'}, status=500)
    

