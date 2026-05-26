from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Form for registering new users.
    Extends Django's UserCreationForm to include email, name, and phone validation.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "correo@mail.com"}
        ),
        label=_("Email address"),
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Jhon"}),
        label=_("First Name"),
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Doe"}),
        label=_("Last Name"),
    )

    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "5547185241"}
        ),
        label=_("Phone Number"),
    )

    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        label=_("Account Type"),
    )

    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("I accept the terms and conditions"),
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "user_type",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to default fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "user_name"}
        )
        self.fields["username"].help_text = _("Only letters, numbers, and @/./+/-/_")

    def clean_email(self):
        """Validate that the email is not already registered."""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email address is already registered."))
        return email

    def save(self, commit=True):
        """
        Save the user instance.
        Note: UserCreationForm.save() handles password hashing automatically.
        """
        user = super().save(commit=False)

        # Explicitly save extra fields not in Meta (though they are in cleaned_data)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone = self.cleaned_data.get("phone", "")
        user.user_type = self.cleaned_data["user_type"]

        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Form for editing user account details (excluding password).
    """

    password = None

    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "phone", "user_type")

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "user_type": forms.Select(
                attrs={"class": "form-select"}
            ),  # 'form-select' for Bootstrap dropdowns
        }


class CustomUserLoginForm(forms.Form):
    """
    Authentication form allowing login via Username OR Email.
    """

    email_or_username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Email or username"),
                "autofocus": True,
            }
        ),
        label=_("Email or Username"),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Password")}
        ),
        label=_("Password"),
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Remember me"),
    )

    def clean(self):
        """
        Authenticate the user against the database.
        Checks for deactivated accounts before authenticating.
        """
        email_or_username = self.cleaned_data.get("email_or_username")
        password = self.cleaned_data.get("password")

        if email_or_username and password:
            # 1. Resolve user object by username or email
            user_obj = None
            try:
                user_obj = CustomUser.objects.get(username=email_or_username)
            except CustomUser.DoesNotExist:
                try:
                    user_obj = CustomUser.objects.get(email=email_or_username)
                except CustomUser.DoesNotExist:
                    pass

            # 2. If user exists but is inactive, show "account doesn't exist"
            if user_obj is not None and not user_obj.is_active:
                raise forms.ValidationError(
                    _("The account doesn't exist.")
                )

            # 3. Authenticate (checks password)
            if user_obj is not None:
                self.user = authenticate(
                    username=user_obj.username, password=password
                )
            else:
                self.user = None

            # 4. If authenticate returned None, credentials are wrong
            if self.user is None:
                raise forms.ValidationError(
                    _("Invalid email/username or password.")
                )

        return self.cleaned_data

    def get_user(self):
        """Helper to retrieve the authenticated user object."""
        return getattr(self, "user", None)


class UserProfileForm(forms.ModelForm):
    """
    Form for updating the extended UserProfile (Bio, Avatar, etc).
    """

    class Meta:
        model = UserProfile
        fields = ("bio", "profile_picture", "newsletter_subscribed")

        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Tell us about yourself (optional)"),
                }
            ),
            "profile_picture": forms.FileInput(attrs={"class": "form-control"}),
            "newsletter_subscribed": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

        labels = {
            "bio": _("Biography"),
            "profile_picture": _("Profile Picture"),
            "newsletter_subscribed": _("Subscribe to newsletter"),
        }


class DeactivateAccountForm(forms.Form):
    """Form requiring password confirmation to deactivate the account."""

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Enter your password")}
        ),
        label=_("Current Password"),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Incorrect password."))
        return password
