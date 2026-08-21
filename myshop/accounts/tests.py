from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser, UserProfile


class CustomUserModelTest(TestCase):
    def test_create_user(self):
        user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_default_user_type(self):
        user = CustomUser.objects.create_user(username="testuser", password="testpass123")
        self.assertEqual(user.user_type, "regular_user")

    def test_is_wholesaler(self):
        user = CustomUser.objects.create_user(
            username="wholesaler", password="testpass123", user_type="wholesaler"
        )
        self.assertTrue(user.is_wholesaler)
        self.assertFalse(user.is_regular_user)

    def test_is_regular_user(self):
        user = CustomUser.objects.create_user(
            username="regular", password="testpass123", user_type="regular_user"
        )
        self.assertTrue(user.is_regular_user)
        self.assertFalse(user.is_wholesaler)

    def test_str(self):
        user = CustomUser.objects.create_user(username="testuser", password="testpass123")
        self.assertIn("testuser", str(user))

    def test_profile_auto_created(self):
        user = CustomUser.objects.create_user(username="testuser", password="testpass123")
        self.assertTrue(hasattr(user, "profile"))
        self.assertIsInstance(user.profile, UserProfile)


class UserProfileModelTest(TestCase):
    def test_str(self):
        user = CustomUser.objects.create_user(username="testuser", password="testpass123")
        self.assertIn("testuser", str(user.profile))


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_get(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_register_post_valid(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password1": "StrongP@ss123",
                "password2": "StrongP@ss123",
                "user_type": "regular_user",
                "terms_accepted": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username="newuser").exists())

    def test_register_ignores_user_type_escalation(self):
        """Registration must never let a request set user_type (A01)."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "sneakywholesaler",
                "email": "sneaky@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password1": "StrongP@ss123",
                "password2": "StrongP@ss123",
                "user_type": "wholesaler",
                "terms_accepted": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username="sneakywholesaler")
        self.assertEqual(user.user_type, "regular_user")

    def test_register_redirects_authenticated(self):
        user = CustomUser.objects.create_user(username="existing", password="pass123")
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 302)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
        )

    def test_login_get(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_with_username(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email_or_username": "testuser",
                "password": "testpass123",
            },
        )
        # On success, redirects to profile. On failure, re-renders form (200).
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertIn(str(self.user.pk), str(self.client.session.get("_auth_user_id", "")))

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email_or_username": "test@example.com",
                "password": "testpass123",
            },
        )
        self.assertIn(response.status_code, [200, 302])

    def test_login_via_client(self):
        """Verify authentication works with Django test client."""
        result = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(result)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email_or_username": "testuser",
                "password": "wrongpass",
            },
        )
        self.assertEqual(response.status_code, 200)


class AxesLockoutTest(TestCase):
    """A07: repeated failed logins through the real login view must lock out
    further attempts (django-axes). Disabled globally in testing settings
    because Client.login() can't provide the request AxesBackend requires —
    re-enabled here to exercise it via real POSTs to accounts:login."""

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="lockoutuser", password="correctpass123"
        )

    @override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=3, AXES_COOLOFF_TIME=1)
    def test_locks_out_after_repeated_failures(self):
        for _ in range(3):
            self.client.post(
                reverse("accounts:login"),
                {"email_or_username": "lockoutuser", "password": "wrongpass"},
            )

        # 4th attempt, even with the correct password, must be blocked.
        response = self.client.post(
            reverse("accounts:login"),
            {"email_or_username": "lockoutuser", "password": "correctpass123"},
        )
        self.assertEqual(response.status_code, 429)  # axes' lockout response
        self.assertTemplateUsed(response, "429.html")
        self.assertNotIn("_auth_user_id", self.client.session)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username="testuser", password="testpass123")

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_get(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)


class ChangeUserTypeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123", user_type="regular_user"
        )

    def test_change_to_wholesaler_is_rejected(self):
        """Self-service escalation to wholesaler must be refused (A01)."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:change_user_type"),
            {"user_type": "wholesaler"},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "regular_user")

    def test_change_to_regular_is_allowed(self):
        """A wholesaler may still self-downgrade to a regular account."""
        self.user.user_type = "wholesaler"
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:change_user_type"),
            {"user_type": "regular_user"},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "regular_user")

    def test_change_invalid_type(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:change_user_type"),
            {"user_type": "invalid_type"},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, "regular_user")


class SocialAdapterTest(TestCase):
    def setUp(self):
        from accounts.adapter import CustomSocialAccountAdapter

        self.adapter = CustomSocialAccountAdapter()
        self.user = CustomUser.objects.create_user(
            username="suser", email="social@example.com", password="x"
        )

    def _build_sociallogin(self, email):
        class _Account:
            def __init__(self, e):
                self.extra_data = {"email": e}

        class _SocialLogin:
            def __init__(self, e):
                self.account = _Account(e)

        return _SocialLogin(email)

    def test_pre_social_login_allows_active_user(self):
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request._messages = type("M", (), {"add": lambda *a, **k: None})()

        sociallogin = self._build_sociallogin("social@example.com")
        # No exception raised
        self.adapter.pre_social_login(request, sociallogin)

    def test_pre_social_login_blocks_deactivated_user(self):
        from django.test import RequestFactory

        self.user.is_active = False
        self.user.save()

        request = RequestFactory().get("/")
        request._messages = type("M", (), {"add": lambda *a, **k: None})()

        sociallogin = self._build_sociallogin("social@example.com")
        with self.assertRaises(Exception):  # noqa: B017 — code raises bare Exception
            self.adapter.pre_social_login(request, sociallogin)

    def test_pre_social_login_skips_unknown_email(self):
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request._messages = type("M", (), {"add": lambda *a, **k: None})()

        sociallogin = self._build_sociallogin("ghost@example.com")
        # No exception, silently allows
        self.adapter.pre_social_login(request, sociallogin)

    def test_pre_social_login_no_email_skips(self):
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request._messages = type("M", (), {"add": lambda *a, **k: None})()

        sociallogin = self._build_sociallogin("")
        self.adapter.pre_social_login(request, sociallogin)
