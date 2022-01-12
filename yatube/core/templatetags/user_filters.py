from django import template

# В template.Library зарегистрированы все встроенные теги и фильтры шаблонов;
# добавляем к ним и наш фильтр.

from posts.models import Like

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def like_filter(value, arg):
    return (arg.is_authenticated and
            Like.objects.filter(post=value, user=arg))
