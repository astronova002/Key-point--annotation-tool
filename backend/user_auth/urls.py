from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('status/', views.get_user_status, name='status'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject-user/<int:user_id>/', views.reject_user, name='reject_user'),
    path('request-password-reset/', views.request_password_reset, name='request_password_reset'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('pending-users/', views.get_pending_users, name='pending_users'),
    path('update-role/<int:user_id>/', views.update_user_role, name='update_role'),
    path('get-users/', views.get_users, name='get_users'),
    path('get-all-users/', views.get_all_users, name='get_all_users'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('pause-user/<int:user_id>/', views.pause_user, name='pause_user'),
]