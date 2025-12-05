# signals.py
from allauth.account.signals import user_signed_up
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# from .models import UserProfile


# @receiver(user_signed_up)
# def create_user_profile(sender, request, user, **kwargs):
#     UserProfile.objects.create(user=user)


# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()
