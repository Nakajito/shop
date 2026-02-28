from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    # Public views
    path("", views.post_list, name="post_list"),
    path(
        "category/<slug:category_slug>/",
        views.post_list,
        name="post_list_by_category",
    ),
    path("tag/<slug:tag_slug>/", views.post_list, name="post_list_by_tag"),
    path("post/<slug:slug>/", views.post_detail, name="post_detail"),
    # Staff management panel
    path("manage/", views.manage_dashboard, name="manage_dashboard"),
    path("manage/posts/", views.manage_post_list, name="manage_post_list"),
    path("manage/posts/create/", views.manage_post_create, name="manage_post_create"),
    path(
        "manage/posts/<int:post_id>/edit/",
        views.manage_post_edit,
        name="manage_post_edit",
    ),
    path(
        "manage/posts/<int:post_id>/delete/",
        views.manage_post_delete,
        name="manage_post_delete",
    ),
    # AJAX endpoints
    path(
        "manage/ajax/create-category/",
        views.ajax_create_category,
        name="ajax_create_category",
    ),
    path(
        "manage/ajax/create-tag/",
        views.ajax_create_tag,
        name="ajax_create_tag",
    ),
]
