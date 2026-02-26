from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class CustomAccountAdapter(DefaultAccountAdapter):
    pass


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Block social login for deactivated accounts."""
        email = sociallogin.account.extra_data.get("email", "")
        if email:
            try:
                user = CustomUser.objects.get(email=email)
                if not user.is_active:
                    messages.error(request, _("The account doesn't exist."))
                    raise Exception(_("The account doesn't exist."))
            except CustomUser.DoesNotExist:
                pass
