"""
URL 总路由。

访问不同网址 → 交给不同应用处理。
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.forum.urls')),
    path('', include('apps.users.urls')),
]

# 开发环境下，让 Django 提供用户上传的文件（头像、图片）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
