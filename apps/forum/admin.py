from django.contrib import admin

from .models import Category, Favorite, Like, Notification, Post, Report, Tag, Thread


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("icon", "name", "order", "thread_count")
    list_editable = ("order",)
    search_fields = ("name", "description")
    filter_horizontal = ("moderators",)

    @admin.display(description="主题数")
    def thread_count(self, obj):
        return obj.threads.filter(is_deleted=False).count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = (
        "title", "category", "author", "reply_count", "views",
        "is_pinned", "is_featured", "is_closed", "is_deleted", "last_activity_at",
    )
    list_filter = ("category", "is_pinned", "is_featured", "is_closed", "is_deleted")
    search_fields = ("title", "body")
    raw_id_fields = ("author",)
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    actions = ["make_pinned", "make_featured", "soft_delete"]

    @admin.action(description="置顶选中主题")
    def make_pinned(self, request, queryset):
        queryset.update(is_pinned=True)

    @admin.action(description="设为精华")
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="删除选中主题（软删除）")
    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("thread", "floor", "author", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("content",)
    raw_id_fields = ("thread", "author", "quote")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "created_at")
    list_filter = ("content_type",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "thread", "created_at")
    raw_id_fields = ("thread",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "actor", "verb", "message", "is_read", "created_at")
    list_filter = ("verb", "is_read")
    search_fields = ("recipient__username", "message")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("reporter", "content_type", "object_id", "status", "created_at")
    list_filter = ("status", "content_type")
    search_fields = ("reason", "reporter__username")
    actions = ["mark_resolved", "mark_rejected"]

    @admin.action(description="标记为已处理")
    def mark_resolved(self, request, queryset):
        queryset.update(status=Report.Status.RESOLVED, handled_by=request.user)

    @admin.action(description="标记为已忽略")
    def mark_rejected(self, request, queryset):
        queryset.update(status=Report.Status.REJECTED, handled_by=request.user)
