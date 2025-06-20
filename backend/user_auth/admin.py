from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_approved', 'role', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_approved', 'is_staff', 'is_superuser', 'role')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Permissions', {
            'fields': ('is_approved', 'is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_approved', 'role'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin) 