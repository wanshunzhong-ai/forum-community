"""一键生成演示数据：版块、用户、主题、回复、点赞、关注、通知。

用法：
    python manage.py seed_demo
可以重复执行，不会产生重复数据。
"""
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.forum.models import Category, Favorite, Like, Notification, Post, Tag, Thread
from apps.users.models import Follow, User

CATEGORIES = [
    ("技术交流", "🔧", "编程、框架、踩坑经验分享"),
    ("产品设计", "🎨", "产品思考、交互设计与用户体验"),
    ("闲聊灌水", "☕", "随便聊聊，放松一下"),
    ("公告反馈", "📢", "站点公告与问题反馈"),
]

USERS = [
    # 用户名, 昵称, 邮箱, 密码, 角色, 是超管?, 是staff?
    ("admin", "管理员", "admin@example.com", "admin123456", User.Role.ADMIN, True, True),
    ("zhangsan", "张三", "zhangsan@example.com", "test123456", User.Role.MEMBER, False, False),
    ("lisi", "李四", "lisi@example.com", "test123456", User.Role.MEMBER, False, False),
    ("wangwu", "王五", "wangwu@example.com", "test123456", User.Role.MODERATOR, False, False),
]

THREADS = [
    (
        "技术交流",
        "admin",
        "【公告】欢迎来到论坛社区，先看这里 👋",
        "欢迎加入！这是一个用 **Django** 搭建的论坛。\n\n"
        "## 你可以做什么\n\n"
        "- 发帖、回复、点赞、收藏\n"
        "- 关注感兴趣的作者\n"
        "- 用 `@用户名` 提及他人\n\n"
        "> 正文支持 **Markdown**，可以写代码块、表格、列表。\n\n"
        "祝大家交流愉快！",
        ["公告", "新手必读"],
        True, True, False,
    ),
    (
        "技术交流",
        "zhangsan",
        "Django 里 select_related 和 prefetch_related 到底怎么选？",
        "最近在优化列表页，N+1 查询有点多。\n\n"
        "我的理解是：\n\n"
        "1. `select_related` 用于**一对一/多对一**（JOIN）\n"
        "2. `prefetch_related` 用于**一对多/多对多**（额外一次查询）\n\n"
        "```python\n"
        "Thread.objects.select_related('author', 'category')\n"
        "      .prefetch_related('tags')\n"
        "```\n\n"
        "大家还有别的实战经验吗？",
        ["Django", "性能优化"],
        False, True, False,
    ),
    (
        "技术交流",
        "lisi",
        "自定义用户模型为什么必须在第一次 migrate 前决定？",
        "新手求教，看到文档里反复强调这一点。\n\n"
        "我理解是 `AUTH_USER_MODEL` 建表之后，改动会牵连一堆外键，"
        "但具体会踩什么坑呢？有没有人踩过？",
        ["Django", "求助"],
        False, False, False,
    ),
    (
        "产品设计",
        "wangwu",
        "论坛的「楼层」到底该不该显示？",
        "我观察到很多社区都去掉了楼层号。\n\n"
        "**支持显示的理由**：方便引用、有「盖楼」的社区感。\n"
        "**支持去掉的理由**：容易产生无意义的「抢楼」，且移动端很挤。\n\n"
        "大家怎么看？",
        ["产品设计", "讨论"],
        False, False, False,
    ),
    (
        "闲聊灌水",
        "zhangsan",
        "大家平时用什么编辑器写代码？",
        "最近在纠结 VS Code 和 PyCharm，想听听大家的看法～",
        ["闲聊"],
        False, False, False,
    ),
]

REPLIES = [
    (0, "zhangsan", "收到，已阅！界面很清爽 👍"),
    (0, "lisi", "感谢管理员，希望社区越来越好。"),
    (1, "wangwu", "补充一点：`prefetch_related` 也支持 `Prefetch` 对象做自定义查询，"
                  "可以只预取需要的数据，比无脑 prefetch 更省。"),
    (1, "admin", "经验之谈：先用 `django-debug-toolbar` 把 N+1 找出来，再针对性优化，别过早优化。"),
    (2, "admin", "主要是两点：1）`INSTALLED_APPS` 里所有 app 的外键都指向它；"
                 "2）迁移一旦生成，改起来要写数据迁移。所以项目一开始就定好最省事。"),
    (3, "lisi", "我倾向去掉楼层号，改成显示「回复」按钮，体验更干净。"),
    (3, "zhangsan", "引用功能做好了其实楼层就无所谓了。"),
    (4, "lisi", "VS Code，插件生态太香了。"),
]


class Command(BaseCommand):
    help = "生成演示数据（版块 / 用户 / 主题 / 回复 / 点赞 / 关注 / 通知）"

    def handle(self, *args, **options):
        self.stdout.write("开始生成演示数据…")

        # 1. 版块
        categories = {}
        for i, (name, icon, desc) in enumerate(CATEGORIES):
            cat, _ = Category.objects.get_or_create(
                name=name, defaults={"icon": icon, "description": desc, "order": i}
            )
            categories[name] = cat
        self.stdout.write(f"  版块 {len(categories)} 个")

        # 2. 用户
        users = {}
        for username, nickname, email, password, role, is_super, is_staff in USERS:
            user = User.objects.filter(username=username).first()
            if user is None:
                if is_super:
                    user = User.objects.create_superuser(username, email, password)
                else:
                    user = User.objects.create_user(username, email, password)
                user.nickname = nickname
                user.role = role
                user.is_staff = is_staff
                user.points = 100 if role != User.Role.MEMBER else 30
                user.bio = "这个人很懒，什么都没写"
                user.save()
            users[username] = user
        self.stdout.write(f"  用户 {len(users)} 个")

        # 3. 主题
        threads = []
        for cat_name, author_name, title, body, tags, pinned, featured, closed in THREADS:
            thread, created = Thread.objects.get_or_create(
                title=title,
                defaults={
                    "category": categories[cat_name],
                    "author": users[author_name],
                    "body": body,
                    "is_pinned": pinned,
                    "is_featured": featured,
                    "is_closed": closed,
                    "views": 42,
                },
            )
            if created:
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    thread.tags.add(tag)
            threads.append(thread)
        self.stdout.write(f"  主题 {len(threads)} 个")

        # 4. 回复
        created_replies = 0
        for thread_index, author_name, content in REPLIES:
            thread = threads[thread_index]
            author = users[author_name]
            exists = Post.objects.filter(thread=thread, author=author, content=content).exists()
            if exists:
                continue
            Post.objects.create(
                thread=thread,
                author=author,
                content=content,
                floor=thread.reply_count + 1,
            )
            Thread.objects.filter(pk=thread.pk).update(
                reply_count=thread.reply_count + 1, last_activity_at=timezone.now()
            )
            thread.refresh_from_db()
            created_replies += 1
        self.stdout.write(f"  回复 {created_replies} 条")

        # 5. 点赞 / 收藏 / 关注
        thread_ct = ContentType.objects.get_for_model(Thread)
        for thread in threads[:3]:
            for username in ("zhangsan", "lisi", "wangwu"):
                Like.objects.get_or_create(
                    user=users[username], content_type=thread_ct, object_id=thread.pk
                )
        Favorite.objects.get_or_create(user=users["zhangsan"], thread=threads[0])

        Follow.objects.get_or_create(follower=users["zhangsan"], following=users["admin"])
        Follow.objects.get_or_create(follower=users["lisi"], following=users["admin"])
        Follow.objects.get_or_create(follower=users["admin"], following=users["zhangsan"])

        # 6. 通知
        if not Notification.objects.filter(recipient=users["admin"]).exists():
            Notification.objects.create(
                recipient=users["admin"],
                actor=users["zhangsan"],
                verb=Notification.Verb.REPLY,
                message=f"回复了你的主题《{threads[0].title}》",
                url=threads[0].get_absolute_url(),
            )
            Notification.objects.create(
                recipient=users["admin"],
                actor=users["lisi"],
                verb=Notification.Verb.LIKE,
                message="赞了你的内容",
                url=threads[0].get_absolute_url(),
            )

        self.stdout.write(self.style.SUCCESS("\n演示数据生成完毕！"))
        self.stdout.write("  管理员账号：admin / admin123456")
        self.stdout.write("  普通账号：  zhangsan / test123456")
