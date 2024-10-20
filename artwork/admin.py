from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import Post

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Trainer"), {"fields": ("is_trainer",)}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_trainer")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "is_trainer")
    search_fields = ("username", "first_name", "last_name", "email")

admin.site.register(User, CustomUserAdmin)
admin.site.register(Post)