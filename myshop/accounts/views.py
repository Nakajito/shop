from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from accounts.forms import (
    CustomUserCreationForm,
    CustomUserLoginForm,
    CustomUserChangeForm,
    UserProfileForm,
)
from accounts.models import CustomUser, UserProfile


@require_http_methods(["GET", "POST"])
def register(request):
    """
    New user registration view.
    GET: Displays registration form
    POST: Processes data and creates new user
    """

    if request.user.is_authenticated:
        messages.info(request, "You are already registered.")
        return redirect("shop:product_list")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = form.save()

                    # The CustomUser signal automatically creates the UserProfile.

                    # Automatically authenticate and log in
                    username = form.cleaned_data.get("username")
                    password = form.cleaned_data.get("password1")
                    user = authenticate(username=username, password=password)

                    if user is not None:
                        login(request, user)
                        messages.success(
                            request,
                            f"Welcome {user.first_name}! Your account has been successfully created.",
                        )
                        return redirect("accounts:profile")

            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
    else:
        form = CustomUserCreationForm()

    context = {"form": form, "page_title": "Create New Account"}
    return render(request, "accounts/register.html", context)


@require_http_methods(["GET", "POST"])
def user_login(request):
    """
    User login view.
    GET: Displays login form.
    POST: Authenticates user and creates session.
    """

    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect("shop:product_list")

    if request.method == "POST":
        form = CustomUserLoginForm(request.POST)

        if form.is_valid():
            user = form.get_user()

            if user is not None:
                login(request, user)

                # If you checked “remember me,” long session
                if form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(1209600)  # 2 semanas

                messages.success(request, f"¡Bienvenido {user.first_name}!")

                # Redirect to next page or profile
                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)
                return redirect("accounts:profile")

    else:
        form = CustomUserLoginForm()

    context = {"form": form, "page_title": "Log in"}
    return render(request, "accounts/login.html", context)


@require_http_methods(["POST"])
def user_logout(request):
    """
    View to log out.
    Only accepts POST for security.
    """
    logout(request)
    messages.success(request, "Session closed successfully.")
    return redirect("shop:product_list")


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def profile(request):
    """
    User profile view.
    GET: Display profile and forms
    POST: Update user information
    """
    user = request.user
    user_profile = user.profile

    if request.method == "POST":
        user_form = CustomUserChangeForm(request.POST, instance=user)
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=user_profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                    messages.success(request, "Profile successfully updated.")
                    return redirect("accounts:profile")

            except Exception as e:
                messages.error(request, f"Error updating profile: {str(e)}")

    else:
        user_form = CustomUserChangeForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)

    # Get data to display
    recent_orders = user.orders.all()[:5]
    addresses_count = user.addresses.count()
    payment_methods_count = user.payment_methods.count()

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "recent_orders": recent_orders,
        "addresses_count": addresses_count,
        "payment_methods_count": payment_methods_count,
        "page_title": "My Profile",
    }

    return render(request, "accounts/profile.html", context)


@login_required(login_url="accounts:login")
def profile_details(request):
    """
    Profile details view (read-only).
    Displays summary information about the user.
    """
    user = request.user

    context = {"user": user, "page_title": "Profile Details"}

    return render(request, "accounts/profile_details.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def change_user_type(request):
    """
    View to switch between normal user and wholesaler.
    POST only for security.
    """
    new_type = request.POST.get("user_type")

    if new_type in dict(CustomUser.USER_TYPE_CHOICES):
        request.user.user_type = new_type
        request.user.save()
        messages.success(
            request,
            f"User type changed to {request.user.get_user_type_display()}",
        )
    else:
        messages.error(request, "Invalid user type.")

    return redirect("accounts:profile")
