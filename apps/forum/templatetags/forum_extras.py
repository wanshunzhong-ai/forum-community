"""自定义模板过滤器。"""
import bleach
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# 允许保留的 HTML 标签与属性（白名单）
ALLOWED_TAGS = [
    "p", "br", "strong", "em", "del", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img", "hr", "table", "thead", "tbody", "tr", "th", "td",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "code": ["class"],
}


@register.filter(name="markdownify")
def markdownify(text):
    """把 Markdown 文本渲染成 HTML，并做安全过滤（防止 XSS）。"""
    if not text:
        return ""
    html = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return mark_safe(clean)
