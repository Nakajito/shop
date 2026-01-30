from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically creates a UserProfile when a CustomUser is created. Django signal that runs after saving.

    Args:
        sender (_type_): _description_
        instance (_type_): _description_
        created (_type_): _description_
    """

    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Automatically saves the UserProfile when CustomUser is updated.

    Args:
        sender (_type_): _description_
        instance (_type_): _description_
    """

    instance.profile.save()
