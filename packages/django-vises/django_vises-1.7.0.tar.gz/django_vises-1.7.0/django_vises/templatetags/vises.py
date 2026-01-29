import re
from datetime import datetime
from json import dumps as json_dumps

from django import template

register = template.Library()


@register.filter(is_safe=True)
def digitcomma(value):
    """
    Convert an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.

    - 基于 django.contrib.humanize 重新实现了一个 tempalte filter
    - 解决 USE_L10N = True 后这个 intcomma filter 不工作的问题
    - 使用 digitcomma 这个新名字已避免与 humanize 内的发生冲突
    """
    orig = str(value)
    new = re.sub(r"^(-?\d+)(\d{3})", r"\g<1>,\g<2>", orig)
    if orig == new:
        return new
    else:
        return digitcomma(new)


@register.filter
def json(value):
    return json_dumps(value)


@register.filter("startswith")
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter("datetime_ss")
def datetime_simple_short(value: datetime):
    if value is None:
        return ""

    value = value.astimezone()
    return value.strftime("%m/%d %H:%M")
