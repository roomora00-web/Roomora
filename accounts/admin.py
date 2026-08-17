from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Verification, EmailVerification, PhoneVerification, LoginAttempt


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'email_verified', 'phone_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'email_verified', 'phone_verified', 'is_active', 'account_status', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'gender', 'profile_picture')}),
        ('User Type', {'fields': ('user_type', 'account_status')}),
        ('Verification', {'fields': ('email_verified', 'phone_verified')}),
        ('Security', {'fields': ('failed_login_attempts', 'locked_until')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'gender', 'user_type', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'profile_completion_percentage', 'created_at']
    list_filter = ['city', 'country', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('user',)}),
        ('Contact Info', {'fields': ('bio', 'address', 'city', 'country', 'preferred_language')}),
        ('Student Info', {'fields': ('institution', 'field_of_study', 'academic_level')}),
        ('Worker Info', {'fields': ('occupation', 'company_name')}),
        ('Family Info', {'fields': ('household_size',)}),
        ('Couple Info', {'fields': ('is_couple_searching',)}),
        ('Profile Completion', {'fields': ('profile_completion_percentage',)}),
    )



@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'verification_type', 'document_type', 'status', 'submitted_at', 'reviewed_at']
    list_filter = ['verification_type', 'status', 'submitted_at', 'reviewed_at']
    search_fields = ['user__email', 'document_type', 'document_number']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Verification Info', {'fields': ('user', 'verification_type', 'document_type', 'document_number', 'document_image')}),
        ('Status', {'fields': ('status', 'rejection_reason')}),
        ('Review', {'fields': ('reviewed_at', 'reviewed_by')}),
    )


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'created_at', 'expires_at', 'used', 'attempts']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'otp']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Email Verification', {'fields': ('user', 'otp', 'created_at', 'expires_at', 'used', 'attempts')}),
    )


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'expires_at', 'used', 'attempts']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__phone_number', 'code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Phone Verification', {'fields': ('user', 'code', 'created_at', 'expires_at', 'used', 'attempts')}),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['email_or_phone', 'ip_address', 'successful', 'timestamp', 'user_agent']
    list_filter = ['successful', 'timestamp']
    search_fields = ['email_or_phone', 'ip_address', 'user_agent']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Login Attempt', {'fields': ('email_or_phone', 'ip_address', 'successful', 'timestamp', 'user_agent')}),
    )
