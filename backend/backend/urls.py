"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from user_auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints - use user_auth views for consistency
    path('api/auth/register/', auth_views.register_user, name='auth-register'),
    path('api/auth/login/', auth_views.login_user, name='auth-login'),
    path('api/auth/logout/', auth_views.logout_user, name='auth-logout'),
    path('api/auth/status/', auth_views.get_user_status, name='auth-status'),
    path('api/auth/get-users/', auth_views.get_users, name='get-users'),
    path('api/auth/approve-user/<int:user_id>/', auth_views.approve_user, name='auth-approve-user'),
    path('api/auth/update-role/<int:user_id>/', auth_views.update_user_role, name='auth-update-role'),
    path('api/auth/delete-user/<int:user_id>/', auth_views.delete_user, name='auth-delete-user'),
    path('api/auth/reject-user/<int:user_id>/', auth_views.reject_user, name='auth-reject-user'),
    path('api/auth/pause-user/<int:user_id>/', auth_views.pause_user, name='auth-pause-user'),
    path('api/auth/pending-users/', auth_views.get_pending_users, name='auth-pending-users'),
    
    # JWT token endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Images app endpoints (includes YOLO processing)
    path('api/images/', include('images.urls')),
    
    # Image upload endpoints (legacy - keep for backward compatibility)
    path('api/images/create-batch/', views.create_batch, name='create_batch'),
    path('api/images/upload/', views.upload_image, name='upload_image'),
    
    # Legacy endpoints (keep for backward compatibility)
    path('api/register/', views.register_user, name='register'),
    path('api/login/', views.login_user, name='login'),
    path('api/logout/', views.logout_user, name='logout'),
    path('api/user/status/', views.get_user_status, name='user-status'),
    path('api/admin/approve-user/<int:user_id>/', views.approve_user, name='approve-user'),
    path('api/admin/pending-users/', views.get_pending_users, name='pending-users'),
]
