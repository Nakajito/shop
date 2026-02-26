from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from accounts.forms import (
    CustomUserCreationForm,
    CustomUserLoginForm,
    CustomUserChangeForm,
    UserProfileForm,
    DeactivateAccountForm,
)
from accounts.models import CustomUser


@require_http_methods(["GET", "POST"])
def register(request):
    """
    New user registration view.
    GET: Displays registration form.
    POST: Processes data, creates new user, and logs them in automatically.
    """
    if request.user.is_authenticated:
        messages.info(request, _("You are already registered."))
        return redirect("shop:product_list")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user (password is hashed automatically by form.save)
                    user = form.save()

                    # The CustomUser signal automatically creates the UserProfile.

                    # Authenticate and log in the user
                    # We need to retrieve the raw password from cleaned_data to authenticate
                    username = form.cleaned_data.get("username")
                    # Note: UserCreationForm standardizes on 'password' or checks matching,
                    # but typically doesn't include 'password1' in cleaned_data unless custom.
                    # Since we customized the form, we check our specific fields.
                    # If using standard AuthenticationForm logic, accessing the user object directly is easier:
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                    messages.success(
                        request,
                        _(
                            "Welcome {name}! Your account has been successfully created."
                        ).format(name=user.first_name),
                    )
                    return redirect("accounts:profile")

            except Exception as e:
                # Catch unexpected errors during the transaction
                messages.error(
                    request, _("Error creating account: {error}").format(error=str(e))
                )
    else:
        form = CustomUserCreationForm()

    context = {"form": form, "page_title": _("Create New Account")}
    return render(request, "accounts/register.html", context)


@require_http_methods(["GET", "POST"])
def user_login(request):
    """
    User login view.
    GET: Displays login form.
    POST: Authenticates user and creates session.
    """
    if request.user.is_authenticated:
        messages.info(request, _("You are already logged in."))
        return redirect("shop:product_list")

    if request.method == "POST":
        form = CustomUserLoginForm(request.POST)

        if form.is_valid():
            user = form.get_user()

            if user is not None:
                login(request, user)

                # "Remember me" functionality
                if form.cleaned_data.get("remember_me"):
                    # Set session expiry to 2 weeks (1,209,600 seconds)
                    request.session.set_expiry(1209600)

                messages.success(
                    request, _("Welcome back, {name}!").format(name=user.first_name)
                )

                # Redirect to 'next' parameter or default profile
                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)
                return redirect("accounts:profile")

    else:
        form = CustomUserLoginForm()

    context = {"form": form, "page_title": _("Log in")}
    return render(request, "accounts/login.html", context)


@require_http_methods(["POST"])
def user_logout(request):
    """
    View to log out.
    Only accepts POST for security (prevents CSRF attacks via GET links).
    """
    logout(request)
    messages.success(request, _("Session closed successfully."))
    return redirect("shop:product_list")


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def profile(request):
    """
    User profile view.
    GET: Display profile dashboard and edit forms.
    POST: Update user and profile information simultaneously.
    """
    user = request.user
    # Ensure profile exists to avoid crash if signal failed previously (defensive coding)
    if not hasattr(user, "profile"):
        from accounts.models import UserProfile

        UserProfile.objects.create(user=user)

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
                    messages.success(request, _("Profile successfully updated."))
                    return redirect("accounts:profile")

            except Exception as e:
                messages.error(
                    request, _("Error updating profile: {error}").format(error=str(e))
                )

    else:
        user_form = CustomUserChangeForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)

    # Context data for the dashboard
    # Use 'all()' and let the template slice or use DB slicing here
    recent_orders = user.orders.select_related("payment_method").order_by("-created")[:5]

    # Use defensive checks for related managers in case apps aren't connected yet
    addresses_count = user.addresses.count() if hasattr(user, "addresses") else 0
    # Assuming 'payment_methods' is the related_name from the Payment app
    payment_methods_count = (
        getattr(user, "payment_methods", None).count()
        if hasattr(user, "payment_methods")
        else 0
    )

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "recent_orders": recent_orders,
        "addresses_count": addresses_count,
        "payment_methods_count": payment_methods_count,
        "page_title": _("My Profile"),
    }

    return render(request, "accounts/profile.html", context)


@login_required(login_url="accounts:login")
def profile_details(request):
    """
    Profile details view (read-only).
    Displays summary information about the user.
    """
    context = {"user": request.user, "page_title": _("Profile Details")}
    return render(request, "accounts/profile_details.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def change_user_type(request):
    """
    View to switch between normal user and wholesaler.
    """
    new_type = request.POST.get("user_type")

    # Validate against the TextChoices values defined in the model
    if new_type in CustomUser.UserTypes.values:
        request.user.user_type = new_type
        request.user.save()
        messages.success(
            request,
            _("User type changed to {type}").format(
                type=request.user.get_user_type_display()
            ),
        )
    else:
        messages.error(request, _("Invalid user type."))

    return redirect("accounts:profile")


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def deactivate_account(request):
    """
    Soft-delete: sets is_active=False and logs the user out.
    Requires password confirmation via POST data.
    """
    form = DeactivateAccountForm(request.user, request.POST)

    if form.is_valid():
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        logout(request)
        messages.success(request, _("Your account has been successfully deleted."))
        return redirect("shop:product_list")

    messages.error(request, _("Incorrect password. Account was not deleted."))
    return redirect("accounts:profile")


@require_http_methods(["GET"])
def google_login(request):
    """
    Redirect to Google OAuth2 login endpoint.
    This path usually comes from django-allauth.
    """
    return redirect("/accounts/google/login/")
