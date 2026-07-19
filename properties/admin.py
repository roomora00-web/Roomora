from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    PropertyType, Amenity, Property, PropertyAmenity, 
    PropertyImage, PropertyVideo, PropertyViewing,
    RoomType, RoomTypePricing, UnitType, UnitTypePricing, RentalDuration
)


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'category']
    ordering = ['category', 'name']


class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    readonly_fields = ['edit_pricing_link']

    def edit_pricing_link(self, instance):
        if instance.pk:
            url = reverse('admin:properties_roomtype_change', args=[instance.pk])
            return format_html('<a href="{}" target="_blank" style="background:#417690;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;">Edit Prices ↗</a>', url)
        return 'Save first to edit prices'
    edit_pricing_link.short_description = 'Pricing'


class UnitTypeInline(admin.TabularInline):
    model = UnitType
    extra = 0
    readonly_fields = ['edit_pricing_link']

    def edit_pricing_link(self, instance):
        if instance.pk:
            url = reverse('admin:properties_unittype_change', args=[instance.pk])
            return format_html('<a href="{}" target="_blank" style="background:#417690;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;">Edit Prices ↗</a>', url)
        return 'Save first to edit prices'
    edit_pricing_link.short_description = 'Pricing'


class RentalDurationInline(admin.TabularInline):
    model = RentalDuration
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['property_code', 'title', 'property_type', 'city', 'is_available', 'is_verified', 'status', 'uploaded_by', 'created_at']
    list_filter = ['property_type', 'property_category', 'is_available', 'is_verified', 'status', 'city', 'created_at']
    search_fields = ['property_code', 'title', 'address', 'city', 'uploaded_by__email']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {'fields': ('uploaded_by', 'property_code', 'property_type', 'property_category', 'title', 'description')}),
        ('Location Information', {'fields': ('address', 'city', 'region', 'country', 'postal_code', 'digital_address', 'latitude', 'longitude')}),
        ('Nearest Institution', {'fields': ('nearest_institution', 'distance_to_campus', 'walking_time_estimate', 'nearby_landmarks')}),
        ('Target Tenant Type', {'fields': ('suitable_for_students', 'suitable_for_workers', 'suitable_for_families', 'suitable_for_couples', 'suitable_for_single_professionals', 'suitable_for_national_service', 'suitable_for_expatriates', 'suitable_for_short_stay')}),
        ('Hostel-Specific', {'fields': ('hostel_type', 'ownership_type')}),
        ('Property Details', {'fields': ('total_area', 'floor_number', 'total_floors')}),
        ('Availability', {'fields': ('is_available',)}),
        ('Policies', {'fields': ('house_rules', 'cancellation_policy', 'smoking_allowed', 'pets_allowed', 'guests_allowed', 'maximum_guests')}),
        ('Curfew & Visitor Policy', {'fields': ('curfew_time', 'visitor_policy')}),
        ('Verification & Status', {'fields': ('is_verified', 'inspection_date', 'safety_score', 'fire_safety_compliance', 'is_featured', 'status', 'rejection_reason')}),
        ('Safety Information', {'fields': ('security_personnel', 'cctv', 'gated_community', 'emergency_contacts')}),
        ('Utilities Information', {'fields': ('water_availability', 'electricity_stability', 'internet_availability', 'utility_billing_method')}),
        ('Metadata', {'fields': ('views_count', 'saves_count', 'booking_requests_count')}),
    )
    
    inlines = [PropertyAmenityInline, PropertyImageInline, RoomTypeInline, UnitTypeInline, RentalDurationInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['accommodation_property', 'image_type', 'is_primary', 'order', 'uploaded_at']
    list_filter = ['image_type', 'is_primary', 'uploaded_at']
    search_fields = ['accommodation_property__title', 'caption']
    ordering = ['accommodation_property', 'order']


class RoomTypePricingInline(admin.TabularInline):
    model = RoomTypePricing
    extra = 0
    
    fieldsets = (
        ('Pricing', {'fields': ('payment_type', 'monthly_price', 'semester_price', 'yearly_price', 'daily_price', 'weekly_price')}),
        ('Billing Model Specific Pricing', {'fields': ('academic_year_price', 'two_years_price')}),
        ('Billing Model Configuration', {'fields': ('max_semesters', 'min_months', 'max_months', 'allow_two_year_advance', 'early_checkout_allowed', 'early_checkout_penalty')}),
        ('Additional Fees', {'fields': ('security_deposit', 'maintenance_fee', 'registration_fee', 'utility_fee', 'currency')}),
    )


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['room_type_name', 'accommodation_property', 'billing_model', 'occupancy_type', 'total_rooms', 'available_slots', 'created_at']
    list_filter = ['billing_model', 'occupancy_type', 'gender_restriction', 'preferred_lifestyle', 'created_at']
    search_fields = ['room_type_name', 'accommodation_property__title']
    ordering = ['room_type_name']
    
    fieldsets = (
        ('Basic Info', {'fields': ('accommodation_property', 'room_type_name', 'billing_model', 'occupancy_type', 'total_rooms', 'beds_per_room')}),
        ('Capacity', {'fields': ('total_capacity', 'available_slots', 'occupied_slots', 'waiting_list_enabled')}),
        ('Room Features', {'fields': ('bed_type', 'study_desk_available', 'wardrobe_available', 'air_conditioning', 'fan', 'wifi_available', 'private_bathroom', 'shared_bathroom_ratio', 'balcony', 'electricity_backup')}),
        ('Roommate Matching', {'fields': ('gender_restriction', 'preferred_lifestyle', 'study_environment_rating')}),
    )
    
    inlines = [RoomTypePricingInline]


class UnitTypePricingInline(admin.TabularInline):
    model = UnitTypePricing
    extra = 0
    
    fieldsets = (
        ('Pricing', {'fields': ('payment_type', 'monthly_price', 'semester_price', 'yearly_price', 'two_years_price', 'three_years_price', 'daily_price', 'weekly_price')}),
        ('Billing Model Specific Pricing', {'fields': ('academic_year_price',)}),
        ('Billing Model Configuration', {'fields': ('max_semesters', 'min_months', 'max_months', 'allow_two_year_advance', 'early_checkout_allowed', 'early_checkout_penalty')}),
        ('Additional Fees', {'fields': ('security_deposit', 'maintenance_fee', 'registration_fee', 'utility_fee', 'currency')}),
    )


@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ['unit_name', 'accommodation_property', 'billing_model', 'bedrooms', 'bathrooms', 'available_units', 'shared_apartment_allowed', 'created_at']
    list_filter = ['billing_model', 'furnished_status', 'shared_apartment_allowed', 'created_at']
    search_fields = ['unit_name', 'accommodation_property__title']
    ordering = ['unit_name']
    
    fieldsets = (
        ('Basic Info', {'fields': ('accommodation_property', 'unit_name', 'billing_model', 'number_of_units', 'bedrooms', 'bathrooms', 'kitchen', 'balcony')}),
        ('Capacity', {'fields': ('total_units', 'occupied_units', 'available_units')}),
        ('Features', {'fields': ('furnished_status', 'air_conditioning', 'fan', 'water_heater', 'refrigerator', 'washing_machine', 'television', 'generator', 'internet')}),
        ('Shared Apartment', {'fields': ('shared_apartment_allowed', 'roommate_matching_enabled')}),
    )
    
    inlines = [UnitTypePricingInline]


@admin.register(UnitTypePricing)
class UnitTypePricingAdmin(admin.ModelAdmin):
    list_display = ['unit_type', 'payment_type', 'monthly_price', 'yearly_price', 'currency']
    list_filter = ['payment_type', 'currency']
    search_fields = ['unit_type__unit_name']
    ordering = ['unit_type', 'payment_type']


@admin.register(RentalDuration)
class RentalDurationAdmin(admin.ModelAdmin):
    list_display = ['accommodation_property', 'duration_type', 'required_advance']
    list_filter = ['duration_type', 'required_advance']
    search_fields = ['accommodation_property__title']
    ordering = ['-id']


@admin.register(PropertyVideo)
class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = ['accommodation_property', 'title', 'is_virtual_tour', 'uploaded_at']
    list_filter = ['is_virtual_tour', 'uploaded_at']
    search_fields = ['accommodation_property__title', 'title']
    ordering = ['-uploaded_at']


@admin.register(PropertyViewing)
class PropertyViewingAdmin(admin.ModelAdmin):
    list_display = ['accommodation_property', 'user', 'scheduled_date', 'status', 'created_at']
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['accommodation_property__title', 'user__email']
    ordering = ['-scheduled_date']
