from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("notifications/", views.notification_list, name="notifications"),

    # 版块
    path("c/<int:pk>/", views.category_detail, name="category_detail"),
    path("c/<int:category_pk>/new/", views.thread_create, name="thread_create_in_category"),

    # 主题
    path("new/", views.thread_create, name="thread_create"),
    path("t/<int:pk>/", views.thread_detail, name="thread_detail"),
    path("t/<int:pk>/edit/", views.thread_edit, name="thread_edit"),
    path("t/<int:pk>/delete/", views.thread_delete, name="thread_delete"),
    path("t/<int:pk>/moderate/", views.thread_moderate, name="thread_moderate"),
    path("t/<int:pk>/reply/", views.reply_create, name="reply_create"),
    path("t/<int:pk>/favorite/", views.favorite_toggle, name="favorite_toggle"),
    path("p/<int:pk>/delete/", views.post_delete, name="post_delete"),

    # 通用互动
    path("like/<str:model>/<int:pk>/", views.like_toggle, name="like_toggle"),
    path("report/<str:model>/<int:pk>/", views.report_create, name="report_create"),
]
