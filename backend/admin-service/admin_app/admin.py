# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Admin, JournalActivite

@admin.register(Admin)
class CustomAdmin(UserAdmin):
    """
    Extends Django's UserAdmin to show our custom fields (like email) correctly.
    """
    # We tell Django Admin to display these columns in the list view
    list_display = ('email', 'first_name', 'is_staff', 'is_active')
    
    # We override the fieldsets to remove 'username' and use 'email' instead
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # This defines the layout when creating a new user from the admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    # The field used to search for users
    search_fields = ('email',)
    ordering = ('email',)

@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    """
    Configuration for the Activity Journal view.
    """
    # Columns to show in the list view
    list_display = ('date_action', 'admin', 'action', 'target_type', 'target_id')
    
    # Filters on the right side of the screen
    list_filter = ('action', 'target_type', 'date_action')
    
    # Make the journal read-only (you cannot edit an audit log!)
    readonly_fields = ('admin', 'action', 'target_type', 'target_id', 'details', 'date_action')

    def has_add_permission(self, request):
        # Disable the "Add" button. Journals should only be created by code.
        return False

    def has_change_permission(self, request, obj=None):
        # Disable editing existing logs.
        return False
