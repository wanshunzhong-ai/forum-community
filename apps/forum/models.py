"""
论坛核心数据模型。

设计要点：
- 主题（Thread）的正文直接存在 Thread.body 上，回复（Post）单独建表，
  这样「楼主」和「回复」分开处理，逻辑更清晰。
- 点赞（Like）用 GenericForeignKey，可以同时作用于主题和回复，
  不用为每种对象各建一张表。
- 删除一律用「软删除」（is_deleted），数据不真删，方便审计和恢复。
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


def generate_unique_slug(model, instance, value):
    """根据名称生成唯一 slug（识别中文，重复时自动加 -2、-3）。"""
    base = slugify(value, allow_unicode=True) or "item"
    slug = base
    i = 1
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        i += 1
        slug = f"{base}-{i}"
    return slug


class Category(models.Model):
    """版块，例如「技术交流」「闲聊灌水」。"""

    name = models.CharField("名称", max_length=50, unique=True)
    slug = models.SlugField("标识", max_length=80, unique=True, blank=True, allow_unicode=True)
    description = models.CharField("简介", max_length=200, blank=True)
    icon = models.CharField("图标", max_length=8, default="💬")
    order = models.IntegerField("排序", default=0)
    moderators = models.ManyToManyField(
        User, blank=True, related_name="moderated_categories", verbose_name="版主"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "版块"
        verbose_name_plural = "版块"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Category, self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("forum:category_detail", args=[self.pk])


class Tag(models.Model):
    """主题标签，例如 Python、求助。"""

    name = models.CharField("标签", max_length=30, unique=True)
    slug = models.SlugField("标识", max_length=40, unique=True, blank=True, allow_unicode=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "标签"
        verbose_name_plural = "标签"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Tag, self, self.name)
        super().save(*args, **kwargs)


class Thread(models.Model):
    """主题帖。"""

    title = models.CharField("标题", max_length=150)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="threads", verbose_name="版块"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="threads", verbose_name="作者"
    )
    body = models.TextField("正文")
    tags = models.ManyToManyField(Tag, blank=True, related_name="threads", verbose_name="标签")

    is_pinned = models.BooleanField("置顶", default=False)
    is_featured = models.BooleanField("精华", default=False)
    is_closed = models.BooleanField("已关闭", default=False)
    is_deleted = models.BooleanField("已删除", default=False)

    views = models.PositiveIntegerField("浏览数", default=0)
    reply_count = models.PositiveIntegerField("回复数", default=0)

    created_at = models.DateTimeField("发布时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_activity_at = models.DateTimeField("最后活跃", default=timezone.now, db_index=True)

    # 反向拿到所有点赞（虚拟字段，不建列）
    likes = GenericRelation("Like", related_query_name="thread")

    class Meta:
        ordering = ["-is_pinned", "-last_activity_at"]
        verbose_name = "主题"
        verbose_name_plural = "主题"
        indexes = [models.Index(fields=["category", "is_deleted", "-last_activity_at"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:thread_detail", args=[self.pk])

    @property
    def excerpt(self):
        text = self.body.replace("\r", "").replace("\n", " ").strip()
        return text[:120] + ("…" if len(text) > 120 else "")

    def can_edit(self, user):
        return user.is_authenticated and (user == self.author or user.is_moderator)


class Post(models.Model):
    """主题下的回复。"""

    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="posts", verbose_name="主题"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", verbose_name="作者"
    )
    content = models.TextField("内容")
    quote = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="quoted_by", verbose_name="引用",
    )
    floor = models.PositiveIntegerField("楼层", default=1)
    is_deleted = models.BooleanField("已删除", default=False)
    created_at = models.DateTimeField("回复时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    likes = GenericRelation("Like", related_query_name="post")

    class Meta:
        ordering = ["floor", "id"]
        verbose_name = "回复"
        verbose_name_plural = "回复"
        indexes = [models.Index(fields=["thread", "is_deleted", "floor"])]

    def __str__(self):
        return f"#{self.floor} by {self.author}"

    def get_absolute_url(self):
        return f"{self.thread.get_absolute_url()}#post-{self.pk}"

    def can_edit(self, user):
        return user.is_authenticated and (user == self.author or user.is_moderator)


class Like(models.Model):
    """点赞。用「通用外键」同时支持主题和回复。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes", verbose_name="用户")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        unique_together = ("user", "content_type", "object_id")
        verbose_name = "点赞"
        verbose_name_plural = "点赞"
        indexes = [models.Index(fields=["content_type", "object_id"])]


class Favorite(models.Model):
    """收藏主题。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites", verbose_name="用户")
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="favorites", verbose_name="主题")
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        unique_together = ("user", "thread")
        verbose_name = "收藏"
        verbose_name_plural = "收藏"


class Notification(models.Model):
    """站内通知。"""

    class Verb(models.TextChoices):
        REPLY = "reply", "回复"
        MENTION = "mention", "提及"
        LIKE = "like", "点赞"
        FOLLOW = "follow", "关注"
        SYSTEM = "system", "系统"

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications", verbose_name="接收者"
    )
    actor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="actions", verbose_name="触发者",
    )
    verb = models.CharField("类型", max_length=20, choices=Verb.choices)
    message = models.CharField("说明", max_length=200, blank=True)
    url = models.CharField("跳转地址", max_length=300, blank=True)
    is_read = models.BooleanField("已读", default=False, db_index=True)
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "通知"
        verbose_name_plural = "通知"

    def __str__(self):
        return f"{self.recipient} - {self.get_verb_display()}"


class Report(models.Model):
    """举报。同样用通用外键，可举报主题或回复。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        RESOLVED = "resolved", "已处理"
        REJECTED = "rejected", "已忽略"

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports", verbose_name="举报人")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    reason = models.TextField("举报理由")
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    handled_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="handled_reports", verbose_name="处理人",
    )
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "举报"
        verbose_name_plural = "举报"

    def __str__(self):
        return f"举报 {self.content_type} #{self.object_id}"
