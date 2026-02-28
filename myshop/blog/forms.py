from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.widgets import CKEditor5Widget

from blog.models import Category, Post, PostImage, PostVideo, Tag


class CategoryForm(forms.ModelForm):
    """Quick form for creating a new blog category inline."""

    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": _("New category name"),
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


class TagForm(forms.ModelForm):
    """Quick form for creating a new blog tag inline."""

    class Meta:
        model = Tag
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": _("New tag name"),
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


class PostForm(forms.ModelForm):
    """Form for creating and editing blog posts in the custom admin panel."""

    class Meta:
        model = Post
        fields = [
            "title",
            "subtitle",
            "slug",
            "body",
            "cover_image",
            "category",
            "tags",
            "related_posts",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Post title"),
                }
            ),
            "subtitle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Optional subtitle"),
                }
            ),
            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("auto-generated-from-title"),
                }
            ),
            "body": CKEditor5Widget(config_name="default"),
            "cover_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.CheckboxSelectMultiple(),
            "related_posts": forms.CheckboxSelectMultiple(),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related_posts"].queryset = Post.objects.published().exclude(
            id=self.instance.id if self.instance.pk else None
        )
        self.fields["category"].empty_label = _("Select a category")
        self.fields["slug"].required = False


class PostImageForm(forms.ModelForm):
    """Form for adding images to a post gallery."""

    class Meta:
        model = PostImage
        fields = ["image", "caption", "order"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "caption": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Image caption"),
                }
            ),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class PostVideoForm(forms.ModelForm):
    """Form for adding videos to a post."""

    class Meta:
        model = PostVideo
        fields = ["video_type", "url", "file", "title", "order"]
        widgets = {
            "video_type": forms.Select(attrs={"class": "form-select"}),
            "url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("https://youtube.com/watch?v=..."),
                }
            ),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Video title"),
                }
            ),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


PostImageFormSet = forms.inlineformset_factory(
    Post,
    PostImage,
    form=PostImageForm,
    extra=0,
    can_delete=True,
)

PostVideoFormSet = forms.inlineformset_factory(
    Post,
    PostVideo,
    form=PostVideoForm,
    extra=0,
    can_delete=True,
)
