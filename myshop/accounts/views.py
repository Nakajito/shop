import base64
import io
import logging

import qrcode
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django_otp import user_has_device
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.forms import (
    CustomUserChangeForm,
    CustomUserCreationForm,
    CustomUserLoginForm,
    DeactivateAccountForm,
    UserProfileForm,
)
from accounts.models import CustomUser
from accounts.utils import is_google_oauth_configured
from myshop.utils import safe_next_url

security_logger = logging.getLogger("security")


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

    context = {
        "form": form,
        "page_title": _("Create New Account"),
        "google_oauth_enabled": is_google_oauth_configured(),
    }
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
        form = CustomUserLoginForm(request.POST, request=request)

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

                # Redirect to validated 'next' or default profile (open-redirect safe)
                return redirect(safe_next_url(request, "accounts:profile"))

    else:
        form = CustomUserLoginForm()

    context = {
        "form": form,
        "page_title": _("Log in"),
        "google_oauth_enabled": is_google_oauth_configured(),
    }
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

    favorites_count = user.favorites.count()

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
        "favorites_count": favorites_count,
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
    Self-service downgrade to a regular account.

    Wholesaler accounts are not self-assignable: only staff can grant
    ``UserTypes.WHOLESALER`` (via the Django admin), after review, to prevent
    unvetted users from unlocking wholesaler-only pricing/catalog.
    """
    new_type = request.POST.get("user_type")

    if new_type == CustomUser.UserTypes.REGULAR.value:
        request.user.user_type = new_type
        request.user.save()
        messages.success(
            request,
            _("User type changed to {type}").format(
                type=request.user.get_user_type_display()
            ),
        )
    elif new_type == CustomUser.UserTypes.WHOLESALER.value:
        security_logger.warning(
            f"User {request.user.id} ({request.user.username}) attempted to "
            "self-assign the wholesaler user_type."
        )
        messages.error(
            request,
            _(
                "Wholesaler accounts are granted by our team after review. "
                "Please use the wholesaler contact form to request access."
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
        security_logger.info(f"User {user.id} ({user.username}) deactivated their account.")
        logout(request)
        messages.success(request, _("Your account has been successfully deleted."))
        return redirect("shop:product_list")

    messages.error(request, _("Incorrect password. Account was not deleted."))
    return redirect("accounts:profile")


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def mfa_setup(request):
    """
    Staff-only TOTP enrollment (A07 — see SECURITY.md).

    Not staff-gated behind /admin/: enrollment must work while
    MFA_ENFORCE_STAFF is still off, so staff can set up a device before
    enforcement is turned on (django-otp's OTPAdminSite has no bypass for
    staff with zero devices — enrolling first avoids locking anyone out).
    """
    if not request.user.is_staff:
        raise Http404

    user = request.user
    context = {}

    if user_has_device(user, confirmed=True):
        context["already_enabled"] = True
        return render(request, "accounts/mfa_setup.html", context)

    device = TOTPDevice.objects.filter(user=user, confirmed=False).first()

    if request.method == "POST":
        token = request.POST.get("token", "")
        if device is not None and device.verify_token(token):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            security_logger.info(f"User {user.id} ({user.username}) enabled TOTP MFA.")
            messages.success(request, _("La autenticación en dos pasos ya está activada."))
            return redirect("accounts:profile")
        messages.error(request, _("Código inválido. Intenta de nuevo."))

    if device is None:
        device = TOTPDevice.objects.create(user=user, confirmed=False, name="default")

    qr_image = qrcode.make(device.config_url)
    buffer = io.BytesIO()
    qr_image.save(buffer, format="PNG")
    context["qr_data_uri"] = "data:image/png;base64," + base64.b64encode(
        buffer.getvalue()
    ).decode("ascii")
    context["secret"] = device.key
    return render(request, "accounts/mfa_setup.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def mfa_disable(request):
    """Removes the user's confirmed TOTP device. Requires password confirmation
    (same pattern as deactivate_account) since this lowers account security."""
    if not request.user.is_staff:
        raise Http404

    form = DeactivateAccountForm(request.user, request.POST)

    if form.is_valid():
        TOTPDevice.objects.filter(user=request.user).delete()
        security_logger.info(
            f"User {request.user.id} ({request.user.username}) disabled TOTP MFA."
        )
        messages.success(request, _("Se desactivó la autenticación en dos pasos."))
    else:
        messages.error(
            request,
            _("Contraseña incorrecta. No se desactivó la autenticación en dos pasos."),
        )

    return redirect("accounts:mfa_setup")


@require_http_methods(["GET"])
def google_login(request):
    """
    Redirect to Google OAuth2 login endpoint.
    This path usually comes from django-allauth.
    """
    return redirect("/accounts/google/login/")
