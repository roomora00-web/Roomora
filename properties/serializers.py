from rest_framework import serializers
from .models import (
    PropertyType, Amenity, Property, PropertyAmenity,
    PropertyImage, PropertyVideo, PropertyViewing,
    RoomType, RoomTypePricing, UnitType, UnitTypePricing, RentalDuration
)


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ['id', 'name', 'description', 'icon', 'created_at']
        read_only_fields = ['id', 'created_at']


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'category', 'icon', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'accommodation_property', 'image', 'image_type', 'caption', 'is_primary', 'order', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class RoomTypeSerializer(serializers.ModelSerializer):
    available_slots = serializers.ReadOnlyField()
    pricing_models = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = ['id', 'accommodation_property', 'room_type_name', 'occupancy_type', 'total_rooms', 'beds_per_room',
                  'total_capacity', 'available_slots', 'occupied_slots', 'waiting_list_enabled',
                  'bed_type', 'study_desk_available', 'wardrobe_available', 'air_conditioning', 'fan',
                  'wifi_available', 'private_bathroom', 'shared_bathroom_ratio', 'balcony', 'electricity_backup',
                  'gender_restriction', 'preferred_lifestyle', 'study_environment_rating',
                  'pricing_models', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pricing_models(self, obj):
        return RoomTypePricingSerializer(obj.pricing_models.all(), many=True).data


class RoomTypePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTypePricing
        fields = ['id', 'room_type', 'payment_type', 'monthly_price', 'semester_price', 'yearly_price',
                  'daily_price', 'weekly_price', 'security_deposit', 'maintenance_fee', 'registration_fee',
                  'utility_fee', 'currency']
        read_only_fields = ['id']


class UnitTypeSerializer(serializers.ModelSerializer):
    available_units = serializers.ReadOnlyField()
    pricing_models = serializers.SerializerMethodField()
    
    class Meta:
        model = UnitType
        fields = ['id', 'accommodation_property', 'unit_name', 'number_of_units', 'bedrooms', 'bathrooms',
                  'kitchen', 'balcony', 'total_units', 'occupied_units', 'available_units',
                  'furnished_status', 'air_conditioning', 'fan', 'water_heater', 'refrigerator',
                  'washing_machine', 'television', 'generator', 'internet',
                  'shared_apartment_allowed', 'roommate_matching_enabled',
                  'pricing_models', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pricing_models(self, obj):
        return UnitTypePricingSerializer(obj.pricing_models.all(), many=True).data


class UnitTypePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitTypePricing
        fields = ['id', 'unit_type', 'payment_type', 'monthly_price', 'semester_price', 'yearly_price',
                  'two_years_price', 'three_years_price', 'daily_price', 'weekly_price',
                  'security_deposit', 'maintenance_fee', 'registration_fee', 'utility_fee', 'currency']
        read_only_fields = ['id']


class RentalDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalDuration
        fields = ['id', 'accommodation_property', 'duration_type', 'daily_available', 'weekend_available',
                  'weekly_available', 'monthly_available', 'six_months_available', 'semester_available',
                  'one_year_available', 'two_years_available', 'three_years_available', 'custom_lease_available',
                  'minimum_stay_months', 'maximum_stay_months', 'required_advance']
        read_only_fields = ['id']


class PropertySerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.ReadOnlyField(source='uploaded_by.full_name')
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    images = PropertyImageSerializer(many=True, read_only=True)
    room_types = RoomTypeSerializer(many=True, read_only=True)
    unit_types = UnitTypeSerializer(many=True, read_only=True)
    rental_durations = RentalDurationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Property
        fields = ['id', 'uploaded_by', 'uploaded_by_name', 'property_code', 'property_type', 'property_category',
                  'title', 'description', 'address', 'city', 'region', 'country', 'postal_code', 'digital_address',
                  'latitude', 'longitude', 'nearest_institution', 'distance_to_campus', 'walking_time_estimate',
                  'nearby_landmarks', 'suitable_for_students', 'suitable_for_workers', 'suitable_for_families',
                  'suitable_for_couples', 'suitable_for_single_professionals', 'suitable_for_national_service',
                  'suitable_for_expatriates', 'suitable_for_short_stay', 'hostel_type', 'ownership_type',
                  'total_area', 'floor_number', 'total_floors', 'is_available', 'house_rules', 'cancellation_policy',
                  'smoking_allowed', 'pets_allowed', 'guests_allowed', 'maximum_guests', 'curfew_time', 'visitor_policy',
                  'is_verified', 'inspection_date', 'safety_score', 'fire_safety_compliance', 'is_featured', 'status',
                  'rejection_reason', 'security_personnel', 'cctv', 'gated_community', 'emergency_contacts',
                  'water_availability', 'electricity_stability', 'internet_availability', 'utility_billing_method',
                  'views_count', 'saves_count', 'booking_requests_count', 'average_rating', 'total_reviews',
                  'images', 'room_types', 'unit_types', 'rental_durations', 'created_at', 'updated_at']
        read_only_fields = ['id', 'views_count', 'saves_count', 'booking_requests_count', 'average_rating', 'total_reviews', 'created_at', 'updated_at']


class PropertyVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVideo
        fields = ['id', 'accommodation_property', 'video_file', 'video_url', 'thumbnail', 'title', 'description',
                  'is_virtual_tour', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class PropertyViewingSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    property_title = serializers.ReadOnlyField(source='accommodation_property.title')
    
    class Meta:
        model = PropertyViewing
        fields = ['id', 'accommodation_property', 'property_title', 'user', 'user_name', 'scheduled_date',
                  'status', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
