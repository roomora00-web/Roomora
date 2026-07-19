from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet, UserProfileViewSet, LifestyleProfileViewSet, VerificationViewSet, SessionViewSet,
    check_email_view, verify_email_view, resend_verification_view,
    login_view, register_view, logout_view, profile_enrichment_view, profile_photo_view,
    forgot_password_view, reset_password_view, dashboard_view, 
    profile_management_view, profile_settings_view, account_settings_view,
    request_unlock_view, send_email_otp_view, verify_email_otp_view,
    lifestyle_edit_view, notifications_page, delete_notification, clear_all_notifications
)
from bookings.views_new_booking import lifestyle_questionnaire, submit_lifestyle_screen, lifestyle_submit

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'lifestyle-profiles', LifestyleProfileViewSet, basename='lifestyleprofile')
router.register(r'verifications', VerificationViewSet, basename='verification')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Web authentication routes
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('check-email/<str:email>/', check_email_view, name='check-email'),
    path('verify-email/', verify_email_view, name='verify-email'),
    path('resend-verification/', resend_verification_view, name='resend-verification'),
    path('send-email-otp/', send_email_otp_view, name='send-email-otp'),
    path('verify-email-otp/', verify_email_otp_view, name='verify-email-otp'),
    path('request-unlock/', request_unlock_view, name='request-unlock'),
    path('logout/', logout_view, name='logout'),
    path('profile-enrichment/', profile_enrichment_view, name='profile-enrichment'),
    path('profile-photo/', profile_photo_view, name='profile-photo'),
    path('profile/', profile_management_view, name='profile'),
    path('profile-management/', profile_management_view, name='profile-management'),
    path('profile-settings/', profile_settings_view, name='profile-settings'),
    path('account-settings/', account_settings_view, name='account-settings'),

    path('forgot-password/', forgot_password_view, name='forgot-password'),
    path('reset-password/<str:token>/', reset_password_view, name='reset-password'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('notifications/', notifications_page, name='notifications'),
    path('notifications/delete/<int:notif_id>/', delete_notification, name='delete-notification'),
    path('notifications/clear-all/', clear_all_notifications, name='clear-all-notifications'),
    
    # Standalone Lifestyle Preferences
    path('lifestyle-edit/', lifestyle_edit_view, name='lifestyle_edit'),
    path('lifestyle-questionnaire/<int:screen>/', lifestyle_questionnaire, name='lifestyle_questionnaire_standalone'),
    path('lifestyle-submit/<int:screen>/', submit_lifestyle_screen, name='lifestyle_submit_standalone'),
    path('lifestyle-submit-final/', lifestyle_submit, name='lifestyle_submit_final_standalone'),
]
