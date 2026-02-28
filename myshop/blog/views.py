import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from blog.forms import CategoryForm, PostForm, PostImageFormSet, PostVideoFormSet, TagForm
from blog.models import Category, Post, Tag

logger = logging.getLogger(__name__)


# ============================================================
# PUBLIC VIEWS
# ============================================================


@require_http_methods(["GET"])
def post_list(request, category_slug=None, tag_slug=None):
    """List published blog posts with filtering by category, tag, date, and search."""
    posts = Post.objects.published().with_relations()
    categories = Category.objects.annotate(
        post_count=Count("posts", filter=Q(posts__status="published"))
    )
    tags = Tag.objects.annotate(
        post_count=Count("posts", filter=Q(posts__status="published"))
    )

    category = None
    tag = None

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(category=category)

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags=tag)

    year = request.GET.get("year")
    month = request.GET.get("month")
    if year:
        posts = posts.filter(created__year=year)
    if month:
        posts = posts.filter(created__month=month)

    search_query = request.GET.get("q")
    if search_query:
        posts = posts.search(search_query)

    paginator = Paginator(posts, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "posts": page_obj,
        "categories": categories,
        "tags": tags,
        "current_category": category,
        "current_tag": tag,
        "search_query": search_query or "",
        "page_title": _("Blog"),
    }
    return render(request, "blog/post_list.html", context)


@require_http_methods(["GET"])
def post_detail(request, slug):
    """Display a single published blog post with gallery, videos, and related posts."""
    post = get_object_or_404(
        Post.objects.with_relations().prefetch_related("images", "videos"),
        slug=slug,
        status=Post.Status.PUBLISHED,
    )
    related_posts = post.get_related_or_similar(limit=3)

    context = {
        "post": post,
        "related_posts": related_posts,
        "page_title": post.title,
    }
    return render(request, "blog/post_detail.html", context)


# ============================================================
# MANAGEMENT VIEWS (staff only)
# ============================================================


@staff_member_required(login_url="accounts:login")
@require_http_methods(["GET"])
def manage_dashboard(request):
    """Blog management dashboard with post statistics."""
    stats = {
        "total": Post.objects.count(),
        "published": Post.objects.published().count(),
        "drafts": Post.objects.drafts().count(),
    }
    recent_posts = Post.objects.with_relations().order_by("-created")[:5]

    context = {
        "stats": stats,
        "recent_posts": recent_posts,
        "page_title": _("Blog Dashboard"),
    }
    return render(request, "blog/manage/dashboard.html", context)


@staff_member_required(login_url="accounts:login")
@require_http_methods(["GET"])
def manage_post_list(request):
    """List all posts with search and status filter."""
    posts = Post.objects.with_relations()

    status_filter = request.GET.get("status")
    if status_filter in ["draft", "published"]:
        posts = posts.filter(status=status_filter)

    search_query = request.GET.get("q")
    if search_query:
        posts = posts.search(search_query)

    paginator = Paginator(posts, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "posts": page_obj,
        "current_status": status_filter,
        "search_query": search_query or "",
        "page_title": _("Manage Posts"),
    }
    return render(request, "blog/manage/post_list.html", context)


@staff_member_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def manage_post_create(request):
    """Create a new blog post with images and videos."""
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        image_formset = PostImageFormSet(request.POST, request.FILES, prefix="images")
        video_formset = PostVideoFormSet(request.POST, request.FILES, prefix="videos")

        if form.is_valid() and image_formset.is_valid() and video_formset.is_valid():
            try:
                with transaction.atomic():
                    post = form.save(commit=False)
                    post.author = request.user
                    if not post.slug:
                        post.slug = slugify(post.title)
                    post.save()
                    form.save_m2m()

                    image_formset.instance = post
                    image_formset.save()

                    video_formset.instance = post
                    video_formset.save()

                messages.success(request, _("Post created successfully."))
                return redirect("blog:manage_post_list")
            except Exception as e:
                logger.error(f"Error creating blog post: {e}")
                messages.error(
                    request, _("An error occurred while creating the post.")
                )
    else:
        form = PostForm()
        image_formset = PostImageFormSet(prefix="images")
        video_formset = PostVideoFormSet(prefix="videos")

    context = {
        "form": form,
        "image_formset": image_formset,
        "video_formset": video_formset,
        "category_form": CategoryForm(),
        "tag_form": TagForm(),
        "page_title": _("Create Post"),
    }
    return render(request, "blog/manage/post_form.html", context)


@staff_member_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def manage_post_edit(request, post_id):
    """Edit an existing blog post with its images and videos."""
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        image_formset = PostImageFormSet(
            request.POST, request.FILES, instance=post, prefix="images"
        )
        video_formset = PostVideoFormSet(
            request.POST, request.FILES, instance=post, prefix="videos"
        )

        if form.is_valid() and image_formset.is_valid() and video_formset.is_valid():
            try:
                with transaction.atomic():
                    post = form.save()
                    image_formset.save()
                    video_formset.save()
                messages.success(request, _("Post updated successfully."))
                return redirect("blog:manage_post_list")
            except Exception as e:
                logger.error(f"Error updating blog post {post_id}: {e}")
                messages.error(
                    request, _("An error occurred while updating the post.")
                )
    else:
        form = PostForm(instance=post)
        image_formset = PostImageFormSet(instance=post, prefix="images")
        video_formset = PostVideoFormSet(instance=post, prefix="videos")

    context = {
        "form": form,
        "post": post,
        "image_formset": image_formset,
        "video_formset": video_formset,
        "category_form": CategoryForm(),
        "tag_form": TagForm(),
        "page_title": _("Edit Post: %(title)s") % {"title": post.title},
    }
    return render(request, "blog/manage/post_form.html", context)


@staff_member_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def manage_post_delete(request, post_id):
    """Delete a blog post with confirmation."""
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        title = post.title
        post.delete()
        messages.success(
            request, _("Post '%(title)s' deleted successfully.") % {"title": title}
        )
        return redirect("blog:manage_post_list")

    context = {
        "post": post,
        "page_title": _("Delete Post: %(title)s") % {"title": post.title},
    }
    return render(request, "blog/manage/post_confirm_delete.html", context)


# ============================================================
# AJAX ENDPOINTS (staff only)
# ============================================================


@staff_member_required(login_url="accounts:login")
@require_POST
def ajax_create_category(request):
    """Create a new category via AJAX and return its id/name."""
    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"error": _("Name is required.")}, status=400)

    slug = slugify(name)
    if Category.objects.filter(slug=slug).exists():
        cat = Category.objects.get(slug=slug)
        return JsonResponse({"id": cat.id, "name": cat.name, "exists": True})

    cat_form = CategoryForm({"name": name})
    if cat_form.is_valid():
        category = cat_form.save()
        return JsonResponse({"id": category.id, "name": category.name, "exists": False})

    return JsonResponse({"error": cat_form.errors}, status=400)


@staff_member_required(login_url="accounts:login")
@require_POST
def ajax_create_tag(request):
    """Create a new tag via AJAX and return its id/name."""
    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"error": _("Name is required.")}, status=400)

    slug = slugify(name)
    if Tag.objects.filter(slug=slug).exists():
        tag = Tag.objects.get(slug=slug)
        return JsonResponse({"id": tag.id, "name": tag.name, "exists": True})

    tag_form = TagForm({"name": name})
    if tag_form.is_valid():
        tag = tag_form.save()
        return JsonResponse({"id": tag.id, "name": tag.name, "exists": False})

    return JsonResponse({"error": tag_form.errors}, status=400)
