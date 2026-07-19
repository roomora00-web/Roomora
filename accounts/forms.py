from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from .models import User, UserProfile


class RegistrationForm(forms.ModelForm):
    """Registration form with field-level validation as per specification"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password',
        help_text='Must contain uppercase, number, and special character or be 12+ characters long.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )
    agree_terms = forms.BooleanField(
        required=True,
        label='I agree to StayMatch\'s Terms of Service and Privacy Policy'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'gender', 'user_type']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number (+233...)'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email address',
            'phone_number': 'Phone number',
            'gender': 'Gender',
            'user_type': 'I am a',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].choices = [
            ('MALE', 'Male'),
            ('FEMALE', 'Female'),
        ]
        self.fields['user_type'].choices = [
            ('STUDENT', 'Student'),
            ('WORKER', 'Worker'),
            ('FAMILY', 'Family'),
            ('COUPLE', 'Couple'),
            ('NATIONAL_SERVICE', 'National Service Personnel'),
            ('EXPATRIATE', 'Expatriate'),
            ('SHORT_STAY', 'Short-Stay Guest'),
        ]
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not re.match(r'^[a-zA-Z\s\-]{2,50}$', first_name):
            raise ValidationError('First name must be 2–50 characters and contain only letters.')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not re.match(r'^[a-zA-Z\s\-]{2,50}$', last_name):
            raise ValidationError('Last name must be 2–50 characters and contain only letters.')
        return last_name
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered. If you forgot your password, you can reset it.')
        return email.lower()
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Normalize phone number to +233 format
        phone_number = phone_number.strip()
        
        # Remove all non-digit characters
        digits = re.sub(r'[^\d]', '', phone_number)
        
        # Handle different formats
        if phone_number.startswith('+233'):
            # Already in international format
            normalized = f"+233{digits[3:]}"
        elif phone_number.startswith('0'):
            # Local format: 0241234567 -> +233241234567
            normalized = f"+233{digits[1:]}"
        else:
            # Assume it's already digits without prefix
            if len(digits) == 10 and digits.startswith('0'):
                normalized = f"+233{digits[1:]}"
            else:
                normalized = f"+233{digits}"
        
        # Validate Ghana phone number format
        if not re.match(r'^\+233[0-9]{9}$', normalized):
            raise ValidationError('Please enter a valid Ghanaian phone number.')
        
        # Check if phone number already exists
        if User.objects.filter(phone_number=normalized).exists():
            raise ValidationError('This phone number is already in use. If this is your account, please use the login form.')
        
        return normalized
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Password strength validation
        # Must be at least 8 characters AND contain uppercase, number, and special character
        # OR be 12+ characters long
        has_uppercase = any(c.isupper() for c in password)
        has_number = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if len(password) >= 12:
            # Long passwords are acceptable regardless of complexity
            return password
        elif len(password) >= 8 and has_uppercase and has_number and has_special:
            # Short passwords must meet complexity requirements
            return password
        else:
            raise ValidationError('Password must be at least 8 characters and contain uppercase, number, and special character, or be 12+ characters long.')
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if password != confirm_password:
            raise ValidationError('Passwords do not match.')
        
        return confirm_password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.account_status = 'EMAIL_UNVERIFIED'
        
        if commit:
            user.save()
            # Create UserProfile
            UserProfile.objects.create(user=user)
        
        return user


class LoginForm(forms.Form):
    """Login form accepting email or phone number"""
    
    email_or_phone = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email or phone number'}),
        label='Email or phone number'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )
    
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None
    
    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone')
        if not email_or_phone:
            raise ValidationError('This field is required.')
        return email_or_phone
    
    def clean(self):
        email_or_phone = self.cleaned_data.get('email_or_phone')
        password = self.cleaned_data.get('password')
        
        if email_or_phone and password:
            # Try to find user by email or phone
            user = None
            if '@' in email_or_phone:
                # Try email
                try:
                    user = User.objects.get(email=email_or_phone.lower())
                except User.DoesNotExist:
                    pass
            else:
                # Try phone number
                try:
                    # Normalize phone number
                    digits = re.sub(r'[^\d]', '', email_or_phone)
                    if email_or_phone.startswith('+233'):
                        normalized = f"+233{digits[3:]}"
                    elif email_or_phone.startswith('0'):
                        normalized = f"+233{digits[1:]}"
                    else:
                        normalized = f"+233{digits}"
                    user = User.objects.get(phone_number=normalized)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                raise ValidationError('Email/phone or password is incorrect.')
            
            # Check if account is locked
            if user.is_locked():
                raise ValidationError('Too many failed login attempts. Please try again in 30 minutes, or reset your password.')
            
            # Check if account is disabled
            if user.account_status == 'DISABLED':
                raise ValidationError('This account has been disabled. Contact support for details.')
            
            # Check if account is under review
            if user.account_status == 'UNDER_REVIEW':
                raise ValidationError('Your account is under review for security. You can still browse, but booking is temporarily unavailable.')
            
            # Verify password
            if user.check_password(password):
                self.user = user
            else:
                # Increment failed login attempts
                user.increment_failed_login()
                raise ValidationError('Email/phone or password is incorrect.')
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user


class ProfileEnrichmentForm(forms.ModelForm):
    """Profile enrichment form based on user type"""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'address', 'city', 'country']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell us about yourself'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }
    
    def __init__(self, *args, **kwargs):
        user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)
        
        # Add user-type specific fields
        if user_type == 'STUDENT':
            self.fields['institution'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institution'}),
                label='Institution',
                required=False
            )
            self.fields['field_of_study'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Field of study'}),
                label='Field of study',
                required=False
            )
            self.fields['academic_level'] = forms.ChoiceField(
                choices=[
                    ('100', '100'),
                    ('200', '200'),
                    ('300', '300'),
                    ('400', '400'),
                    ('GRADUATED', 'Graduated'),
                ],
                widget=forms.Select(attrs={'class': 'form-control'}),
                label='Academic level',
                required=False
            )
        elif user_type == 'WORKER':
            self.fields['occupation'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
                label='Occupation',
                required=False
            )
            self.fields['company_name'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
                label='Company name',
                required=False
            )
        elif user_type == 'FAMILY':
            self.fields['household_size'] = forms.IntegerField(
                widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of people'}),
                label='Household size',
                required=False
            )
        elif user_type == 'COUPLE':
            self.fields['is_couple_searching'] = forms.BooleanField(
                label='Are you searching for accommodation as a couple?',
                required=False
            )


class ProfilePhotoForm(forms.Form):
    """Profile photo upload form"""
    
    profile_photo = forms.ImageField(
        label='Profile photo',
        required=False,
        help_text='JPEG or PNG, at least 400x400 pixels, maximum 5MB'
    )
    
    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        
        if photo:
            # Validate file size (5MB max)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError('Photo must be less than 5MB.')
            
            # Validate file type
            valid_extensions = ['jpg', 'jpeg', 'png']
            ext = photo.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Photo must be JPEG or PNG format.')
        
        return photo


class PasswordResetRequestForm(forms.Form):
    """Password reset request form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        label='Email address'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Don't reveal if email exists or not
        return email.lower()


class PasswordResetForm(forms.Form):
    """Password reset form with new password"""
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}),
        label='New password',
        help_text='Must contain uppercase, number, and special character or be 12+ characters long.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
        label='Confirm new password'
    )
    
    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        
        # Same validation as registration
        has_uppercase = any(c.isupper() for c in password)
        has_number = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if len(password) >= 12:
            return password
        elif len(password) >= 8 and has_uppercase and has_number and has_special:
            return password
        else:
            raise ValidationError('Password must be at least 8 characters and contain uppercase, number, and special character, or be 12+ characters long.')
    
    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if new_password != confirm_password:
            raise ValidationError('Passwords do not match.')
        
        return confirm_password

from datetime import date

class PersonalInfoForm(forms.ModelForm):
    """Form for personal information updates"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth', 'preferred_name', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'field-input'}),
            'last_name': forms.TextInput(attrs={'class': 'field-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'field-input', 'placeholder': '+233...'}),
            'gender': forms.Select(attrs={'class': 'field-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'field-input', 'type': 'date'}),
            'preferred_name': forms.TextInput(attrs={'class': 'field-input'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'field-input'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'field-input'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'field-input'}),
        }
        
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise ValidationError("You must be at least 16 years old.")
        return dob

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not re.match(r'^[a-zA-Z\s\-]{2,50}$', first_name):
            raise ValidationError('First name must be 2–50 characters and contain only letters.')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not re.match(r'^[a-zA-Z\s\-]{2,50}$', last_name):
            raise ValidationError('Last name must be 2–50 characters and contain only letters.')
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            return phone_number
        phone_number = phone_number.strip()
        digits = re.sub(r'[^\d]', '', phone_number)
        
        if phone_number.startswith('+233'):
            normalized = f"+233{digits[3:]}"
        elif phone_number.startswith('0'):
            normalized = f"+233{digits[1:]}"
        else:
            if len(digits) == 10 and digits.startswith('0'):
                normalized = f"+233{digits[1:]}"
            else:
                normalized = f"+233{digits}"
        
        if not re.match(r'^\+233[0-9]{9}$', normalized):
            raise ValidationError('Please enter a valid Ghanaian phone number (e.g., +233 24 123 4567).')
            
        return normalized

class StudentInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['institution', 'field_of_study', 'academic_level', 'expected_graduation', 'school_email', 'school_year_start', 'school_year_end']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'field-input'}),
            'field_of_study': forms.TextInput(attrs={'class': 'field-input'}),
            'academic_level': forms.Select(attrs={'class': 'field-select'}),
            'expected_graduation': forms.DateInput(attrs={'class': 'field-input', 'type': 'date'}),
            'school_email': forms.EmailInput(attrs={'class': 'field-input'}),
            'school_year_start': forms.DateInput(attrs={'class': 'field-input', 'type': 'date'}),
            'school_year_end': forms.DateInput(attrs={'class': 'field-input', 'type': 'date'}),
        }

class WorkerInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['occupation', 'company_name', 'industry', 'company_location', 'years_of_experience', 'work_email', 'employment_status', 'work_schedule']
        widgets = {
            'occupation': forms.TextInput(attrs={'class': 'field-input'}),
            'company_name': forms.TextInput(attrs={'class': 'field-input'}),
            'industry': forms.TextInput(attrs={'class': 'field-input'}),
            'company_location': forms.TextInput(attrs={'class': 'field-input'}),
            'years_of_experience': forms.TextInput(attrs={'class': 'field-input'}),
            'work_email': forms.EmailInput(attrs={'class': 'field-input'}),
            'employment_status': forms.Select(attrs={'class': 'field-select'}),
            'work_schedule': forms.TextInput(attrs={'class': 'field-input'}),
        }

class FamilyInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['household_size', 'num_children', 'children_age_range', 'special_requirements']
        widgets = {
            'household_size': forms.NumberInput(attrs={'class': 'field-input'}),
            'num_children': forms.NumberInput(attrs={'class': 'field-input'}),
            'children_age_range': forms.TextInput(attrs={'class': 'field-input'}),
            'special_requirements': forms.Textarea(attrs={'class': 'field-textarea', 'rows': 3}),
        }

class NSPInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nsp_organization', 'nsp_location', 'service_end_date', 'service_id']
        widgets = {
            'nsp_organization': forms.TextInput(attrs={'class': 'field-input'}),
            'nsp_location': forms.TextInput(attrs={'class': 'field-input'}),
            'service_end_date': forms.DateInput(attrs={'class': 'field-input', 'type': 'date'}),
            'service_id': forms.TextInput(attrs={'class': 'field-input'}),
        }

class ExpatInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['home_country', 'visa_status', 'purpose_of_stay', 'length_of_stay', 'dietary_requirements']
        widgets = {
            'home_country': forms.TextInput(attrs={'class': 'field-input'}),
            'visa_status': forms.Select(attrs={'class': 'field-select'}),
            'purpose_of_stay': forms.Select(attrs={'class': 'field-select'}),
            'length_of_stay': forms.Select(attrs={'class': 'field-select'}),
            'dietary_requirements': forms.Textarea(attrs={'class': 'field-textarea', 'rows': 3}),
        }

class CommunicationPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'notif_email_enabled', 'notif_sms_enabled', 'notif_push_enabled', 'notif_in_app_enabled',
            'notif_booking_updates', 'notif_property_updates', 'notif_system_alerts', 'notif_marketing',
            'notif_roommate_messages', 'quiet_hours_start', 'quiet_hours_end'
        ]
        widgets = {
            'quiet_hours_start': forms.TimeInput(attrs={'type': 'time', 'class': 'field-input'}),
            'quiet_hours_end': forms.TimeInput(attrs={'type': 'time', 'class': 'field-input'})
        }

from .models import LifestyleProfile

class LifestyleProfileForm(forms.ModelForm):
    class Meta:
        model = LifestyleProfile
        fields = [
            'sleep_time', 'wake_time', 'uses_alarm', 'night_activity_level',
            'personal_cleanliness_level', 'shared_space_cleaning_frequency', 'toilet_cleaning_responsibility',
            'noise_tolerance', 'preferred_noise_level', 'study_noise_preference', 'entertainment_noise_preference',
            'visitor_frequency', 'visitor_overnight_preference', 'smoking_tolerance', 'alcohol_tolerance',
            'study_location', 'study_time', 'cooking_frequency', 'shared_kitchen_comfort', 'food_sharing_comfort',
            'preferred_temperature', 'air_con_preference', 'window_open_preference', 'shared_items_comfort',
            'privacy_preference', 'shared_expense_comfort'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            from django import forms
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'field-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'field-checkbox'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'field-textarea'
                field.widget.attrs['rows'] = 3
            else:
                field.widget.attrs['class'] = 'field-input'
