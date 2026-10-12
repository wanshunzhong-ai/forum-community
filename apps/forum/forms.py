"""论坛表单：发帖、回复、举报。"""
from django import forms

from .models import Post, Tag, Thread


class ThreadForm(forms.ModelForm):
    """发布 / 编辑主题。标签用逗号或空格分隔。"""

    tags_input = forms.CharField(
        label="标签",
        required=False,
        help_text="用空格或逗号分隔，最多 5 个，例如：Python 求助",
    )

    class Meta:
        model = Thread
        fields = ("category", "title", "body")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "一句话说清你的主题"}),
            "body": forms.Textarea(
                attrs={"rows": 12, "placeholder": "详细描述你的内容…（支持 Markdown 语法）"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "请选择版块"
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "input")

    def save_tags(self, thread):
        raw = (self.cleaned_data.get("tags_input") or "").replace("，", ",").replace(" ", ",")
        names = [n.strip() for n in raw.split(",") if n.strip()][:5]
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(name=name[:30])
            tags.append(tag)
        thread.tags.set(tags)


class ReplyForm(forms.ModelForm):
    """回复。"""

    class Meta:
        model = Post
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5, "placeholder": "写下你的回复…"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content"].widget.attrs.setdefault("class", "input")


class ReportForm(forms.Form):
    """举报表单。"""

    reason = forms.CharField(
        label="举报理由",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "请描述具体情况，方便管理员判断"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget.attrs.setdefault("class", "input")
