from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from blog.managers import PostManager


class Category(models.Model):
    """Blog category, separate from shop categories."""

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("blog category")
        verbose_name_plural = _("blog categories")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:post_list_by_category", args=[self.slug])


class Tag(models.Model):
    """Blog tag for flexible content classification."""

    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:post_list_by_tag", args=[self.slug])


class Post(models.Model):
    """Blog post with rich text content, gallery, and video support."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    title = models.CharField(_("title"), max_length=250)
    subtitle = models.CharField(_("subtitle"), max_length=300, blank=True)
    slug = models.SlugField(_("slug"), max_length=250, unique=True)
    body = CKEditor5Field(_("body"), config_name="default")
    cover_image = models.ImageField(
        _("cover image"),
        upload_to="blog/covers/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        verbose_name=_("author"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name=_("category"),
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="posts",
        verbose_name=_("tags"),
    )
    related_posts = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        verbose_name=_("related posts"),
    )

    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created = models.DateTimeField(_("created"), auto_now_add=True)
    updated = models.DateTimeField(_("updated"), auto_now=True)

    objects = PostManager()

    class Meta:
        ordering = ["-created"]
        verbose_name = _("post")
        verbose_name_plural = _("posts")
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["status", "-created"]),
            models.Index(fields=["author", "-created"]),
            models.Index(fields=["category", "-created"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[self.slug])

    def get_related_or_similar(self, limit=3):
        """
        Return manually selected related posts. If none exist,
        fall back to posts sharing the same category or tags.
        """
        related = self.related_posts.filter(status=self.Status.PUBLISHED)
        if related.exists():
            return related[:limit]

        from django.db.models import Count, Q

        similar = (
            Post.objects.published()
            .exclude(id=self.id)
            .filter(Q(category=self.category) | Q(tags__in=self.tags.all()))
            .annotate(shared_tags=Count("tags"))
            .order_by("-shared_tags", "-created")
            .distinct()[:limit]
        )
        return similar


class PostImage(models.Model):
    """Gallery image attached to a blog post."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("post"),
    )
    image = models.ImageField(
        _("image"),
        upload_to="blog/gallery/%Y/%m/%d/",
    )
    caption = models.CharField(_("caption"), max_length=250, blank=True)
    order = models.PositiveIntegerField(_("order"), default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("post image")
        verbose_name_plural = _("post images")

    def __str__(self):
        return f"Image {self.order} for {self.post.title}"


class PostVideo(models.Model):
    """Video attached to a blog post -- supports YouTube, Vimeo, or file upload."""

    class VideoType(models.TextChoices):
        YOUTUBE = "youtube", _("YouTube")
        VIMEO = "vimeo", _("Vimeo")
        FILE = "file", _("Server Hosted")

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="videos",
        verbose_name=_("post"),
    )
    video_type = models.CharField(
        _("video type"),
        max_length=10,
        choices=VideoType.choices,
    )
    url = models.URLField(
        _("video URL"),
        blank=True,
        help_text=_("YouTube or Vimeo URL"),
    )
    file = models.FileField(
        _("video file"),
        upload_to="blog/videos/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Upload video file for server-hosted videos"),
    )
    title = models.CharField(_("title"), max_length=250, blank=True)
    order = models.PositiveIntegerField(_("order"), default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = _("post video")
        verbose_name_plural = _("post videos")

    def __str__(self):
        return f"{self.get_video_type_display()}: {self.title or self.url}"

    def get_embed_url(self):
        """Convert YouTube/Vimeo URLs to embeddable format."""
        if self.video_type == self.VideoType.YOUTUBE:
            video_id = self._extract_youtube_id()
            if not video_id:
                return self.url
            return f"https://www.youtube.com/embed/{video_id}"
        elif self.video_type == self.VideoType.VIMEO:
            video_id = self.url.rstrip("/").split("/")[-1]
            return f"https://player.vimeo.com/video/{video_id}"
        return self.url

    def _extract_youtube_id(self):
        """Extract video ID from various YouTube URL formats."""
        import re

        patterns = [
            r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"(?:v=)([a-zA-Z0-9_-]{11})",
            r"(?:embed/)([a-zA-Z0-9_-]{11})",
            r"(?:shorts/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.url)
            if match:
                return match.group(1)
        return None
