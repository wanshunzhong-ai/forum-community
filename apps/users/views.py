"""用户相关视图：注册、登录、退出、个人主页、编辑资料、关注。"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import ProfileEditForm, RegisterForm
from .models import Follow, User


class RegisterView(CreateView):
    """注册。注册成功后自动登录并跳回首页。"""

    model = User
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("forum:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f"注册成功，欢迎加入，{self.object.display_name}！")
        return response


class UserLoginView(LoginView):
    """登录。"""

    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "登录成功")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """退出登录（Django 5 要求用 POST 提交）。"""

    next_page = reverse_lazy("forum:home")


class ProfileView(DetailView):
    """用户主页：基本资料 + 他发过的帖子 + 他的回复。"""

    model = User
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.object
        ctx["threads"] = (
            user.threads.filter(is_deleted=False)
            .select_related("category")
            .order_by("-created_at")[:20]
        )
        ctx["posts"] = (
            user.posts.filter(is_deleted=False)
            .select_related("thread", "thread__category")
            .order_by("-created_at")[:20]
        )
        ctx["thread_count"] = user.threads.filter(is_deleted=False).count()
        ctx["post_count"] = user.posts.filter(is_deleted=False).count()
        ctx["followers_count"] = user.followers.count()
        ctx["following_count"] = user.following.count()
        if self.request.user.is_authenticated:
            ctx["is_following"] = self.request.user.is_following(user)
        return ctx


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """编辑自己的资料。"""

    model = User
    form_class = ProfileEditForm
    template_name = "users/profile_edit.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("users:profile", args=[self.request.user.pk])

    def form_valid(self, form):
        messages.success(self.request, "资料已保存")
        return super().form_valid(form)


@login_required
def follow_toggle(request, pk):
    """关注 / 取消关注（POST）。"""
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "不能关注自己哦")
        return redirect(target)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow.delete()
        messages.info(request, f"已取消关注 {target.display_name}")
    else:
        messages.success(request, f"已关注 {target.display_name}")
        # 给对方发一条通知
        from apps.forum.models import Notification

        Notification.objects.create(
            recipient=target,
            actor=request.user,
            verb=Notification.Verb.FOLLOW,
            message="关注了你",
            url=reverse("users:profile", args=[request.user.pk]),
        )
    return redirect(target)
