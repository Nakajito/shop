from django.urls import path
from accounts import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    # Profile
    path("profile/", views.profile, name="profile"),
    path("profile/details/", views.profile_details, name="profile_details"),
    path("profile/change-user-type/", views.change_user_type, name="change_user_type"),
]
