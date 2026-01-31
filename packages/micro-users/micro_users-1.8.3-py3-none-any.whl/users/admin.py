# Imports of the required python modules and libraries
######################################################
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

from .models import UserActivityLog, Scope

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'scope', 'is_staff', 'is_active', 'phone']
    list_filter = ['is_staff', 'is_active', 'scope']
    search_fields = ['username', 'email']
    ordering = ['username']

@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'object_id', 'ip_address')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'number', 'ip_address', 'user_agent', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(User, CustomUserAdmin)
admin.site.register(Scope)
admin.site.unregister(Group)
