from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a UserProfile whenever a new CustomUser is saved.

    This function listens for the post_save signal from the CustomUser model.
    If a new user instance is created, it initializes an associated empty
    UserProfile.

    Args:
        sender (Model): The model class that sent the signal (CustomUser).
        instance (CustomUser): The actual instance of the user being saved.
        created (bool): True if a new record was created, False if updated.
        **kwargs: Arbitrary keyword arguments passed by the signal dispatcher.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal receiver that saves the associated UserProfile when CustomUser is updated.

    This ensures that any changes to the user instance trigger a save on the
    related profile, maintaining data consistency.

    Args:
        sender (Model): The model class that sent the signal (CustomUser).
        instance (CustomUser): The actual instance of the user being saved.
        **kwargs: Arbitrary keyword arguments passed by the signal dispatcher.
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Handles cases where the user exists but the profile has not been created yet
        # (e.g., during the very first save transaction or with legacy data).
        pass
