"""
用户相关数据模型。

⚠️ 重要：自定义用户模型必须在项目**第一次 migrate 之前**就定好，
   因为 Django 的 AUTH_USER_MODEL 一旦建表，后期更换代价极高。
   我们把论坛需要的字段（昵称、头像、签名、积分、角色）直接扩展在 User 上，
   这样就不用额外再建一张 Profile 表。
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """论坛用户。继承 AbstractUser，自带用户名/密码/邮箱/权限等。"""

    class Role(models.TextChoices):
        MEMBER = "member", "普通用户"
        MODERATOR = "moderator", "版主"
        ADMIN = "admin", "管理员"

    nickname = models.CharField("昵称", max_length=40, blank=True)
    avatar = models.ImageField("头像", upload_to="avatars/%Y/%m/", blank=True, null=True)
    bio = models.CharField("个性签名", max_length=200, blank=True)
    location = models.CharField("所在地", max_length=60, blank=True)
    website = models.URLField("个人网站", blank=True)
    points = models.PositiveIntegerField("积分", default=0, db_index=True)
    role = models.CharField("角色", max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField("注册时间", auto_now_add=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        """优先显示昵称，没有就用用户名。"""
        return self.nickname or self.username

    def get_absolute_url(self):
        return reverse("users:profile", args=[self.pk])

    @property
    def is_moderator(self):
        """是否是版主/管理员（用来在页面上显示管理按钮）。"""
        return self.role in (self.Role.MODERATOR, self.Role.ADMIN) or self.is_staff

    def is_following(self, other):
        if not self.is_authenticated or self.pk == other.pk:
            return False
        return Follow.objects.filter(follower=self, following=other).exists()

    def add_points(self, n):
        """加/减积分（用 F 表达式避免并发问题）。"""
        User.objects.filter(pk=self.pk).update(points=models.F("points") + n)


class Follow(models.Model):
    """关注关系：follower 关注了 following。"""

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following", verbose_name="关注者"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers", verbose_name="被关注者"
    )
    created_at = models.DateTimeField("关注时间", auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
        verbose_name = "关注关系"
        verbose_name_plural = "关注关系"

    def __str__(self):
        return f"{self.follower} → {self.following}"
