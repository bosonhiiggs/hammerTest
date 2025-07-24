from django.db import transaction
from rest_framework import serializers

from users.models import Profile, VerificationCode, CustomUser


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения и обновления профиля пользователя.
    """
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    activated_invite_code = serializers.SerializerMethodField()
    referred_users_phone_numbers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['phone_number', 'invite_code', 'activated_invite_code', 'referred_users_phone_numbers']
        read_only_fields = ['phone_number', 'invite_code', 'referred_users_phone_numbers']

    def get_activated_invite_code(self, obj):
        """
        Возвращает активированный инвайт-код профиля (строку) или None, если не активирован.
        """
        if obj.activated_invite_code:
            return obj.activated_invite_code.invite_code
        return None

    def get_referred_users_phone_numbers(self, obj):
        """
        Возвращает список номеров телефонов рефералов.
        """
        return [user for user in obj.referred_users]


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) < 7:
            raise serializers.ValidationError("Номер не соответствует условиям")
        return value


class VerificationCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4)

    def validate(self, data):
        phone_number = data.get('phone_number')
        code = data.get('code')

        if not phone_number or not code:
            raise serializers.ValidationError("Номер телефона и код обязательны.")

        try:
            # Ищем код верификации для данного номера телефона
            verification_entry = VerificationCode.objects.get(phone_number=phone_number)
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("Код для данного номера телефона не найден или истек.")

        # Проверяем, совпадает ли код и действителен ли он
        if verification_entry.code != code:
            raise serializers.ValidationError("Неверный код верификации.")

        if not verification_entry.is_valid():
            raise serializers.ValidationError({"Срок действия кода истек. Запросите новый."})

        # Если все проверки прошли, удаляем использованный код
        verification_entry.delete()
        return data

class ActivateInviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6)

    def validate_invite_code(self, value):
        if not Profile.objects.filter(invite_code=value).exists():
            raise serializers.ValidationError("Код приглашения не существует")
        return value

    def update(self, instance, validated_data):
        if instance.activated_invite_code:
            raise serializers.ValidationError("Код уже активирован")

        try:
            target_profile = Profile.objects.get(invite_code=validated_data['invite_code'])
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Код не найден")

        if instance == target_profile:
            raise serializers.ValidationError("Нельзя активировать свой код")

        with transaction.atomic():
            instance.activated_invite_code = target_profile
            instance.save()

        return instance


