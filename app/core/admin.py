from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _
from . import models


class UserAdmin(BaseUserAdmin):
    """
    Specifies the  ordering and the custom fields to
    display in admin view.
    """
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password',)}),
        (_('Personal details'), {'fields': ('name',)}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser',)}
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined',)})
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide'),
                'fields': ('email', 'password1', 'password2', 'date_joined'),
            }
        ),
    )


admin.site.register(models.User, UserAdmin)
