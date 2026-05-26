from django.contrib import admin

from blog.models import Category, Post, PostImage, PostVideo, Tag


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


class PostVideoInline(admin.TabularInline):
    model = PostVideo
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created")
    list_filter = ("status", "category", "created")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("author",)
    date_hierarchy = "created"
    inlines = [PostImageInline, PostVideoInline]
