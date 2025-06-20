from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from .models import CustomUser
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
import secrets
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', CustomUser.Role.ANNOTATOR)
        
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
            
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_approved=False,
            role=role
        )
        
        return JsonResponse({
            'message': 'Registration successful. Waiting for admin approval.',
            'user_id': user.id
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            print(f"Login attempt for user: {username}")
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                print(f"User authenticated: {user.username}")
                if user.is_approved:
                    login(request, user)
                    # Get tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # Create consistent response format that matches frontend expectations
                    response_data = {
                        'message': 'Login successful',
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_approved': user.is_approved,
                        'role': user.role,
                        'accessToken': str(refresh.access_token),
                        'refreshToken': str(refresh)
                    }
                    print(f"Sending response: {response_data}")
                    return JsonResponse(response_data)
                else:
                    print(f"User {username} not approved")
                    return JsonResponse({'error': 'Account pending approval'}, status=403)
            else:
                print(f"Invalid credentials for user: {username}")
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            print(f"Login error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logout successful'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_status(request):
    return JsonResponse({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_approved': request.user.is_approved,
            'role': request.user.role
        }
    })

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    if request.method == 'GET':
        # Check if the requesting user is an admin
        if not request.user.role == CustomUser.Role.ADMIN:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        users = CustomUser.objects.all()
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_approved': user.is_approved,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        } for user in users]
        
        return JsonResponse({'users': users_data})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_user(request, user_id):
    if request.method == 'POST':
        # Check if the requesting user is an admin
        if not request.user.role == CustomUser.Role.ADMIN:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            user = CustomUser.objects.get(id=user_id)
            user.is_approved = True
            user.save()
            return JsonResponse({
                'message': 'User approved successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_approved': user.is_approved,
                    'role': user.role
                }
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_role(request, user_id):
    if request.method == 'POST':
        # Check if the requesting user is an admin
        if not request.user.role == CustomUser.Role.ADMIN:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            data = json.loads(request.body)
            new_role = data.get('role')
            
            if new_role not in [role[0] for role in CustomUser.Role.choices]:
                return JsonResponse({'error': 'Invalid role'}, status=400)
            
            user = CustomUser.objects.get(id=user_id)
            user.role = new_role
            user.save()
            
            return JsonResponse({
                'message': 'User role updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_approved': user.is_approved,
                    'role': user.role
                }
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_users(request):
    if not request.user.role == CustomUser.Role.ADMIN:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    pending_users = CustomUser.objects.filter(is_approved=False)
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined,
        'role': user.role
    } for user in pending_users]
    
    return JsonResponse({'users': users_data})

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    if not request.user.role == CustomUser.Role.ADMIN:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        is_approved = request.GET.get('is_approved')
        
        # Base queryset
        users = CustomUser.objects.all()
        
        # Apply filters
        if is_approved is not None:
            is_approved = is_approved.lower() == 'true'
            users = users.filter(is_approved=is_approved)
        
        # Calculate pagination
        total_users = users.count()
        total_pages = (total_users + per_page - 1) // per_page
        
        # Get paginated users
        start = (page - 1) * per_page
        end = start + per_page
        paginated_users = users[start:end]
        
        # Prepare response data
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
            'is_approved': user.is_approved,
            'role': user.role
        } for user in paginated_users]
        
        return JsonResponse({
            'users': users_data,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_users': total_users,
                'per_page': per_page
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email)
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.save()
        
        # Enhanced email template
        reset_link = f"http://localhost:5173/reset-password/{token}"
        
        email_subject = "Password Reset Request - KPA Annotation Tool"
        email_body = f"""
Dear {user.username},

You have requested to reset your password for the KPA Annotation Tool.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

For support, contact: {settings.DEFAULT_FROM_EMAIL}

Best regards,
KPA Annotation Tool Team
        """.strip()
        
        send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response(
            {'message': 'If an account exists with this email, you will receive a password reset link'}, 
            status=status.HTTP_200_OK
        )
    except CustomUser.DoesNotExist:
        # Don't reveal if email exists or not for security
        return Response(
            {'message': 'If an account exists with this email, you will receive a password reset link'}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Password reset email error: {str(e)}")
        return Response(
            {'error': 'Failed to send password reset email. Please try again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not token or not new_password:
        return Response({'error': 'Token and new password are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(password_reset_token=token)
        # Validate password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.password_reset_token = None  # Clear the token
        user.save()
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_user(request, user_id):
    if request.method == 'POST':
        # Check if the requesting user is an admin
        if not request.user.role == CustomUser.Role.ADMIN:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            user = CustomUser.objects.get(id=user_id)
            
            # Prevent admin from rejecting themselves
            if user.id == request.user.id:
                return JsonResponse({'error': 'Cannot reject your own account'}, status=400)
            
            # Store user info for response
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
            
            # Delete the user (rejection = permanent removal)
            user.delete()
            
            return JsonResponse({
                'message': 'User rejected and removed successfully',
                'user': user_info
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if request.method == 'DELETE':
        # Check if the requesting user is an admin
        if not request.user.role == CustomUser.Role.ADMIN:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            user = CustomUser.objects.get(id=user_id)
            
            # Prevent admin from deleting themselves
            if user.id == request.user.id:
                return JsonResponse({'error': 'Cannot delete your own account'}, status=400)
            
            # Store user info for response
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
            
            # Delete the user
            user.delete()
            
            return JsonResponse({
                'message': 'User deleted successfully',
                'user': user_info
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pause_user(request, user_id):
    if request.method == 'POST':
        # Check if the requesting user is an admin
        if not request.user.role == CustomUser.Role.ADMIN:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            user = CustomUser.objects.get(id=user_id)
            
            # Prevent admin from pausing themselves
            if user.id == request.user.id:
                return JsonResponse({'error': 'Cannot pause your own account'}, status=400)
            
            # Toggle the approval status (pause/unpause)
            user.is_approved = not user.is_approved
            user.save()
            
            action = 'paused' if not user.is_approved else 'unpaused'
            
            return JsonResponse({
                'message': f'User {action} successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_approved': user.is_approved,
                    'role': user.role
                }
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)