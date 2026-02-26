from django.urls import path
from django.views.generic import RedirectView
from accounts import views

"""
URL Configuration for the 'accounts' application.

This module defines the URL patterns for user authentication (registration, login, logout),
social authentication (Google), and user profile management.

Namespace:
    app_name = "accounts"

Key Endpoints:
    - /register/: User registration page.
    - /login/: User login page.
    - /logout/: Logs out the user.
    - /auth/google/login/: Initiates Google OAuth login flow.
    - /profile/: Main dashboard/profile view for the user.
"""

app_name = "accounts"

urlpatterns = [
    # --- Authentication ---
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    # --- Social Authentication ---
    path("google-login/", views.google_login, name="google_login"),
    # --- Profile Management ---
    path("profile/", views.profile, name="profile"),
    path("profile/details/", views.profile_details, name="profile_details"),
    path("profile/change-user-type/", views.change_user_type, name="change_user_type"),
    path("profile/deactivate/", views.deactivate_account, name="deactivate_account"),
]
