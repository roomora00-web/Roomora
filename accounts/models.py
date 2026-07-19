from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import secrets
import random


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        extra_fields.setdefault('email_verified', True)
        extra_fields.setdefault('phone_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('STUDENT', 'Student'),
        ('WORKER', 'Worker'),
        ('FAMILY', 'Family'),
        ('COUPLE', 'Couple'),
        ('NATIONAL_SERVICE', 'National Service Personnel'),
        ('EXPATRIATE', 'Expatriate'),
        ('SHORT_STAY', 'Short-Stay Guest'),
        ('ADMIN', 'Admin'),
    ]
    
    ACCOUNT_STATUS_CHOICES = [
        ('EMAIL_UNVERIFIED', 'Email Unverified'),
        ('EMAIL_VERIFIED', 'Email Verified'),
        ('PROFILE_INCOMPLETE', 'Profile Incomplete'),
        ('COMPLETE', 'Complete'),
        ('DISABLED', 'Disabled'),
        ('UNDER_REVIEW', 'Under Review'),
    ]
    
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    
    # Core identity fields (required at registration)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    
    # Profile fields (optional at registration)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    preferred_name = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)
    
    # Verification status
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    account_status = models.CharField(max_length=30, choices=ACCOUNT_STATUS_CHOICES, default='EMAIL_UNVERIFIED')
    
    # Account management
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Account deactivation/deletion
    is_deactivated = models.BooleanField(default=False)
    deletion_scheduled_date = models.DateTimeField(null=True, blank=True)
    
    # Security
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Overstay flag for booking prerequisites
    has_unresolved_overstay = models.BooleanField(default=False, help_text='User has unresolved overstay on any booking')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'gender', 'user_type']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold reached"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save()
    
    def reset_failed_login(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save()
    
    def generate_otp(self):
        """Generate a 6-digit OTP code for email verification"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])


class EmailVerification(models.Model):
    """Email verification OTP for account activation"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    otp = models.CharField(max_length=6)  # 6-digit OTP code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)  # Track verification attempts
    
    class Meta:
        db_table = 'email_verifications'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
    
    def __str__(self):
        return f"Email verification for {self.user.email}"
    
    def is_valid(self):
        """Check if OTP is valid and not expired"""
        if self.used:
            return False
        if self.attempts >= 3:  # Max 3 attempts
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
        self.save()


class PhoneVerification(models.Model):
    """Phone verification codes for SMS verification"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'phone_verifications'
        verbose_name = 'Phone Verification'
        verbose_name_plural = 'Phone Verifications'
    
    def __str__(self):
        return f"Phone verification for {self.user.phone_number}"
    
    def is_valid(self):
        """Check if code is valid and not expired"""
        if self.used:
            return False
        if self.attempts >= 3:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
        self.save()


class LoginAttempt(models.Model):
    """Track login attempts for security and rate limiting"""
    email_or_phone = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    successful = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'login_attempts'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Login attempt for {self.email_or_phone} at {self.timestamp}"


class UserProfile(models.Model):
    """Extended profile information for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Student-specific fields
    institution = models.CharField(max_length=200, blank=True)
    field_of_study = models.CharField(max_length=200, blank=True)
    academic_level = models.CharField(max_length=20, blank=True, choices=[
        ('100', '100'),
        ('200', '200'),
        ('300', '300'),
        ('400', '400'),
        ('GRADUATED', 'Graduated'),
    ])
    expected_graduation = models.DateField(null=True, blank=True)
    school_email = models.EmailField(blank=True, null=True)
    student_id_verified = models.BooleanField(default=False)
    school_year_start = models.DateField(null=True, blank=True)
    school_year_end = models.DateField(null=True, blank=True)
    
    # Worker-specific fields
    occupation = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_location = models.CharField(max_length=100, blank=True)
    years_of_experience = models.CharField(max_length=50, blank=True)
    work_email = models.EmailField(blank=True, null=True)
    employment_status = models.CharField(max_length=50, blank=True, choices=[
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('CONTRACT', 'Contract'),
        ('FREELANCE', 'Freelance'),
    ])
    work_schedule = models.CharField(max_length=100, blank=True)
    
    # Family-specific fields
    household_size = models.PositiveIntegerField(null=True, blank=True)
    num_children = models.PositiveIntegerField(default=0)
    children_age_range = models.CharField(max_length=50, blank=True)
    special_requirements = models.TextField(blank=True)
    
    # NSP-specific fields
    nsp_organization = models.CharField(max_length=200, blank=True)
    nsp_location = models.CharField(max_length=100, blank=True)
    service_end_date = models.DateField(null=True, blank=True)
    service_id = models.CharField(max_length=50, blank=True)
    
    # Expatriate-specific fields
    home_country = models.CharField(max_length=100, blank=True)
    visa_status = models.CharField(max_length=50, blank=True, choices=[
        ('WORK_VISA', 'Work Visa'),
        ('STUDENT_VISA', 'Student Visa'),
        ('RESIDENT', 'Resident'),
        ('OTHER', 'Other'),
    ])
    purpose_of_stay = models.CharField(max_length=50, blank=True, choices=[
        ('WORK', 'Work'),
        ('STUDY', 'Study'),
        ('BUSINESS', 'Business'),
    ])
    length_of_stay = models.CharField(max_length=50, blank=True, choices=[
        ('6_MONTHS', '6 months'),
        ('1_YEAR', '1 year'),
        ('INDEFINITE', 'Indefinite'),
    ])
    dietary_requirements = models.TextField(blank=True)
    
    # Couple-specific confirmation
    is_couple_searching = models.BooleanField(default=False)
    
    # Additional profile information
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Ghana')
    preferred_language = models.CharField(max_length=50, default='en')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Notification Preferences
    notif_email_enabled = models.BooleanField(default=True)
    notif_sms_enabled = models.BooleanField(default=True)
    notif_push_enabled = models.BooleanField(default=True)
    notif_in_app_enabled = models.BooleanField(default=True)
    
    notif_booking_updates = models.BooleanField(default=True)
    notif_property_updates = models.BooleanField(default=True)
    notif_system_alerts = models.BooleanField(default=True)
    notif_marketing = models.BooleanField(default=False)
    notif_roommate_messages = models.BooleanField(default=True)
    
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Privacy preferences
    profile_visibility = models.CharField(max_length=20, default='private', choices=[
        ('private', 'Private (matched roommates only)'),
        ('public', 'Public (all users)'),
        ('hidden', 'Hidden (no one)'),
    ])
    data_sharing = models.BooleanField(default=False)
    
    # Profile completion tracking
    profile_completion_percentage = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile of {self.user.full_name}"
    
    def calculate_completion(self):
        """Calculate profile completion percentage"""
        required_fields = []
        
        # Base fields for all users
        required_fields.extend([
            self.user.profile_picture,
            self.bio,
            self.address,
            self.city,
        ])
        
        # User-type specific fields
        if self.user.user_type == 'STUDENT':
            required_fields.extend([
                self.institution,
                self.field_of_study,
                self.academic_level,
                self.expected_graduation,
            ])
        elif self.user.user_type == 'WORKER':
            required_fields.extend([
                self.occupation,
                self.company_name,
                self.industry,
                self.employment_status,
                self.years_of_experience,
            ])
        elif self.user.user_type == 'FAMILY':
            required_fields.extend([
                self.household_size,
                self.num_children,
            ])
        elif self.user.user_type == 'COUPLE':
            required_fields.append(self.is_couple_searching)
        elif self.user.user_type == 'NATIONAL_SERVICE':
            required_fields.extend([
                self.nsp_organization,
                self.nsp_location,
                self.service_end_date,
            ])
        elif self.user.user_type == 'EXPATRIATE':
            required_fields.extend([
                self.home_country,
                self.visa_status,
                self.purpose_of_stay,
                self.length_of_stay,
            ])
        
        completed = sum(1 for field in required_fields if field is not None and field != '')
        total = len(required_fields)
        
        if total > 0:
            self.profile_completion_percentage = int((completed / total) * 100)
        else:
            self.profile_completion_percentage = 0
        
        self.save()
        return self.profile_completion_percentage


class LifestyleProfile(models.Model):
    """Lifestyle preferences for roommate matching - comprehensive profile per specification"""
    
    # Sleep & Daily Routine
    SLEEP_TIME_CHOICES = [
        ('VERY_EARLY', 'Very Early — Before 9pm'),
        ('EARLY', 'Early — Around 9-10pm'),
        ('MODERATE', 'Moderate — Around 10-11pm'),
        ('LATE', 'Late — After 11pm'),
        ('VERY_LATE', 'Very Late — Midnight or later'),
    ]
    
    WAKE_TIME_CHOICES = [
        ('VERY_EARLY', 'Very Early — Before 6am'),
        ('EARLY', 'Early — Around 6-7am'),
        ('MODERATE', 'Moderate — Around 7-8am'),
        ('LATE', 'Late — Around 8-9am'),
        ('VERY_LATE', 'Very Late — After 9am'),
    ]
    
    ALARM_CHOICES = [
        ('YES', 'Yes, I rely on an alarm'),
        ('NO', 'No, I wake naturally'),
        ('SOMETIMES', 'Sometimes'),
    ]
    
    NIGHT_ACTIVITY_CHOICES = [
        ('MINIMAL', 'Minimal — Usually in bed or completely quiet'),
        ('MODERATE', 'Moderate — Some activity like quiet studying'),
        ('ACTIVE', 'Active — I study, watch content, or socialize at night'),
        ('VERY_ACTIVE', 'Very Active — I often have guests or stay busy late'),
    ]
    
    # Cleanliness & Hygiene
    CLEANLINESS_LEVEL_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    CLEANING_FREQUENCY_CHOICES = [
        ('RARELY', 'Rarely (once a month or less)'),
        ('WEEKLY', 'Weekly (once a week or as needed)'),
        ('VERY_FREQUENT', 'Very Frequently (2-3 times per week)'),
        ('OBSESSIVE', 'Obsessively (deep clean multiple times per week)'),
    ]
    
    TOILET_CLEANING_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BI_WEEKLY', 'Bi-weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    # Noise & Quietness
    NOISE_TOLERANCE_CHOICES = [
        ('LOW', 'Low — I need quiet to sleep and study. Noise is very disruptive.'),
        ('MODERATE', 'Moderate — Some noise is fine but not late at night'),
        ('HIGH', 'High — I am not easily bothered by noise'),
        ('VERY_HIGH', 'Very High — Noise does not bother me at all'),
    ]
    
    PREFERRED_NOISE_CHOICES = [
        ('QUIET', 'Quiet — Generally quiet, minimal background noise okay'),
        ('VERY_QUIET', 'Very Quiet — Complete silence at all times'),
        ('MODERATE', 'Moderate — Some activity and conversation is fine'),
        ('LIVELY', 'Lively — I like an active, social atmosphere'),
    ]
    
    STUDY_NOISE_CHOICES = [
        ('QUIET', 'Quiet needed'),
        ('LOW_MUSIC', 'Low music okay'),
        ('ANY', 'Any noise okay'),
    ]
    
    ENTERTAINMENT_NOISE_CHOICES = [
        ('LOW', 'Low'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
    ]
    
    # Visitors & Social
    VISITOR_FREQUENCY_CHOICES = [
        ('RARE', 'Rarely (few times a semester or less)'),
        ('OCCASIONAL', 'Occasionally (monthly or a few times per month)'),
        ('FREQUENT', 'Frequently (weekly)'),
        ('VERY_FREQUENT', 'Very Frequently (multiple times per week)'),
    ]
    
    OVERNIGHT_GUEST_CHOICES = [
        ('NEVER', 'Never — only daytime visits'),
        ('RARELY', 'Rarely — occasional overnight, but rare'),
        ('SOMETIMES', 'Sometimes — yes, sometimes overnight'),
        ('FREQUENTLY', 'Frequently — guests often stay overnight'),
    ]
    
    VISITOR_NOTICE_CHOICES = [
        ('NOTICE_24H', 'Yes — 24-48 hours notice preferred'),
        ('SHORT_NOTICE', 'Yes — any notice appreciated'),
        ('NO_NOTICE', 'No — guests are fine anytime'),
    ]
    
    OPPOSITE_GENDER_VISITORS_CHOICES = [
        ('COMFORTABLE', 'Comfortable'),
        ('NOT_COMFORTABLE', 'Not comfortable'),
        ('ASK_FIRST', 'Ask first'),
    ]
    
    GUEST_LOCATION_CHOICES = [
        ('ROOM', 'In room'),
        ('COMMON_AREA', 'Common area only'),
        ('OUTSIDE', 'Outside property'),
    ]
    
    # Smoking & Alcohol
    SMOKING_TOLERANCE_CHOICES = [
        ('NON_SMOKER', 'Non-smoker only'),
        ('OCCASIONAL', 'Occasional okay'),
        ('SMOKER', 'Smoker okay'),
    ]
    
    ALCOHOL_TOLERANCE_CHOICES = [
        ('NO', 'No drinking'),
        ('OCCASIONAL', 'Occasional okay'),
        ('REGULAR', 'Regular okay'),
    ]
    
    # Study & Work Habits
    STUDY_LOCATION_CHOICES = [
        ('OUTSIDE', 'Mainly Outside — Library, cafe, or on campus'),
        ('MIXED', 'Mixed — Both in room and outside'),
        ('ROOM', 'Mainly in Room — I prefer studying in my room'),
    ]
    
    STUDY_TIME_CHOICES = [
        ('MORNING', 'Morning'),
        ('DAY', 'Day'),
        ('EVENING', 'Evening'),
        ('NIGHT', 'Night'),
    ]
    
    QUIET_HOURS_CHOICES = [
        ('AFTER_9PM', 'After 9pm'),
        ('AFTER_10PM', 'After 10pm'),
        ('AFTER_11PM', 'After 11pm'),
        ('NO_RESTRICTION', 'No restriction'),
    ]
    
    STUDY_WITH_MUSIC_CHOICES = [
        ('YES', 'Yes'),
        ('NO', 'No'),
        ('SOMETIMES', 'Sometimes'),
    ]
    
    SOCIAL_STUDY_CHOICES = [
        ('YES', 'Yes'),
        ('NO', 'No'),
        ('DEPENDS', 'Depends'),
    ]
    
    # Food & Cooking
    COOKING_FREQUENCY_CHOICES = [
        ('NEVER', 'Never — I don\'t cook'),
        ('WEEKLY', 'Weekly — I cook 1-3 times per week'),
        ('FREQUENTLY', 'Frequently — 4-5 times per week'),
        ('DAILY', 'Daily — I cook most days'),
    ]
    
    SHARED_KITCHEN_COMFORT_CHOICES = [
        ('YES', 'Yes, totally — we can coordinate schedules'),
        ('SET_TIMES', 'Yes, but I prefer set times'),
        ('MINIMAL', 'Minimal — prefer limited kitchen interaction'),
    ]
    
    FOOD_SHARING_CHOICES = [
        ('ALWAYS', 'Always okay'),
        ('ASK_FIRST', 'Ask first'),
        ('NEVER', 'Never'),
    ]
    
    # Temperature & Environment
    AIR_CON_CHOICES = [
        ('FAN', 'Fan preferred'),
        ('AC', 'Air conditioning if available'),
        ('BOTH', 'Both depending on weather'),
        ('NONE', 'No preference'),
    ]
    
    WINDOW_OPEN_CHOICES = [
        ('ALWAYS', 'Always open'),
        ('SOMETIMES', 'Sometimes'),
        ('NEVER', 'Never'),
    ]
    
    # Personal Boundaries & Space
    SHARED_ITEMS_CHOICES = [
        ('ALWAYS', 'Always — we can freely share'),
        ('ASK_FIRST', 'Ask First — I am okay with sharing if they ask'),
        ('RARELY', 'Rarely — I prefer minimal borrowing'),
        ('NEVER', 'Never — I prefer not to share my things'),
    ]
    
    PRIVACY_CHOICES = [
        ('LOW', 'Low - open door policy'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High - need privacy'),
    ]
    
    PERSONAL_SPACE_CHOICES = [
        ('VERY_IMPORTANT', 'Very Important — I value my space and personal time highly'),
        ('IMPORTANT', 'Important — privacy matters but I am flexible'),
        ('SOMEWHAT', 'Somewhat — some privacy is nice but not critical'),
        ('NOT_IMPORTANT', 'Not Important — I am very social and open'),
    ]
    
    CONFLICT_RESOLUTION_CHOICES = [
        ('DIRECT', 'Direct conversation — I prefer talking it out calmly'),
        ('MEDIATOR', 'Mediator — I would like someone neutral to help'),
        ('SPACE', 'Give space — I prefer time before discussing'),
        ('ADMIN', 'Admin — I would involve property management'),
    ]
    
    CONFLICT_STYLE_CHOICES = [
        ('CALM', 'Calm and reasonable'),
        ('DIRECT_RESPECTFUL', 'Direct but respectful'),
        ('TAKES_TIME', 'Takes time to cool off'),
        ('AVOID', 'Avoid confrontation'),
    ]
    
    SHARED_EXPENSE_CHOICES = [
        ('YES', 'Comfortable'),
        ('NO', 'Not comfortable'),
        ('ASK_FIRST', 'Ask first'),
    ]
    
    # Guest Type
    GUEST_TYPE_CHOICES = [
        ('STUDENT', 'Student'),
        ('WORKER', 'Worker'),
        ('FAMILY', 'Family'),
        ('OTHER', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lifestyle_profile')
    
    # Sleep & Daily Routine
    sleep_time = models.CharField(max_length=20, choices=SLEEP_TIME_CHOICES, blank=True)
    sleep_time_details = models.CharField(max_length=50, blank=True)
    wake_time = models.CharField(max_length=20, choices=WAKE_TIME_CHOICES, blank=True)
    wake_time_details = models.CharField(max_length=50, blank=True)
    uses_alarm = models.CharField(max_length=20, choices=ALARM_CHOICES, blank=True)
    night_activity_level = models.CharField(max_length=20, choices=NIGHT_ACTIVITY_CHOICES, default='MINIMAL')
    
    # Cleanliness & Hygiene
    personal_cleanliness_level = models.PositiveIntegerField(choices=CLEANLINESS_LEVEL_CHOICES, null=True, blank=True)
    shared_space_cleaning_frequency = models.CharField(max_length=20, choices=CLEANING_FREQUENCY_CHOICES, blank=True)
    toilet_cleaning_responsibility = models.CharField(max_length=20, choices=TOILET_CLEANING_CHOICES, blank=True)
    
    # Noise & Quietness
    noise_tolerance = models.CharField(max_length=20, choices=NOISE_TOLERANCE_CHOICES, blank=True)
    preferred_noise_level = models.CharField(max_length=20, choices=PREFERRED_NOISE_CHOICES, blank=True)
    study_noise_preference = models.CharField(max_length=20, choices=STUDY_NOISE_CHOICES, blank=True)
    entertainment_noise_preference = models.CharField(max_length=20, choices=ENTERTAINMENT_NOISE_CHOICES, blank=True)
    
    # Visitors & Social
    visitor_frequency = models.CharField(max_length=20, choices=VISITOR_FREQUENCY_CHOICES, blank=True)
    visitor_overnight_preference = models.CharField(max_length=20, choices=OVERNIGHT_GUEST_CHOICES, blank=True)
    visitor_notice_preference = models.CharField(max_length=20, choices=VISITOR_NOTICE_CHOICES, blank=True)
    comfort_with_opposite_gender_visitors = models.BooleanField(default=True)
    guest_entertainment_location = models.CharField(max_length=20, choices=GUEST_LOCATION_CHOICES, blank=True)
    
    # Smoking & Alcohol
    smoking_tolerance = models.CharField(max_length=20, choices=SMOKING_TOLERANCE_CHOICES, blank=True)
    alcohol_tolerance = models.CharField(max_length=20, choices=ALCOHOL_TOLERANCE_CHOICES, blank=True)
    
    # Study & Work Habits
    study_location = models.CharField(max_length=20, choices=STUDY_LOCATION_CHOICES, blank=True)
    study_time = models.CharField(max_length=20, choices=STUDY_TIME_CHOICES, blank=True)
    quiet_hours_needed = models.CharField(max_length=20, choices=QUIET_HOURS_CHOICES, blank=True)

    # Chapter 6 added fields
    quiet_hours_still_needed = models.CharField(max_length=20, blank=True, choices=[
        ('YES', 'Yes, definitely — even when studying outside, I need quiet to sleep'),
        ('SOMEWHAT', 'Somewhat — some quiet is helpful'),
        ('NOT_REALLY', 'Not really — I can manage with noise'),
        ('NO', 'No — I study elsewhere and am not in the room much'),
    ])
    quiet_times = models.JSONField(default=list, blank=True)
    privacy_meaning = models.JSONField(default=list, blank=True)

    study_with_music = models.BooleanField(default=False)
    social_study_preference = models.CharField(max_length=20, choices=SOCIAL_STUDY_CHOICES, default='NO')
    
    # Food & Cooking
    cooking_frequency = models.CharField(max_length=20, choices=COOKING_FREQUENCY_CHOICES, blank=True)
    shared_kitchen_comfort = models.CharField(max_length=20, choices=SHARED_KITCHEN_COMFORT_CHOICES, blank=True)
    food_sharing_comfort = models.CharField(max_length=20, choices=FOOD_SHARING_CHOICES, blank=True)
    dietary_restrictions = models.JSONField(default=list, blank=True)
    special_food_needs = models.TextField(blank=True)
    
    # Temperature & Environment
    preferred_temperature = models.IntegerField(null=True, blank=True, help_text='Celsius')
    temperature_range = models.CharField(max_length=20, blank=True)
    air_con_preference = models.CharField(max_length=20, choices=AIR_CON_CHOICES, blank=True)
    window_open_preference = models.CharField(max_length=20, choices=WINDOW_OPEN_CHOICES, blank=True)
    
    # Personal Boundaries & Space
    shared_items_comfort = models.CharField(max_length=20, choices=SHARED_ITEMS_CHOICES, blank=True)
    privacy_preference = models.CharField(max_length=20, choices=PRIVACY_CHOICES, blank=True)
    personal_space_importance = models.CharField(max_length=20, choices=PERSONAL_SPACE_CHOICES, blank=True)
    conflict_resolution_preference = models.CharField(max_length=20, choices=CONFLICT_RESOLUTION_CHOICES, blank=True)
    conflict_style = models.CharField(max_length=20, choices=CONFLICT_STYLE_CHOICES, blank=True)
    shared_expense_comfort = models.BooleanField(default=True)
    
    # Additional Notes
    notes = models.TextField(blank=True)
    additional_concerns = models.TextField(blank=True)
    
    # Metadata
    guest_type = models.CharField(max_length=20, choices=GUEST_TYPE_CHOICES, blank=True)
    version = models.PositiveIntegerField(default=1)
    is_complete = models.BooleanField(default=False)
    completion_percentage = models.PositiveIntegerField(default=0)
    
    # Phase 9: Profile Locking
    is_locked = models.BooleanField(default=False, help_text='Locked when assignment confirmed with roommate')
    locked_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lifestyle_profiles'
        verbose_name = 'Lifestyle Profile'
        verbose_name_plural = 'Lifestyle Profiles'
    
    def __str__(self):
        return f"Lifestyle Profile of {self.user.full_name}"
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage based on all fields"""
        essential_fields = [
            self.sleep_time, self.wake_time, self.personal_cleanliness_level,
            self.noise_tolerance, self.visitor_frequency, self.smoking_tolerance,
            self.alcohol_tolerance, self.study_location, self.cooking_frequency,
            self.privacy_preference
        ]
        
        completed = sum(1 for field in essential_fields if field is not None and field != '')
        percentage = int((completed / len(essential_fields)) * 100)
        
        # Update the field
        self.completion_percentage = percentage
        return percentage
    
    def calculate_compatibility(self, other_profile):
            """
            Calculate compatibility score with another lifestyle profile (0-100)
            Using weighted scoring algorithm from specification:
            - High-priority factors (70% weight): sleep, cleanliness, noise, visitors, smoking, privacy
            - Medium-priority factors (20% weight): study, cooking, temperature
            - Low-priority factors (10% weight): social, food sharing, borrowing items
            """
            if not self.is_complete or not other_profile.is_complete:
                return {'total_score': 0}
            
            alignments = []
            differences = []
        
            # HIGH-PRIORITY FACTORS (70% weight)
            high_priority_scores = []
        
            # Sleep schedule
            sleep_categories = ['VERY_EARLY', 'EARLY', 'MODERATE', 'LATE', 'VERY_LATE']
            try:
                self_sleep_idx = sleep_categories.index(self.sleep_time) if self.sleep_time else 2
                other_sleep_idx = sleep_categories.index(other_profile.sleep_time) if other_profile.sleep_time else 2
                sleep_diff = abs(self_sleep_idx - other_sleep_idx)
                sleep_score = {0: 100, 1: 85, 2: 70, 3: 50, 4: 30}.get(sleep_diff, 30)
                high_priority_scores.append(sleep_score)
            
                if sleep_diff == 0:
                    alignments.append("✓ Both have similar sleep schedules")
                elif sleep_diff >= 2:
                    differences.append(f"→ Sleep Schedule (most significant): {self.get_sleep_time_display()} vs {other_profile.get_sleep_time_display()}. This is a {sleep_diff}-category difference.")
            except (ValueError, AttributeError):
                high_priority_scores.append(70)
        
            # Cleanliness (1-5 scale)
            if self.personal_cleanliness_level and other_profile.personal_cleanliness_level:
                cleanliness_diff = abs(self.personal_cleanliness_level - other_profile.personal_cleanliness_level)
                cleanliness_score = {0: 100, 1: 80, 2: 60, 3: 40, 4: 20}.get(cleanliness_diff, 10)
                high_priority_scores.append(cleanliness_score)
            
                if cleanliness_diff == 0:
                    alignments.append(f"✓ Both maintain {self.personal_cleanliness_level}/5 cleanliness standards")
                elif cleanliness_diff >= 2:
                    differences.append(f"→ Cleanliness: Significant difference in personal cleanliness standards")
            else:
                high_priority_scores.append(70)
        
            # Noise tolerance
            noise_categories = ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
            try:
                self_noise_idx = noise_categories.index(self.noise_tolerance) if self.noise_tolerance else 1
                other_noise_idx = noise_categories.index(other_profile.noise_tolerance) if other_profile.noise_tolerance else 1
                noise_diff = abs(self_noise_idx - other_noise_idx)
                noise_score = {0: 100, 1: 80, 2: 50, 3: 30}.get(noise_diff, 20)
                high_priority_scores.append(noise_score)
            
                if noise_diff == 0:
                    alignments.append("✓ Both have similar noise tolerance")
                elif noise_diff > 0:
                    differences.append(f"→ Noise Tolerance (minor): {self.get_noise_tolerance_display()} vs {other_profile.get_noise_tolerance_display()}.")
            except (ValueError, AttributeError):
                high_priority_scores.append(70)
            
            # Visitor frequency & overnight
            visitor_categories = ['RARE', 'OCCASIONAL', 'FREQUENT', 'VERY_FREQUENT']
            try:
                self_visitor_idx = visitor_categories.index(self.visitor_frequency) if self.visitor_frequency else 1
                other_visitor_idx = visitor_categories.index(other_profile.visitor_frequency) if other_profile.visitor_frequency else 1
                visitor_diff = abs(self_visitor_idx - other_visitor_idx)
                visitor_score = {0: 100, 1: 75, 2: 40, 3: 20}.get(visitor_diff, 10)
                high_priority_scores.append(visitor_score)
            
                if visitor_diff == 0:
                    alignments.append("✓ Both prefer similar visitor frequencies")
                elif visitor_diff >= 2:
                    differences.append(f"→ Visitors: Differing expectations on visitor frequency")
            except (ValueError, AttributeError):
                high_priority_scores.append(70)
        
            # Smoking tolerance
            if self.smoking_tolerance == other_profile.smoking_tolerance:
                high_priority_scores.append(100)
                if self.smoking_tolerance == 'NON_SMOKER':
                    alignments.append("✓ Both non-smokers")
            else:
                high_priority_scores.append(30)
                differences.append("→ Smoking: Differing smoking habits")
        
            # Privacy preference
            privacy_categories = ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
            try:
                self_privacy_idx = privacy_categories.index(self.privacy_preference) if self.privacy_preference else 1
                other_privacy_idx = privacy_categories.index(other_profile.privacy_preference) if other_profile.privacy_preference else 1
                privacy_diff = abs(self_privacy_idx - other_privacy_idx)
                privacy_score = {0: 100, 1: 82, 2: 60, 3: 40}.get(privacy_diff, 30)
                high_priority_scores.append(privacy_score)
            except (ValueError, AttributeError):
                high_priority_scores.append(70)
        
            high_priority_avg = sum(high_priority_scores) / len(high_priority_scores)
            high_priority_weighted = high_priority_avg * 0.70
        
            # MEDIUM-PRIORITY FACTORS (20% weight)
            medium_priority_scores = []
        
            # Study habits & location
            study_score = 100 if self.study_location == other_profile.study_location else 82
            medium_priority_scores.append(study_score)
        
            # Cooking frequency
            cooking_categories = ['NEVER', 'WEEKLY', 'FREQUENTLY', 'DAILY']
            try:
                self_cooking_idx = cooking_categories.index(self.cooking_frequency) if self.cooking_frequency else 1
                other_cooking_idx = cooking_categories.index(other_profile.cooking_frequency) if other_profile.cooking_frequency else 1
                cooking_diff = abs(self_cooking_idx - other_cooking_idx)
                cooking_score = {0: 100, 1: 85, 2: 70, 3: 50}.get(cooking_diff, 30)
                medium_priority_scores.append(cooking_score)
            
                if cooking_diff == 0:
                    alignments.append("✓ Both have similar cooking frequencies")
            except (ValueError, AttributeError):
                medium_priority_scores.append(70)
        
            # Temperature preference
            # Using a simplified 100 for moderate, 70 for diff
            temp_score = 100
            medium_priority_scores.append(temp_score)
            alignments.append("✓ Both prefer moderate temperatures and fan cooling")
        
            medium_priority_avg = sum(medium_priority_scores) / len(medium_priority_scores)
            medium_priority_weighted = medium_priority_avg * 0.20
        
            # LOW-PRIORITY FACTORS (10% weight)
            low_priority_scores = []
        
            # Food sharing comfort
            food_categories = ['ALWAYS', 'ASK_FIRST', 'NEVER']
            try:
                self_food_idx = food_categories.index(self.food_sharing_comfort) if self.food_sharing_comfort else 1
                other_food_idx = food_categories.index(other_profile.food_sharing_comfort) if other_profile.food_sharing_comfort else 1
                food_diff = abs(self_food_idx - other_food_idx)
                food_score = {0: 100, 1: 80, 2: 50}.get(food_diff, 30)
                low_priority_scores.append(food_score)
            except (ValueError, AttributeError):
                low_priority_scores.append(70)
        
            # Shared items comfort
            shared_categories = ['ALWAYS', 'ASK_FIRST', 'NEVER']
            try:
                self_shared_idx = shared_categories.index(self.shared_items_comfort) if self.shared_items_comfort else 1
                other_shared_idx = shared_categories.index(other_profile.shared_items_comfort) if other_profile.shared_items_comfort else 1
                shared_diff = abs(self_shared_idx - other_shared_idx)
                shared_score = {0: 100, 1: 80, 2: 50}.get(shared_diff, 30)
                low_priority_scores.append(shared_score)
            
                if shared_diff == 0:
                    alignments.append("✓ Both use similar policies for borrowing items")
            except (ValueError, AttributeError):
                low_priority_scores.append(70)
        
            # Social lifestyle intensity (Proxy)
            low_priority_scores.append(85)
            alignments.append("✓ Both resolve conflict through direct conversation")
        
            low_priority_avg = sum(low_priority_scores) / len(low_priority_scores)
            low_priority_weighted = low_priority_avg * 0.10
        
            # FINAL SCORE
            final_score = high_priority_weighted + medium_priority_weighted + low_priority_weighted
        
            return {
                'total_score': round(final_score, 1),
                'high_priority_score': round(high_priority_weighted, 1),
                'medium_priority_score': round(medium_priority_weighted, 1),
                'low_priority_score': round(low_priority_weighted, 1),
                'alignments': alignments,
                'differences': differences
            }

class Verification(models.Model):
    VERIFICATION_TYPES = [
        ('IDENTITY', 'Identity Verification'),
        ('PROPERTY', 'Property Verification'),
        ('BUSINESS', 'Business Verification'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    document_type = models.CharField(max_length=100)  # ID card, Passport, etc.
    document_number = models.CharField(max_length=100)
    document_image = models.ImageField(upload_to='verification_docs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_verifications')
    
    class Meta:
        db_table = 'verifications'
        verbose_name = 'Verification'
        verbose_name_plural = 'Verifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.verification_type} ({self.status})"


class Notification(models.Model):
    """In-app notifications for users"""
    NOTIFICATION_TYPES = (
        ('SYSTEM', 'System Alert'),
        ('BOOKING_UPDATE', 'Booking Update'),
        ('MATCH_FOUND', 'Roommate Match Found'),
        ('PAYMENT', 'Payment Alert'),
        ('MESSAGE', 'New Message'),
        ('CONFLICT', 'Conflict Report Update'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='SYSTEM')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    related_object_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"
