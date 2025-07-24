from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Profile, VerificationCode


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('phone_number',)
    list_filter = ('is_staff', 'is_active', 'date_joined')
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number',)}),
    )
    ordering = ('phone_number',)

admin.site.register(CustomUser, CustomUserAdmin)

# Регистрируем модель Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'invite_code', 'activated_invite_code')
    search_fields = ('user__phone_number', 'invite_code', 'activated_invite_code__invite_code')
    list_filter = ('activated_invite_code',)
    raw_id_fields = ('user', 'activated_invite_code')

# Регистрируем модель VerificationCode
@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created_at', 'expires_at', 'is_valid')
    search_fields = ('phone_number',)
    list_filter = ('created_at', 'expires_at')
    readonly_fields = ('created_at', 'expires_at')
