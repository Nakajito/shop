from django import template

from blog.models import Category, Post, Tag

register = template.Library()


@register.simple_tag
def recent_posts(count=5):
    """Return the N most recent published posts."""
    return Post.objects.published().with_relations()[:count]


@register.simple_tag
def blog_categories():
    """Return all blog categories."""
    return Category.objects.all()


@register.simple_tag
def blog_tags():
    """Return all blog tags."""
    return Tag.objects.all()
