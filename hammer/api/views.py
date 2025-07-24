import threading

import time
import random

from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import ProfileSerializer, PhoneNumberSerializer, VerificationCodeSerializer, \
    ActivateInviteCodeSerializer
from users.models import VerificationCode, CustomUser


# Create your views here.
class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.profile

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


def _send_verification_code_mock(phone_number, code):
    print(f"Имитация отправки кода {code} на номер {phone_number}...")
    time.sleep(random.uniform(1, 2)) # Имитация задержки на сервере
    print(f"Код {code} отправлен на номер {phone_number}.")


class RequestVerificationCodeView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PhoneNumberSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]

        VerificationCode.objects.filter(phone_number=phone_number).delete()

        verification_entry = VerificationCode.objects.create(phone_number=phone_number)
        code = verification_entry.code

        # Таска на отправку кода
        threading.Thread(target=_send_verification_code_mock, args=(phone_number, code)).start()

        return Response({"code": code})


class VerifyCodeView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = VerificationCodeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]

        user, created = CustomUser.objects.get_or_create(phone_number=phone_number)

        if created:
            user.set_unusable_password()
            user.save()

        login(request, user)

        return Response({
            'detail': 'Успешная авторизация'
        }, status=status.HTTP_200_OK)


class ActivateCodeView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ActivateInviteCodeSerializer

    def post(self, request):
        user_profile = request.user.profile
        serializer = self.serializer_class(instance=user_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "detail": "Код приглашения активирован",
            "activated_code": serializer.instance.activated_invite_code.invite_code,
        }, status=status.HTTP_200_OK)

