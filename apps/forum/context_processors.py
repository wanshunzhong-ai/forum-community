"""模板上下文处理器：让所有页面都能拿到未读通知数。"""


def site_context(request):
    unread = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        unread = user.notifications.filter(is_read=False).count()
    return {
        "unread_count": unread,
        "site_name": "论坛社区",
    }
