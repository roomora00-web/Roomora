from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import User, UserProfile, LifestyleProfile, Verification, EmailVerification, PhoneVerification, LoginAttempt
from bookings.models import Booking
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserProfileSerializer, LifestyleProfileSerializer, VerificationSerializer, UserDashboardSerializer
)
from .forms import RegistrationForm, LoginForm, ProfileEnrichmentForm, ProfilePhotoForm, PasswordResetRequestForm, PasswordResetForm
import secrets
import random
from functools import wraps


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def email_verification_required(view_func):
    """Decorator to check if user's email is verified"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.email_verified:
                messages.warning(request, 'Please verify your email to access this feature.')
                return redirect('accounts:check-email', email=request.user.email)
        return view_func(request, *args, **kwargs)
    return wrapped_view


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard(self, request):
        """Comprehensive user dashboard endpoint"""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        lifestyle_profile, _ = LifestyleProfile.objects.get_or_create(user=request.user)
        
        data = {
            'user': request.user,
            'profile': profile,
            'lifestyle_profile': lifestyle_profile,
        }
        
        serializer = UserDashboardSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def my_profile(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if request.method in ['PUT', 'PATCH']:
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)


class LifestyleProfileViewSet(viewsets.ModelViewSet):
    queryset = LifestyleProfile.objects.select_related('user').all()
    serializer_class = LifestyleProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def my_lifestyle_profile(self, request):
        profile, created = LifestyleProfile.objects.get_or_create(user=request.user)
        if request.method in ['PUT', 'PATCH']:
            # Capture old high-priority values for change detection
            old_values = {
                'sleep_schedule': profile.sleep_schedule,
                'cleanliness_level': profile.cleanliness_level,
                'noise_tolerance': profile.noise_tolerance,
                'smoking_comfortable': profile.smoking_comfortable,
                'visitor_preference': profile.visitor_preference,
            }

            serializer = LifestyleProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()

                # Detect high-priority changes
                changed = []
                new_profile = LifestyleProfile.objects.get(user=request.user)
                for key, old in old_values.items():
                    new = getattr(new_profile, key)
                    if (old != new):
                        changed.append((key, old, new))

                high_priority_keys = {'sleep_schedule', 'cleanliness_level', 'noise_tolerance', 'smoking_comfortable', 'visitor_preference'}
                if any(k for (k, o, n) in changed if k in high_priority_keys):
                    # Check if user has active roommate matches or bookings
                    from bookings.models import RoommateMatch, Booking
                    has_active_match = RoommateMatch.objects.filter(user=request.user, status='ACCEPTED').exists()
                    tenant_has_match = RoommateMatch.objects.filter(booking__tenant=request.user, status='ACCEPTED').exists()

                    if has_active_match or tenant_has_match:
                        # Determine a representative match score if available
                        match_score = None
                        match = RoommateMatch.objects.filter(user=request.user, status='ACCEPTED').first() or RoommateMatch.objects.filter(booking__tenant=request.user, status='ACCEPTED').first()
                        if match:
                            match_score = match.compatibility_score or None

                        # Notify admins/support
                        try:
                            support_email = getattr(settings, 'SUPPORT_EMAIL', None)
                            subject = f"Lifestyle profile updated - high-priority change: {request.user.email}"
                            changes_text = '\n'.join([f"- {k}: {o} -> {n}" for (k, o, n) in changed if k in high_priority_keys])
                            message = f"User {request.user.get_full_name() or request.user.email} updated their lifestyle profile.\n\nChanged fields:\n{changes_text}\n\nCurrent match score: {match_score if match_score is not None else 'N/A'}\n\nPlease review the user's matches and notify roommates/admins if needed."
                            if support_email:
                                send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[support_email], fail_silently=True)
                            else:
                                # Fallback: notify all staff users
                                from django.contrib.auth import get_user_model
                                User = get_user_model()
                                staff_emails = list(User.objects.filter(is_staff=True).values_list('email', flat=True))
                                if staff_emails:
                                    send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=staff_emails, fail_silently=True)
                        except Exception:
                            pass

                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = LifestyleProfileSerializer(profile)
        return Response(serializer.data)


class VerificationViewSet(viewsets.ModelViewSet):
    queryset = Verification.objects.select_related('user', 'reviewed_by').all()
    serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        verification = self.get_object()
        verification.status = 'APPROVED'
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        
        # Mark user as verified
        verification.user.is_verified = True
        verification.user.save()
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        verification = self.get_object()
        verification.status = 'REJECTED'
        verification.rejection_reason = request.data.get('rejection_reason', '')
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        return Response({'status': 'rejected'})


class SessionViewSet(viewsets.ViewSet):
    """API ViewSet for managing user sessions"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active_sessions(self, request):
        """List all active sessions for the current user"""
        from django.contrib.sessions.models import Session
        import json
        from datetime import datetime
        
        sessions = []
        current_session_key = request.session.session_key
        
        for session in Session.objects.all():
            try:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(request.user.id):
                    sessions.append({
                        'session_key': session.session_key,
                        'is_current': session.session_key == current_session_key,
                        'last_activity': session.expire_date.isoformat(),
                        'device': 'Browser',  # Could be enhanced with user-agent parsing
                    })
            except:
                pass
        
        return Response({'sessions': sessions, 'count': len(sessions)})
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout_session(self, request):
        """Logout from a specific session"""
        from django.contrib.sessions.models import Session
        
        session_key = request.data.get('session_key')
        current_session_key = request.session.session_key
        
        # Prevent logging out the current session
        if session_key == current_session_key:
            return Response({'error': 'Cannot logout from current session'}, status=400)
        
        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()
            
            # Verify it belongs to current user
            if session_data.get('_auth_user_id') == str(request.user.id):
                session.delete()
                return Response({'success': True, 'message': 'Session logged out successfully'})
            else:
                return Response({'error': 'Unauthorized'}, status=403)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)


# Django Views for Web Authentication

def normalize_ghana_phone(phone):
    """Normalize Ghana phone number to +233 format"""
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Check if it's a valid Ghana phone number (9 or 10 digits)
    if len(digits) == 10 and digits.startswith('0'):
        # Format: 0241234567 -> +233241234567
        return '+233' + digits[1:]
    elif len(digits) == 9 and not digits.startswith('0'):
        # Format: 241234567 -> +233241234567
        return '+233' + digits
    elif len(digits) == 12 and digits.startswith('233'):
        # Format: 233241234567 -> +233241234567
        return '+' + digits
    elif len(digits) == 13 and digits.startswith('+233'):
        # Already in correct format
        return digits
    else:
        return None

def check_email_view(request, email):
    """Check your email page - shown after registration"""
    return render(request, 'accounts/check_email.html', {'email': email})


def verify_email_view(request):
    """Email verification view using OTP"""
    if request.user.is_authenticated and request.user.email_verified:
        return redirect('landing:home')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        email = request.POST.get('email')
        
        if not email:
            return render(request, 'accounts/verify_email.html', {
                'status': 'error',
                'message': 'Invalid request.'
            })
        
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                user.account_status = 'ACTIVE'
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, 'Your email is already verified! Welcome to Roomora.')
                return redirect('landing:home')

            if not otp:
                return render(request, 'accounts/verify_email.html', {
                    'status': 'error',
                    'message': 'Please enter your 6-digit verification code.',
                    'email': email
                })

            verification = EmailVerification.objects.filter(
                user=user,
                used=False
            ).latest('created_at')
            
            if verification.is_valid() and verification.otp == otp:
                # Mark OTP as used
                verification.used = True
                verification.save()
                
                # Mark email as verified and active
                user.email_verified = True
                user.account_status = 'ACTIVE'
                user.is_active = True
                user.save()
                
                # Log user in and redirect to home
                login(request, user)
                messages.success(request, 'Email verified! Welcome to Roomora.')
                return redirect('landing:home')
            elif verification.used:
                return render(request, 'accounts/verify_email.html', {
                    'status': 'error',
                    'message': 'This verification code has already been used.',
                    'email': email
                })
            elif verification.attempts >= 3:
                return render(request, 'accounts/verify_email.html', {
                    'status': 'error',
                    'message': 'Too many incorrect attempts. Please request a new code.',
                    'can_resend': True,
                    'email': email
                })
            elif timezone.now() > verification.expires_at:
                return render(request, 'accounts/verify_email.html', {
                    'status': 'error',
                    'message': 'This verification code has expired. Would you like us to send you a new one?',
                    'can_resend': True,
                    'email': email
                })
            else:
                # Increment attempts
                verification.increment_attempts()
                return render(request, 'accounts/verify_email.html', {
                    'status': 'error',
                    'message': 'Invalid verification code.',
                    'email': email
                })
        except User.DoesNotExist:
            return render(request, 'accounts/verify_email.html', {
                'status': 'error',
                'message': 'We could not verify your email. Please try again or contact support.'
            })
        except EmailVerification.DoesNotExist:
            return render(request, 'accounts/verify_email.html', {
                'status': 'error',
                'message': 'No active verification code found. Please request a new code.',
                'can_resend': True,
                'email': email
            })
    
    # GET request - redirect to check email page or home if verified
    email = request.GET.get('email', '')
    if email:
        try:
            u = User.objects.get(email=email)
            if u.email_verified:
                u.account_status = 'ACTIVE'
                u.is_active = True
                u.save()
                login(request, u)
                messages.success(request, 'Your email is verified! Welcome to Roomora.')
                return redirect('landing:home')
        except User.DoesNotExist:
            pass
    return redirect('accounts:check-email', email=email)


def resend_verification_view(request):
    """Resend verification OTP"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user can resend (max 5 times in 24 hours)
            recent_verifications = EmailVerification.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            
            if recent_verifications >= 5:
                messages.error(request, 'You have reached the maximum number of resend attempts. Please try again later.')
                return redirect('accounts:check-email', email=email)
            
            # Generate new OTP
            otp = user.generate_otp()
            expires_at = timezone.now() + timezone.timedelta(hours=24)
            EmailVerification.objects.create(
                user=user,
                otp=otp,
                expires_at=expires_at
            )
            
            # Send verification email with OTP
            try:
                send_mail(
                    'Verify your Roomora account',
                    f'Hi {user.first_name},\n\nYour verification code is: {otp}\n\nThis code expires in 24 hours.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                pass
            messages.success(request, 'Verification code sent successfully.')
        except User.DoesNotExist:
            # Don't reveal if email exists
            messages.success(request, 'If an account exists with this email, we\'ve sent a verification code.')
    
    return redirect('accounts:check-email', email=email)


def forgot_password_view(request):
    """Password reset request view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Always show the same message to prevent account enumeration
        messages.success(request, 'If an account exists with this email, we\'ve sent a password reset link.')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate a secure reset token (32 bytes of random data)
            import secrets
            reset_token = secrets.token_urlsafe(32)
            
            # Store the reset token with expiration (1 hour)
            from django.utils import timezone
            expires_at = timezone.now() + timezone.timedelta(hours=1)
            
            # Create or update password reset record
            # Note: We need a PasswordReset model, but for now we'll use EmailVerification with a different purpose
            # In production, create a dedicated PasswordReset model
            verification = EmailVerification.objects.create(
                user=user,
                otp=reset_token[:6],  # Using first 6 chars as OTP for simplicity
                expires_at=expires_at
            )
            
            # Send password reset email
            try:
                reset_url = f"http://{request.get_host()}/accounts/reset-password/{reset_token}/"
                send_mail(
                    'Reset your Realco password',
                    f'Hi {user.first_name},\n\nClick the link below to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.\n\nIf you didn\'t request a password reset, you can ignore this email.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send password reset email: {e}")
                
        except User.DoesNotExist:
            # Don't reveal if email exists - already showed success message above
            pass
        
        return redirect('accounts:login')
    
    return render(request, 'accounts/forgot_password.html')


def reset_password_view(request, token=None):
    """Password reset view with token"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        token = request.POST.get('token')
        
        # Password strength validation
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters and contain uppercase, number, and special character, or be 12+ characters long.')
            return render(request, 'accounts/reset_password.html', {'token': token})
        
        if len(new_password) >= 12:
            pass
        else:
            has_upper = any(c.isupper() for c in new_password)
            has_number = any(c.isdigit() for c in new_password)
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password)
            
            if not (has_upper and has_number and has_special):
                messages.error(request, 'Password must be at least 8 characters and contain uppercase, number, and special character, or be 12+ characters long.')
                return render(request, 'accounts/reset_password.html', {'token': token})
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/reset_password.html', {'token': token})
        
        # Find the verification record with this token
        try:
            verification = EmailVerification.objects.filter(otp=token[:6], used=False).latest('created_at')
            
            if timezone.now() > verification.expires_at:
                messages.error(request, 'This reset link has expired. Please request a new one.')
                return redirect('accounts:forgot-password')
            
            if verification.used:
                messages.error(request, 'This reset link has already been used. Please request a new one.')
                return redirect('accounts:forgot-password')
            
            # Reset the user's password
            user = verification.user
            user.set_password(new_password)
            user.save()
            
            # Mark verification as used
            verification.used = True
            verification.save()
            
            # Reset failed login attempts
            user.reset_failed_login()
            
            messages.success(request, 'Your password has been reset. Please log in.')
            return redirect('accounts:login')
            
        except (EmailVerification.DoesNotExist, Exception) as e:
            messages.error(request, 'Invalid reset link. Please request a new one.')
            return redirect('accounts:forgot-password')
    
    return render(request, 'accounts/reset_password.html', {'token': token})


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect(getattr(settings, 'LOGOUT_REDIRECT_URL', 'landing:home'))


def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Reset failed login attempts on successful login
            user.reset_failed_login()
            
            # Redirect to next URL if provided, otherwise dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # Redirect based on account status
            if user.account_status == 'EMAIL_UNVERIFIED':
                return redirect('accounts:check-email', email=user.email)
            elif user.account_status == 'PROFILE_INCOMPLETE':
                return redirect('accounts:profile-enrichment')
            else:
                return redirect('accounts:dashboard')
    else:
        form = LoginForm(request=request)
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """Registration view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            
            # Generate and send OTP for email verification
            otp = user.generate_otp()
            expires_at = timezone.now() + timezone.timedelta(hours=24)
            EmailVerification.objects.create(
                user=user,
                otp=otp,
                expires_at=expires_at
            )
            
            # Send verification email
            try:
                send_mail(
                    'Verify your Roomora account',
                    f'Hi {user.first_name},\n\nYour verification code is: {otp}\n\nThis code expires in 24 hours.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                pass
            messages.success(request, 'Account created successfully! Please check your email for the verification code.')
            return redirect('accounts:check-email', email=user.email)
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@email_verification_required
def profile_enrichment_view(request):
    """Profile enrichment view - Phase 3 of authentication"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileEnrichmentForm(request.POST, instance=profile, user_type=request.user.user_type)
        if form.is_valid():
            form.save()
            profile.calculate_completion()
            
            # Update account status
            if profile.profile_completion_percentage >= 100:
                request.user.account_status = 'COMPLETE'
            else:
                request.user.account_status = 'PROFILE_INCOMPLETE'
            request.user.save()
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:dashboard')
    else:
        form = ProfileEnrichmentForm(instance=profile, user_type=request.user.user_type)
    
    return render(request, 'accounts/profile_enrichment.html', {
        'form': form,
        'profile': profile,
        'completion_percentage': profile.calculate_completion()
    })


@login_required
@email_verification_required
def profile_photo_view(request):
    """Profile photo upload view"""
    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.cleaned_data['profile_photo']
            request.user.profile_picture = photo
            request.user.save()
            
            # Recalculate profile completion
            if hasattr(request.user, 'profile'):
                request.user.profile.calculate_completion()
            
            messages.success(request, 'Profile photo updated successfully.')
            return redirect('accounts:profile-enrichment')
    else:
        form = ProfilePhotoForm()
    
    return render(request, 'accounts/profile_photo.html', {'form': form})





def password_reset_request_view(request):
    """Password reset request view"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Create password reset token
                token = user.generate_verification_token()
                expires_at = timezone.now() + timezone.timedelta(hours=1)
                
                # Store token in EmailVerification with a special flag
                EmailVerification.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Send password reset email
                reset_url = f"{request.build_absolute_uri('/reset-password/')}?token={token}"
                try:
                    send_mail(
                        'Reset your StayMatch password',
                        f'Click the link below to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour.\n\nIf you didn\'t request a password reset, you can ignore this email.',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    messages.success(request, 'If an account exists with this email, we\'ve sent a password reset link.')
                except Exception as e:
                    messages.error(request, 'Failed to send password reset email. Please try again.')
            except User.DoesNotExist:
                # Don't reveal if email exists
                messages.success(request, 'If an account exists with this email, we\'ve sent a password reset link.')
            
            return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_view(request):
    """Password reset view"""
    token = request.GET.get('token')
    
    if not token:
        return render(request, 'accounts/password_reset.html', {
            'status': 'error',
            'message': 'Invalid password reset link.'
        })
    
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if not verification.is_valid():
            return render(request, 'accounts/password_reset.html', {
                'status': 'error',
                'message': 'This password reset link has expired.'
            })
        
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                # Update user password
                verification.user.set_password(form.cleaned_data['new_password'])
                verification.user.save()
                
                # Mark token as used
                verification.used = True
                verification.save()
                
                # Invalidate all sessions
                from django.contrib.sessions.models import Session
                Session.objects.filter(session_key__contains=str(verification.user.id)).delete()
                
                messages.success(request, 'Your password has been reset. Please log in.')
                return redirect('accounts:login')
        else:
            form = PasswordResetForm()
        
        return render(request, 'accounts/password_reset.html', {
            'form': form,
            'status': 'valid'
        })
        
    except EmailVerification.DoesNotExist:
        return render(request, 'accounts/password_reset.html', {
            'status': 'error',
            'message': 'Invalid password reset link.'
        })


@login_required
@email_verification_required
def dashboard_view(request):
    """User dashboard view - State-aware hub showing relevant information based on user journey stage"""
    if request.user.user_type == 'ADMIN':
        return redirect('bookings:admin-dashboard')
        
    from bookings.models import PropertySearch, RecentlyViewed, Booking, RoommateMatch
    from properties.models import Property
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Check profile completion
    completion_percentage = profile.calculate_completion()
    
    # Get saved properties
    saved_properties = request.user.saved_properties.all()
    saved_properties_count = saved_properties.count()
    
    # Get recent searches
    recent_searches = PropertySearch.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).order_by('-created_at')
    recent_searches_count = recent_searches.count()
    last_search = recent_searches.first()
    
    # Get recently viewed properties
    recently_viewed = RecentlyViewed.objects.filter(
        user=request.user
    ).select_related('property').order_by('-viewed_at')[:5]
    
    # Get booking information for state determination
    active_bookings = Booking.objects.filter(
        tenant=request.user,
        status__in=['INITIATED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPATIBILITY_REVIEW', 'WAITING_CONSENT', 
                    'BOTH_ACCEPTED', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 'ACTIVE', 'TEMPORARILY_CANCELLED']
    ).select_related('accommodation_property', 'room_type', 'unit_type').order_by('-created_at')
    
    current_booking = active_bookings.first()
    active_booking_count = active_bookings.count()
    
    # Get roommate match if exists
    roommate_match = None
    if current_booking:
        roommate_match = RoommateMatch.objects.filter(
            booking=current_booking
        ).select_related('user').first()
    
    # Determine user state for contextual messaging
    user_state = determine_user_state(request.user, profile, saved_properties, recent_searches, current_booking)
    
    # Get status message and details based on state
    status_message, status_details = get_status_message(user_state, request.user, last_search, saved_properties_count, current_booking, roommate_match)
    
    # Get recommended properties based on user type and search history
    if last_search:
        recommended_properties = Property.objects.filter(
            status='APPROVED',
            is_available=True,
            city__icontains=last_search.city if last_search.city else ''
        ).exclude(
            saved_by=request.user
        ).prefetch_related('images', 'room_types__pricing_models', 'unit_types__pricing_models').order_by('-created_at', '-views_count')[:6]
    else:
        recommended_properties = Property.objects.filter(
            status='APPROVED',
            is_available=True,
            suitable_for_students=request.user.user_type == 'STUDENT'
        ).prefetch_related('images', 'room_types__pricing_models', 'unit_types__pricing_models').order_by('-views_count', '-created_at')[:6]
    
    # Get notifications/alerts
    notifications = get_user_notifications(request.user, profile, current_booking)
    
    context = {
        'user': request.user,
        'profile': profile,
        'completion_percentage': completion_percentage,
        'needs_profile_enrichment': completion_percentage < 100,
        'user_state': user_state,
        'status_message': status_message,
        'status_details': status_details,
        'saved_properties_count': saved_properties_count,
        'recent_searches_count': recent_searches_count,
        'recommended_properties': recommended_properties,
        'recently_viewed': recently_viewed,
        'last_search': last_search,
        'current_booking': current_booking,
        'roommate_match': roommate_match,
        'active_booking_count': active_booking_count,
        'notifications': notifications,
    }
    
    return render(request, 'accounts/dashboard.html', context)


def determine_user_state(user, profile, saved_properties, recent_searches, current_booking):
    """Determine the user's current state for contextual messaging based on journey stage"""
    # Priority 1: Check if user has multiple active bookings
    if current_booking and hasattr(current_booking, '__iter__'):
        active_count = len([b for b in current_booking if b.status in ['INITIATED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPATIBILITY_REVIEW', 'WAITING_CONSENT', 'BOTH_ACCEPTED', 'APPROVED_ASSIGNED', 'ACTIVE', 'TEMPORARILY_CANCELLED']])
        if active_count > 1:
            return 'multiple_bookings'
    
    # Priority 2: Check if user has an active booking (currently living)
    if current_booking and current_booking.status == 'ACTIVE':
        return 'active_living'
    
    # Priority 3: Check if user has an approved booking (pre-move-in)
    if current_booking and current_booking.status == 'APPROVED_ASSIGNED':
        return 'approved_pre_movein'
    
    # Priority 4: Check if user has a booking in progress
    if current_booking and current_booking.status in ['INITIATED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPATIBILITY_REVIEW', 'WAITING_CONSENT', 'BOTH_ACCEPTED']:
        return 'booking_in_progress'
    
    # Priority 5: Check if user has a completed booking (post-move-out)
    completed_booking = Booking.objects.filter(
        tenant=user,
        status='COMPLETED',
        move_out_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).first()
    if completed_booking:
        return 'completed_lease'
    
    # Priority 6: Check if profile is incomplete
    if profile and profile.profile_completion_percentage < 50:
        return 'new_user'
    
    # Priority 7: Check if user is actively searching
    if recent_searches.exists():
        return 'searching'
    
    # Priority 8: Check if user has saved properties
    if saved_properties.count() > 0:
        return 'property_saver'
    
    # Default to new user
    return 'new_user'


def get_status_message(user_state, user, last_search=None, saved_count=0, current_booking=None, roommate_match=None):
    """Get contextual status message and details based on user state"""
    if user_state == 'new_user':
        message = f"Welcome to StayMatch, {user.first_name}! 👋"
        details = {
            'subtitle': "You're 3 steps away from finding your perfect accommodation.",
            'actions': [
                {'text': 'Complete Your Profile', 'url': '/profile/'},
                {'text': 'Browse Now', 'url': '/properties/'}
            ]
        }
    elif user_state == 'searching':
        message = f"Welcome back, {user.first_name}! 👋"
        subtitle = f"You've saved {saved_count} propert{'y' if saved_count == 1 else 'ies'} and searched recently."
        details = {
            'subtitle': subtitle,
            'actions': [
                {'text': 'View Saved', 'url': '/saved/'},
                {'text': 'Continue Searching', 'url': '/properties/'}
            ]
        }
    elif user_state == 'booking_in_progress':
        message = "Your booking is being processed 🔄"
        if current_booking:
            property_name = current_booking.accommodation_property.title
            status_display = current_booking.get_status_display()
            if current_booking.status == 'INITIATED':
                message = "Action Required: Complete Booking ⏳"
                details = {
                    'subtitle': f"{property_name} — Soft Lock Active",
                    'expected': "Your slot is held. Complete the next steps to confirm.",
                    'actions': [
                        {'text': 'Resume Booking', 'url': f'/bookings/booking/{current_booking.id}/initiated/'}
                    ]
                }
            else:
                details = {
                    'subtitle': f"{property_name} — Status: {status_display}",
                    'expected': "Expected: Within 24 hours",
                    'actions': [
                        {'text': 'View Booking Details', 'url': f'/bookings/{current_booking.id}/'}
                    ]
                }
        else:
            details = {'subtitle': '', 'actions': []}
    elif user_state == 'approved_pre_movein':
        message = "✓ Your booking is confirmed! 🎉"
        if current_booking:
            property_name = current_booking.accommodation_property.title
            room_info = current_booking.assigned_room or "Room assigned"
            move_in = current_booking.move_in_date.strftime("%B %d, %Y") if current_booking.move_in_date else "TBD"
            roommate_info = ""
            if roommate_match:
                roommate_name = roommate_match.user.first_name
                score = roommate_match.compatibility_score or 0
                roommate_info = f"Roommate: {roommate_name} ({int(score)}% compatible)"
            details = {
                'subtitle': f"{property_name} — {room_info}",
                'roommate': roommate_info,
                'move_in': f"Move-in: {move_in}",
                'actions': [
                    {'text': 'View Details', 'url': f'/bookings/{current_booking.id}/'},
                    {'text': 'Meet Your Roommate', 'url': f'/roommate/{roommate_match.id}/' if roommate_match else '#'}
                ]
            }
        else:
            details = {'subtitle': '', 'roommate': '', 'move_in': '', 'actions': []}
    elif user_state == 'active_living':
        message = "You're settled in! 🏠"
        if current_booking:
            property_name = current_booking.accommodation_property.title
            room_info = current_booking.assigned_room or "Your room"
            roommate_info = ""
            if roommate_match:
                roommate_name = roommate_match.user.first_name
                roommate_info = f"Roommate: {roommate_name}"
            
            # Calculate lease progress
            lease_progress = 0
            time_left = ""
            if current_booking.move_in_date and current_booking.move_out_date:
                total_days = (current_booking.move_out_date - current_booking.move_in_date).days
                days_passed = (timezone.now().date() - current_booking.move_in_date).days
                lease_progress = min(100, max(0, int((days_passed / total_days) * 100)))
                days_remaining = (current_booking.move_out_date - timezone.now().date()).days
                if days_remaining > 0:
                    weeks = days_remaining // 7
                    time_left = f"{weeks} week{'s' if weeks != 1 else ''}"
            
            details = {
                'subtitle': f"{property_name} — {room_info}",
                'lease_progress': lease_progress,
                'time_left': time_left,
                'roommate': roommate_info,
                'actions': [
                    {'text': 'View Details', 'url': f'/bookings/{current_booking.id}/'},
                    {'text': 'Report Issue', 'url': f'/bookings/{current_booking.id}/report/'}
                ]
            }
        else:
            details = {'subtitle': '', 'lease_progress': 0, 'time_left': '', 'roommate': '', 'actions': []}
    elif user_state == 'completed_lease':
        message = "Thanks for staying with us! 👏"
        details = {
            'subtitle': "Your lease has ended.",
            'actions': [
                {'text': 'Rate Your Stay', 'url': '/review/'},
                {'text': 'Leave a Review', 'url': '/review/'},
                {'text': 'Search Again', 'url': '/properties/'}
            ]
        }
    elif user_state == 'multiple_bookings':
        message = "You have multiple active bookings 📋"
        details = {
            'subtitle': "You can hold bookings at multiple properties before confirming move-in.",
            'note': "Cancellations may apply fees.",
            'actions': [
                {'text': 'Manage Bookings', 'url': '/bookings/'}
            ]
        }
    else:
        message = f"Welcome back, {user.first_name}! 👋"
        details = {
            'subtitle': "Ready to find your perfect accommodation?",
            'actions': [
                {'text': 'Browse Properties', 'url': '/properties/'}
            ]
        }
    
    return message, details


def get_user_notifications(user, profile, current_booking):
    """Get notifications/alerts for the user"""
    notifications = []
    

    # Profile incomplete (Keep this as a dynamic generated notification)
    if profile and profile.profile_completion_percentage < 100:
        notifications.append({
            'type': 'info',
            'icon': '📝',
            'title': 'Complete Your Profile',
            'message': f'Your profile is {profile.profile_completion_percentage}% complete.',
            'action': 'Complete Profile',
            'action_url': '/profile/'
        })
    
    # Fetch real notifications from the database
    from accounts.models import Notification
    db_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    
    for notif in db_notifications:
        # Determine visual type based on notification_type
        notif_type = 'info'
        if notif.notification_type in ['SUCCESS', 'MATCH_FOUND']:
            notif_type = 'success'
        elif notif.notification_type in ['WARNING', 'CONFLICT']:
            notif_type = 'warning'
        elif notif.notification_type in ['SYSTEM', 'URGENT']:
            notif_type = 'urgent'
            
        notifications.append({
            'type': notif_type,
            'title': notif.title,
            'message': notif.message,
            'action': 'View',
            'action_url': notif.link if notif.link else '#',
            'id': notif.id,
            'is_read': notif.is_read,
        })
        
    return notifications


@login_required
def lifestyle_edit_view(request):
    """View for editing lifestyle preferences from the dashboard"""
    lifestyle_profile, created = LifestyleProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'use_saved':
            messages.success(request, 'Your lifestyle profile is active.')
            return redirect('accounts:profile')
            
        elif action in ['recomplete', 'edit_categories']:
            # For now, redirect to the standalone questionnaire flow
            # The questionnaire will pre-load existing answers since we pass profile in context
            return redirect('accounts:lifestyle_questionnaire_standalone', screen=1)
            
    context = {
        'last_updated': lifestyle_profile.last_updated_at if not created else timezone.now(),
    }
    return render(request, 'accounts/lifestyle_edit.html', context)


@login_required
@email_verification_required
def profile_management_view(request):
    """User profile management view - Comprehensive profile page with tab-based navigation"""
    from bookings.models import Booking
    from feedback.models import Review
    from .forms import PersonalInfoForm, StudentInfoForm, WorkerInfoForm, FamilyInfoForm, NSPInfoForm, ExpatInfoForm, LifestyleProfileForm, CommunicationPreferencesForm
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    lifestyle_profile, _ = LifestyleProfile.objects.get_or_create(user=request.user)
    
    # Initialize forms
    personal_form = PersonalInfoForm(instance=request.user)
    student_form = StudentInfoForm(instance=profile) if request.user.user_type == 'STUDENT' else None
    worker_form = WorkerInfoForm(instance=profile) if request.user.user_type == 'WORKER' else None
    family_form = FamilyInfoForm(instance=profile) if request.user.user_type == 'FAMILY' else None
    nsp_form = NSPInfoForm(instance=profile) if request.user.user_type == 'NATIONAL_SERVICE' else None
    expat_form = ExpatInfoForm(instance=profile) if request.user.user_type == 'EXPATRIATE' else None
    lifestyle_form = LifestyleProfileForm(instance=lifestyle_profile)
    communication_form = CommunicationPreferencesForm(instance=profile)
    
    # Determine active tab from query parameter or post data
    active_tab = request.GET.get('tab', 'personal')
    
    # Handle POST requests for profile updates
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        from django.contrib import messages
        
        if form_type == 'photo':
            if 'profile_picture' in request.FILES:
                request.user.profile_picture = request.FILES['profile_picture']
                request.user.save()
                messages.success(request, 'Profile photo updated successfully.')
            else:
                messages.error(request, 'No photo selected.')
            return redirect('accounts:profile')
            
        elif form_type == 'personal':
            personal_form = PersonalInfoForm(request.POST, instance=request.user)
            if personal_form.is_valid():
                personal_form.save()
                
                # Also save bio, emergency contacts from user object but UserProfile has some fields like bio
                profile.bio = request.POST.get('bio', profile.bio)
                profile.save()
                
                messages.success(request, 'Personal information updated successfully.')
                return redirect('accounts:profile')
            else:
                active_tab = 'personal'
                
        elif form_type == 'student' and student_form:
            student_form = StudentInfoForm(request.POST, instance=profile)
            if student_form.is_valid():
                student_form.save()
                messages.success(request, 'Student information updated successfully.')
                return redirect('accounts:profile')
            else:
                active_tab = 'type_info'
                
        elif form_type == 'worker' and worker_form:
            worker_form = WorkerInfoForm(request.POST, instance=profile)
            if worker_form.is_valid():
                worker_form.save()
                messages.success(request, 'Worker information updated successfully.')
                return redirect('accounts:profile')
            else:
                active_tab = 'type_info'
                
        elif form_type == 'family' and family_form:
            family_form = FamilyInfoForm(request.POST, instance=profile)
            if family_form.is_valid():
                family_form.save()
                messages.success(request, 'Family information updated successfully.')
                return redirect('accounts:profile')
            else:
                active_tab = 'type_info'
                
        elif form_type == 'national_service' and nsp_form:
            nsp_form = NSPInfoForm(request.POST, instance=profile)
            if nsp_form.is_valid():
                nsp_form.save()
                messages.success(request, 'National Service information updated successfully.')
                return redirect('accounts:profile')
            else:
                active_tab = 'type_info'
                
        elif form_type == 'expatriate' and expat_form:
            expat_form = ExpatInfoForm(request.POST, instance=profile)
            if expat_form.is_valid():
                expat_form.save()
                messages.success(request, 'Expatriate information updated successfully.')
                return redirect('accounts:profile')
            else:
                active_tab = 'type_info'
                
        elif form_type == 'privacy':
            profile.profile_visibility = request.POST.get('profile_visibility', profile.profile_visibility)
            profile.save()
            messages.success(request, 'Privacy settings updated successfully.')
            return redirect('/accounts/profile/?tab=privacy')
            
        elif form_type == 'lifestyle':
            lifestyle_form = LifestyleProfileForm(request.POST, instance=lifestyle_profile)
            if lifestyle_form.is_valid():
                lifestyle_form.save()
                messages.success(request, 'Living preferences updated successfully.')
                return redirect('/accounts/profile/?tab=lifestyle')
            else:
                active_tab = 'lifestyle'
                
        elif form_type == 'communication':
            communication_form = CommunicationPreferencesForm(request.POST, instance=profile)
            if communication_form.is_valid():
                communication_form.save()
                messages.success(request, 'Communication preferences updated successfully.')
                return redirect('/accounts/profile/?tab=communication')
            else:
                active_tab = 'communication'
                
        elif form_type == 'verification':
            action = request.POST.get('verify_action')
            if action == 'email':
                messages.success(request, 'Verification email resent.')
            return redirect('/accounts/profile/?tab=verification')
            
    # Calculate profile completion
    completion_percentage = profile.calculate_completion()
    remaining_percentage = 100 - completion_percentage
    
    # Get user's bookings and reviews for public profile info
    user_bookings = Booking.objects.filter(tenant=request.user).select_related('accommodation_property')
    user_reviews = Review.objects.filter(reviewer=request.user)
    
    # Get notifications
    current_booking = user_bookings.first()
    notifications = get_user_notifications(request.user, profile, current_booking)
    
    context = {
        'user': request.user,
        'profile': profile,
        'lifestyle_profile': lifestyle_profile,
        'completion_percentage': completion_percentage,
        'remaining_percentage': remaining_percentage,
        'notifications': notifications,
        'active_tab': active_tab,
        'user_bookings': user_bookings,
        'user_reviews': user_reviews,
        'personal_form': personal_form,
        'student_form': student_form,
        'worker_form': worker_form,
        'family_form': family_form,
        'nsp_form': nsp_form,
        'expat_form': expat_form,
        'lifestyle_form': lifestyle_form,
        'communication_form': communication_form,
        'has_shared_room_booking': user_bookings.filter(
            room_type__occupancy_type__in=['DOUBLE', 'TRIPLE', 'DORM']
        ).exists(),
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
@email_verification_required
def profile_settings_view(request):
    """Profile settings view - Phase 2.5: Account Preferences"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle display preferences
        preferred_language = request.POST.get('preferred_language', 'en')
        profile.preferred_language = preferred_language
        profile.save()
        
        messages.success(request, 'Your display preferences have been updated.')
        return redirect('accounts:profile-settings')
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    
    return render(request, 'accounts/profile_settings.html', context)


@login_required
@email_verification_required
def account_settings_view(request):
    """Account settings view - Phase 5: Account Settings, Notifications, and Support"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle settings updates
        action = request.POST.get('action')
        
        if action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if request.user.check_password(old_password):
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    
                    # Invalidate all other sessions (logout from other devices)
                    from django.contrib.sessions.models import Session
                    import json
                    current_session_key = request.session.session_key
                    for session in Session.objects.all():
                        try:
                            session_data = session.get_decoded()
                            if session_data.get('_auth_user_id') == str(request.user.id):
                                if session.session_key != current_session_key:
                                    session.delete()
                        except:
                            pass
                    
                    messages.success(request, 'Password changed successfully. All other sessions have been logged out for security.')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        elif action == 'notification_preferences':
            profile.email_notifications = request.POST.get('email_notifications') == 'on'
            profile.sms_notifications = request.POST.get('sms_notifications') == 'on'
            profile.push_notifications = request.POST.get('push_notifications') == 'on'
            profile.save()
            messages.success(request, 'Notification preferences updated.')
        
        elif action == 'privacy_settings':
            profile.profile_visibility = request.POST.get('profile_visibility', 'private')
            profile.data_sharing = request.POST.get('data_sharing') == 'on'
            profile.save()
            messages.success(request, 'Privacy settings updated.')
        
        elif action == 'download_data':
            # Generate a data export for the user
            import json
            from django.http import HttpResponse
            
            user_data = {
                'user': {
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'phone_number': request.user.phone_number,
                    'gender': request.user.gender,
                    'user_type': request.user.user_type,
                    'created_at': request.user.created_at.isoformat() if request.user.created_at else None,
                },
                'profile': {
                    'bio': profile.bio,
                    'address': profile.address,
                    'city': profile.city,
                    'country': profile.country,
                    'preferred_language': profile.preferred_language,
                    'email_notifications': profile.email_notifications,
                    'sms_notifications': profile.sms_notifications,
                    'push_notifications': profile.push_notifications,
                    'profile_visibility': profile.profile_visibility,
                    'data_sharing': profile.data_sharing,
                }
            }
            
            response = HttpResponse(json.dumps(user_data, indent=2), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="staymatch_data_{request.user.email}.json"'
            return response
        
        elif action == 'deactivate_account':
            confirmation = request.POST.get('deactivate_confirm')
            if confirmation == 'DEACTIVATE':
                request.user.is_active = False
                request.user.save()
                from django.contrib.auth import logout
                logout(request)
                messages.success(request, 'Your account has been deactivated.')
                return redirect('landing:home')
            else:
                messages.error(request, 'You must type DEACTIVATE to confirm.')
                
        elif action == 'delete_account':
            # Require password confirmation for account deletion
            password = request.POST.get('delete_password')
            if request.user.check_password(password):
                # Mark account for deletion (30-day grace period)
                request.user.is_deactivated = True
                request.user.deletion_scheduled_date = timezone.now() + timezone.timedelta(days=30)
                request.user.save()
                
                # Log out user
                logout(request)
                
                messages.success(request, 'Your account has been scheduled for deletion. You have 30 days to cancel this request.')
                return redirect('accounts:login')
            else:
                messages.error(request, 'Incorrect password. Account deletion cancelled.')
        
        elif action == 'contact_support':
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            
            if subject and message:
                # Generate support ticket reference
                import random
                import string
                ticket_ref = 'SUPPORT-' + ''.join(random.choices(string.digits, k=6))
                
                # Send confirmation email to user
                try:
                    send_mail(
                        subject=f'Support Ticket Received - {ticket_ref}',
                        message=f'''Hello {request.user.get_full_name() or request.user.email},

We have received your support request with ticket reference: {ticket_ref}

Subject: {subject}
Message: {message}

Our support team will review your request and get back to you within 24 hours.

Best regards,
StayMatch Support Team''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[request.user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    pass
                
                # Send notification to support team
                try:
                    support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@staymatch.com')
                    send_mail(
                        subject=f'New Support Ticket: {ticket_ref}',
                        message=f'''New support ticket received:

Ticket Reference: {ticket_ref}
User: {request.user.email}
User Name: {request.user.get_full_name()}
Phone: {request.user.phone_number}

Subject: {subject}

Message:
{message}

Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[support_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    pass
                
                messages.success(request, f'Your support request has been submitted. Reference: {ticket_ref}. We will get back to you within 24 hours.')
            else:
                messages.error(request, 'Please fill in both subject and message.')
        
        return redirect('accounts:account-settings')
    
    context = {
        'user': request.user,
        'profile': profile,
        'email_notifications': profile.email_notifications,
        'sms_notifications': profile.sms_notifications,
        'push_notifications': profile.push_notifications,
        'profile_visibility': profile.profile_visibility,
        'data_sharing': profile.data_sharing,
    }
    
    return render(request, 'accounts/account_settings.html', context)


from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def request_unlock_view(request):
    import json
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)
        reason = data.get('reason')
        if not reason:
            return JsonResponse({'error': 'Reason is required'}, status=400)
            
        from feedback.models import UserFeedback
        
        UserFeedback.objects.create(
            user=request.user,
            feedback_type='GENERAL',
            subject=f'Profile Unlock Request - {request.user.email}',
            message=f'User requested a profile unlock. Reason: {reason}'
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def notifications_page(request):
    from accounts.models import Notification
    
    # Get all notifications for the user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all unread as read
    unread = notifications.filter(is_read=False)
    if unread.exists():
        unread.update(is_read=True)
        
    # We still fetch again or just pass the evaluated queryset. 
    # Since we updated them to read, we can just fetch them again so they show as read.
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'accounts/notifications.html', context)

@login_required
@require_POST
def delete_notification(request, notif_id):
    from accounts.models import Notification
    from django.http import JsonResponse
    try:
        notification = Notification.objects.get(id=notif_id, user=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)

@login_required
@require_POST
def clear_all_notifications(request):
    from accounts.models import Notification
    from django.http import JsonResponse
    Notification.objects.filter(user=request.user).delete()
    return JsonResponse({'success': True})
@login_required
@require_POST
def send_email_otp_view(request):
    import json
    from django.http import JsonResponse
    # Mock sending email OTP
    return JsonResponse({'success': True, 'message': 'Email OTP sent'})

@login_required
@require_POST
def verify_email_otp_view(request):
    import json
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)
        otp = data.get('otp')
        if otp and len(otp) >= 4:
            # Mock verification
            request.user.email_verified = True
            request.user.save()
            return JsonResponse({'success': True, 'message': 'Email verified'})
        return JsonResponse({'success': False, 'error': 'Invalid 6-digit code'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
