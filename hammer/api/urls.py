from django.urls import path
from rest_framework.urls import app_name

from .views import (
    UserProfileView, RequestVerificationCodeView, VerifyCodeView, ActivateCodeView,
)

urlpatterns = [
    # Эндпоинт для получения и обновления профиля пользователя
    path('auth/request_code/', RequestVerificationCodeView.as_view(), name='request_verification_code'),
    path('auth/verify_code/', VerifyCodeView.as_view(), name='verify_code'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/activate_invite/', ActivateCodeView.as_view(), name='activate_invite_code'),
]
