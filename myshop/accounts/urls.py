from django.urls import path
from django.views.generic import RedirectView
from accounts import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("auth/google/login/", views.google_login, name="google_login"),
    # Legacy allauth provider path used earlier by some templates/tests.
    # Redirect `/accounts/social/google/login/` -> `/accounts/google/login/`.
    path(
        "social/google/login/",
        RedirectView.as_view(url="/accounts/google/login/", permanent=False),
        name="google_login_legacy",
    ),
    # Profile
    path("profile/", views.profile, name="profile"),
    path("profile/details/", views.profile_details, name="profile_details"),
    path("profile/change-user-type/", views.change_user_type, name="change_user_type"),
]
