"""论坛核心视图：首页、版块、主题、回复、点赞、收藏、搜索、通知、举报。"""
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.users.models import User

from .forms import ReplyForm, ReportForm, ThreadForm
from .models import Category, Favorite, Like, Notification, Post, Report, Thread

# 可以被点赞 / 举报的对象类型
MODEL_MAP = {"thread": Thread, "post": Post}

# 匹配 @用户名
MENTION_RE = re.compile(r"@([A-Za-z0-9_\u4e00-\u9fa5]{2,20})")


# ---------------------------------------------------------------- 首页 / 浏览

def home(request):
    """首页：版块列表 + 最新主题 + 热门主题 + 站点统计。"""
    categories = (
        Category.objects.annotate(
            thread_count=Count("threads", filter=Q(threads__is_deleted=False), distinct=True),
            post_count=Count("threads__posts", filter=Q(threads__posts__is_deleted=False), distinct=True),
        ).order_by("order", "id")
    )

    latest_threads = (
        Thread.objects.filter(is_deleted=False)
        .select_related("author", "category")
        .order_by("-is_pinned", "-last_activity_at")[:15]
    )

    hot_threads = (
        Thread.objects.filter(is_deleted=False)
        .select_related("author", "category")
        .annotate(heat=F("reply_count") * 3 + F("views"))
        .order_by("-heat")[:8]
    )

    stats = {
        "threads": Thread.objects.filter(is_deleted=False).count(),
        "posts": Post.objects.filter(is_deleted=False).count(),
        "users": User.objects.count(),
        "today": Thread.objects.filter(created_at__date=timezone.localdate()).count(),
    }

    return render(
        request,
        "home.html",
        {
            "categories": categories,
            "latest_threads": latest_threads,
            "hot_threads": hot_threads,
            "stats": stats,
            "active": "home",
        },
    )


def category_detail(request, pk):
    """版块页：该版块下的主题列表。"""
    category = get_object_or_404(Category, pk=pk)
    qs = Thread.objects.filter(category=category, is_deleted=False).select_related("author")

    sort = request.GET.get("sort", "latest")
    if sort == "hot":
        qs = qs.annotate(heat=F("reply_count") * 3 + F("views")).order_by("-heat")
    elif sort == "new":
        qs = qs.order_by("-created_at")
    else:
        qs = qs.order_by("-is_pinned", "-last_activity_at")

    page_obj = Paginator(qs, settings.PAGE_SIZE).get_page(request.GET.get("page"))

    return render(
        request,
        "forum/category_detail.html",
        {
            "category": category,
            "page_obj": page_obj,
            "sort": sort,
            "thread_total": Thread.objects.filter(category=category, is_deleted=False).count(),
            "active": "categories",
        },
    )


def thread_detail(request, pk):
    """主题详情：楼主正文 + 所有回复。"""
    thread = get_object_or_404(
        Thread.objects.select_related("author", "category"), pk=pk, is_deleted=False
    )
    # 浏览量 +1（用 update 避免触发 updated_at）
    Thread.objects.filter(pk=thread.pk).update(views=F("views") + 1)
    thread.views += 1

    posts = list(
        thread.posts.filter(is_deleted=False).select_related("author", "quote", "quote__author")
    )

    liked_thread = False
    liked_post_ids = set()
    favorited = False
    if request.user.is_authenticated:
        thread_ct = ContentType.objects.get_for_model(Thread)
        liked_thread = Like.objects.filter(
            user=request.user, content_type=thread_ct, object_id=thread.pk
        ).exists()
        favorited = Favorite.objects.filter(user=request.user, thread=thread).exists()
        if posts:
            post_ct = ContentType.objects.get_for_model(Post)
            liked_post_ids = set(
                Like.objects.filter(
                    user=request.user, content_type=post_ct, object_id__in=[p.pk for p in posts]
                ).values_list("object_id", flat=True)
            )

    return render(
        request,
        "forum/thread_detail.html",
        {
            "thread": thread,
            "posts": posts,
            "reply_form": ReplyForm(),
            "liked_thread": liked_thread,
            "liked_post_ids": liked_post_ids,
            "favorited": favorited,
            "can_edit": thread.can_edit(request.user),
            "active": "categories",
        },
    )


def search(request):
    """全文搜索（标题 + 正文）。"""
    q = request.GET.get("q", "").strip()
    page_obj = None
    if q:
        qs = (
            Thread.objects.filter(is_deleted=False)
            .filter(Q(title__icontains=q) | Q(body__icontains=q))
            .select_related("author", "category")
            .order_by("-last_activity_at")
        )
        page_obj = Paginator(qs, settings.PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "forum/search.html", {"q": q, "page_obj": page_obj})


# ---------------------------------------------------------------- 发布 / 编辑

@login_required
def thread_create(request, category_pk=None):
    """发布新主题。"""
    initial = {}
    if category_pk:
        initial["category"] = get_object_or_404(Category, pk=category_pk)

    if request.method == "POST":
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.last_activity_at = timezone.now()
            thread.save()
            form.save_tags(thread)
            request.user.add_points(5)
            messages.success(request, "发布成功！")
            return redirect(thread)
    else:
        form = ThreadForm(initial=initial)

    return render(request, "forum/thread_form.html", {"form": form, "active": "new"})


@login_required
def thread_edit(request, pk):
    """编辑主题。"""
    thread = get_object_or_404(Thread, pk=pk, is_deleted=False)
    if not thread.can_edit(request.user):
        messages.error(request, "你没有权限编辑这个主题")
        return redirect(thread)

    if request.method == "POST":
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            form.save_tags(thread)
            messages.success(request, "已保存")
            return redirect(thread)
    else:
        form = ThreadForm(
            instance=thread,
            initial={"tags_input": " ".join(t.name for t in thread.tags.all())},
        )
    return render(request, "forum/thread_form.html", {"form": form, "thread": thread, "active": "new"})


@login_required
@require_POST
def thread_delete(request, pk):
    """删除主题（软删除）。"""
    thread = get_object_or_404(Thread, pk=pk)
    if not thread.can_edit(request.user):
        messages.error(request, "你没有权限删除这个主题")
        return redirect(thread)
    thread.is_deleted = True
    thread.save(update_fields=["is_deleted"])
    messages.success(request, "主题已删除")
    return redirect(thread.category)


@login_required
@require_POST
def post_delete(request, pk):
    """删除回复（软删除）。"""
    post = get_object_or_404(Post, pk=pk)
    thread = post.thread
    if not post.can_edit(request.user):
        messages.error(request, "你没有权限删除这条回复")
        return redirect(thread)

    if not post.is_deleted:
        post.is_deleted = True
        post.save(update_fields=["is_deleted"])
        Thread.objects.filter(pk=thread.pk, reply_count__gt=0).update(
            reply_count=F("reply_count") - 1
        )
    messages.success(request, "回复已删除")
    return redirect(thread)


@login_required
@require_POST
def thread_moderate(request, pk):
    """版主操作：置顶 / 精华 / 关闭。"""
    thread = get_object_or_404(Thread, pk=pk)
    if not request.user.is_moderator:
        messages.error(request, "只有版主可以执行这个操作")
        return redirect(thread)

    action = request.POST.get("action")
    if action == "pin":
        thread.is_pinned = not thread.is_pinned
    elif action == "feature":
        thread.is_featured = not thread.is_featured
    elif action == "close":
        thread.is_closed = not thread.is_closed
    thread.save()
    messages.success(request, "操作成功")
    return redirect(thread)


@login_required
@require_POST
def reply_create(request, pk):
    """回复主题。"""
    thread = get_object_or_404(Thread, pk=pk, is_deleted=False)
    if thread.is_closed and not request.user.is_moderator:
        messages.error(request, "该主题已关闭，暂时不能回复")
        return redirect(thread)

    form = ReplyForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.thread = thread
        post.author = request.user
        post.floor = thread.reply_count + 1
        quote_id = request.POST.get("quote")
        if quote_id:
            post.quote = Post.objects.filter(pk=quote_id, thread=thread).first()
        post.save()

        Thread.objects.filter(pk=thread.pk).update(
            reply_count=F("reply_count") + 1, last_activity_at=timezone.now()
        )
        request.user.add_points(2)
        notify_new_reply(thread, post, request.user)
        messages.success(request, "回复成功")
        return redirect(f"{thread.get_absolute_url()}#post-{post.pk}")

    messages.error(request, "回复内容不能为空")
    return redirect(thread)


def notify_new_reply(thread, post, actor):
    """给楼主和 @ 到的人发通知。"""
    notified = set()

    if thread.author != actor:
        Notification.objects.create(
            recipient=thread.author,
            actor=actor,
            verb=Notification.Verb.REPLY,
            message=f"回复了你的主题《{thread.title}》",
            url=post.get_absolute_url(),
        )
        notified.add(thread.author.pk)

    names = set(MENTION_RE.findall(post.content))
    if names:
        for user in User.objects.filter(username__in=names):
            if user == actor or user.pk in notified:
                continue
            Notification.objects.create(
                recipient=user,
                actor=actor,
                verb=Notification.Verb.MENTION,
                message=f"在《{thread.title}》中提到了你",
                url=post.get_absolute_url(),
            )


# ---------------------------------------------------------------- 互动

@login_required
@require_POST
def like_toggle(request, model, pk):
    """点赞 / 取消点赞（主题或回复）。"""
    cls = MODEL_MAP.get(model)
    if cls is None:
        raise Http404("未知的对象类型")
    obj = get_object_or_404(cls, pk=pk)
    ct = ContentType.objects.get_for_model(cls)

    like, created = Like.objects.get_or_create(user=request.user, content_type=ct, object_id=obj.pk)
    if not created:
        like.delete()
    else:
        owner = obj.author
        if owner != request.user:
            Notification.objects.create(
                recipient=owner,
                actor=request.user,
                verb=Notification.Verb.LIKE,
                message="赞了你的内容",
                url=obj.get_absolute_url(),
            )

    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or "/")


@login_required
@require_POST
def favorite_toggle(request, pk):
    """收藏 / 取消收藏主题。"""
    thread = get_object_or_404(Thread, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, thread=thread)
    if not created:
        fav.delete()
        messages.info(request, "已取消收藏")
    else:
        messages.success(request, "已收藏")
    return redirect(request.POST.get("next") or thread.get_absolute_url())


# ---------------------------------------------------------------- 通知 / 举报

@login_required
def notification_list(request):
    """通知中心。查看后自动标记为已读。"""
    qs = request.user.notifications.select_related("actor")
    page_obj = Paginator(qs, 30).get_page(request.GET.get("page"))
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(
        request,
        "forum/notifications.html",
        {"page_obj": page_obj, "active": "notifications"},
    )


@login_required
def report_create(request, model, pk):
    """举报主题或回复。"""
    cls = MODEL_MAP.get(model)
    if cls is None:
        raise Http404("未知的对象类型")
    obj = get_object_or_404(cls, pk=pk)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            Report.objects.create(
                reporter=request.user,
                content_type=ContentType.objects.get_for_model(cls),
                object_id=obj.pk,
                reason=form.cleaned_data["reason"],
            )
            messages.success(request, "举报已提交，管理员会尽快处理。")
            return redirect(obj.get_absolute_url())
    else:
        form = ReportForm()

    return render(request, "forum/report_form.html", {"form": form, "target": obj})
