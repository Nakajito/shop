from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from accounts.models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Form for registering new users.
    Extends Django's UserCreationForm with custom fields.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "correo@mail.com"}
        ),
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Jhon"}),
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Doe"}),
    )

    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "5547185241"}
        ),
    )

    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Minimum 8 characters"}
        ),
    )

    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Repeat your password"}
        ),
    )

    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="I accept the terms and conditions",
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
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "user_name"}
        )

        # Mensaje de ayuda personalizado
        self.fields["username"].help_text = "Only letters, numbers, and @/./+/-/_"
        self.fields["password1"].help_text = (
            "Minimum 8 characters, must include letters and numbers"
        )

    def clean_email(self):
        """Validate that the email is not registered"""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean_username(self):
        """Validate that the username is unique"""
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username already exists.")
        return username

    def clean_password2(self):
        """Validate that passwords match"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The passwords do not match.")

        return password2

    def save(self, commit=True):
        """Save the user with the additional data"""
        user = super().save(commit=False)
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
    Form for editing user profiles.
    Extends Django's UserChangeForm.
    """

    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "phone", "user_type")

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "user_type": forms.Select(attrs={"class": "form-control"}),
        }


class CustomUserLoginForm(forms.Form):
    """
    User login form.
    Use email OR username (more user-friendly than just username).
    """

    email_or_username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email or username",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Remember me on this device",
    )

    def clean(self):
        """Validate credentials"""
        email_or_username = self.cleaned_data.get("email_or_username")
        password = self.cleaned_data.get("password")

        if email_or_username and password:
            # Try authenticating by username first
            self.user = authenticate(username=email_or_username, password=password)

            # If that doesn't work, try emailing us.
            if self.user is None:
                try:
                    user = CustomUser.objects.get(email=email_or_username)
                    self.user = authenticate(username=user.username, password=password)
                except CustomUser.DoesNotExist:
                    self.user = None

            # If it still doesn't work, error
            if self.user is None:
                raise forms.ValidationError("Incorrect email/username or password.")

            # Verify that the account is active
            if not self.user.is_active:
                raise forms.ValidationError("This account has been deactivated.")

        return self.cleaned_data

    def get_user(self):
        """Returns the authenticated user"""
        return self.user if hasattr(self, "user") else None


class UserProfileForm(forms.ModelForm):
    """
    Form to edit the user's additional profile.
    """

    class Meta:
        model = UserProfile
        fields = ("bio", "profile_picture", "newsletter_subscribed")

        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Tell us about yourself (optional)",
                }
            ),
            "profile_picture": forms.FileInput(attrs={"class": "form-control"}),
            "newsletter_subscribed": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

        labels = {
            "bio": "Biography",
            "profile_picture": "Profile picture",
            "newsletter_subscribed": "Subscribe to newsletter and promotions",
        }
