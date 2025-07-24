import string
import random
from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=4))


class VerificationCode(models.Model):
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    code = models.CharField(max_length=4, default=generate_verification_code, verbose_name="Код верификации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    expires_at = models.DateTimeField(verbose_name="Время истечения")

    class Meta:
        verbose_name = "Код верификации"
        verbose_name_plural = "Коды верификации"

    def save(self, *args, **kwargs):
        # Устанавливаем время истечения на 5 минут вперед от текущего времени при создании
        if not self.pk or not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Проверяет, действителен ли код (не истек ли срок действия)."""
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Код {self.code} для {self.phone_number}"

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        """
        Создает и сохраняет обычного пользователя с указанным номером телефона и паролем.
        """
        if not phone_number:
            raise ValueError('Номер телефона должен быть указан')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """
        Создает и сохраняет суперпользователя с указанным номером телефона и паролем.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Суперпользователь всегда активен

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=15, unique=True)
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    invite_code = models.CharField(
        max_length=6,
        default=generate_invite_code,
        unique=True,
    )
    activated_invite_code = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals',
    )

    def __str__(self):
        return f"Профиль пользователя {self.user.phone_number}"

    @property
    def referred_users(self):
        """Возвращает список телефонов пользователей-рефералов."""
        return [referral.user.phone_number for referral in self.referrals.all()]


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

