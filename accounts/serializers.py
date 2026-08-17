from rest_framework import serializers
from .models import User, UserProfile, LifestyleProfile, Verification


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number', 
                  'user_type', 'profile_picture', 'is_verified', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'is_verified', 'is_active', 'date_joined', 'last_login']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'user_type', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'gender', 'nationality', 'tenant_type', 'bio',
                  'address', 'city', 'country', 'preferred_language',
                  'institution', 'program', 'level', 'occupation', 'company', 'household_size',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LifestyleProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = LifestyleProfile
        fields = ['id', 'user', 'sleep_schedule', 'wake_time', 'cleanliness_level',
                  'study_habits', 'social_personality', 'visitor_preference', 'noise_tolerance',
                  'smoking_comfortable', 'drinking_comfortable', 'gender_preference',
                  'additional_notes', 'is_complete', 'completion_percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_complete', 'completion_percentage', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Auto-update is_complete if profile is sufficiently filled
        instance = super().update(instance, validated_data)
        if instance.completion_percentage >= 80:
            instance.is_complete = True
            instance.save()
        return instance


class VerificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Verification
        fields = ['id', 'user', 'verification_type', 'document_type', 'document_number',
                  'document_image', 'status', 'rejection_reason', 'submitted_at', 'reviewed_at', 'reviewed_by']
        read_only_fields = ['id', 'submitted_at', 'reviewed_at', 'reviewed_by']


class UserDashboardSerializer(serializers.Serializer):
    """Comprehensive dashboard serializer aggregating user data"""
    user = UserSerializer(read_only=True)
    profile = UserProfileSerializer(read_only=True)
    lifestyle_profile = LifestyleProfileSerializer(read_only=True)
    
    # Dashboard stats
    active_bookings_count = serializers.SerializerMethodField()
    pending_bookings_count = serializers.SerializerMethodField()
    saved_properties_count = serializers.SerializerMethodField()
    current_accommodation = serializers.SerializerMethodField()
    lifestyle_profile_complete = serializers.SerializerMethodField()
    
    def get_active_bookings_count(self, obj):
        from bookings.models import Booking
        return Booking.objects.filter(
            tenant=obj['user'], 
            status__in=['APPROVED', 'COMPLETED']
        ).count()
    
    def get_pending_bookings_count(self, obj):
        from bookings.models import Booking
        return Booking.objects.filter(
            tenant=obj['user'], 
            status='PENDING'
        ).count()
    
    def get_saved_properties_count(self, obj):
        # Placeholder - implement saved properties functionality
        return 0
    
    def get_current_accommodation(self, obj):
        from bookings.models import Booking
        active_booking = Booking.objects.filter(
            tenant=obj['user'], 
            status='APPROVED'
        ).first()
        if active_booking:
            return {
                'property': active_booking.accommodation_property.title,
                'room_type': active_booking.room_type.room_type_name if active_booking.room_type else None,
                'unit_type': active_booking.unit_type.unit_name if active_booking.unit_type else None,
                'move_in_date': active_booking.move_in_date,
            }
        return None
    
    def get_lifestyle_profile_complete(self, obj):
        try:
            lifestyle_profile = LifestyleProfile.objects.get(user=obj['user'])
            return lifestyle_profile.is_complete
        except LifestyleProfile.DoesNotExist:
            return False
