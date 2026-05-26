from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver that handles the creation and updates of UserProfiles.

    This single function handles both:
    1. Creating a UserProfile when a new CustomUser is created.
    2. Saving the UserProfile when the CustomUser is updated.

    Args:
        sender (Model): The model class that sent the signal (CustomUser).
        instance (CustomUser): The actual instance of the user being saved.
        created (bool): True if a new record was created, False if updated.
        **kwargs: Arbitrary keyword arguments passed by the signal dispatcher.
    """
    if created:
        # Create a new profile for every new user
        UserProfile.objects.create(user=instance)
    else:
        # For existing users, save the profile if it exists
        # hasattr check prevents crashing if for some reason the profile
        # was deleted or doesn't exist (e.g. legacy data)
        if hasattr(instance, "profile"):
            instance.profile.save()
