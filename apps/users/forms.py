"""用户相关的表单（注册、资料编辑）。"""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    """注册表单：用户名 + 邮箱 + 昵称 + 两次密码。"""

    email = forms.EmailField(label="邮箱", required=True)
    nickname = forms.CharField(label="昵称", max_length=40, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "nickname")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给所有输入框加上统一的 CSS 类
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")
        self.fields["username"].label = "用户名"
        self.fields["password1"].label = "密码"
        self.fields["password2"].label = "确认密码"

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("这个邮箱已经被注册过了")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.nickname = self.cleaned_data.get("nickname") or ""
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """编辑个人资料。"""

    class Meta:
        model = User
        fields = ("nickname", "avatar", "bio", "location", "website", "email")
        widgets = {
            "bio": forms.TextInput(attrs={"placeholder": "一句话介绍自己"}),
            "website": forms.URLInput(attrs={"placeholder": "https://"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.setdefault("class", "input")
