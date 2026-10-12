from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "nickname", "email", "role", "points", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "nickname", "email")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("论坛资料", {"fields": ("nickname", "avatar", "bio", "location", "website", "points", "role")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("论坛资料", {"fields": ("nickname", "email", "role")}),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
