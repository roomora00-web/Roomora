from django.db import models
from django.conf import settings
from django.utils import timezone


class PropertyType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For UI display
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_types'
        verbose_name = 'Property Type'
        verbose_name_plural = 'Property Types'
    
    def __str__(self):
        return self.name


class Amenity(models.Model):
    CATEGORY_CHOICES = [
        ('GENERAL', 'General'),
        ('SAFETY', 'Safety'),
        ('UTILITIES', 'Utilities'),
        ('INTERNET', 'Internet'),
        ('KITCHEN', 'Kitchen'),
        ('BATHROOM', 'Bathroom'),
        ('LAUNDRY', 'Laundry'),
        ('OUTDOOR', 'Outdoor'),
        ('STUDY', 'Study'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'amenities'
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class Property(models.Model):
    PROPERTY_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('HOSTEL', 'Hostel'),
        ('APARTMENT', 'Apartment'),
        ('FLAT', 'Flat'),
        ('COMPOUND_HOUSE', 'Compound House'),
        ('TOWNHOUSE', 'Townhouse'),
        ('DUPLEX', 'Duplex'),
        ('VILLA', 'Villa'),
        ('STUDIO', 'Studio'),
        ('STUDENT_APARTMENT', 'Student Apartment'),
    ]
    
    PROPERTY_CATEGORY_CHOICES = [
        ('RESIDENTIAL', 'Residential'),
        ('STUDENT_HOUSING', 'Student Housing'),
        ('FAMILY_HOUSING', 'Family Housing'),
        ('EXECUTIVE_HOUSING', 'Executive Housing'),
        ('MIXED_USE', 'Mixed Use'),
    ]
    
    # Admin uploads all properties
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_properties', null=True, blank=True)
    
    # Property Owner / Manager Contact Information (Managed by Admin)
    owner_name = models.CharField(max_length=200, blank=True, help_text="Full Name of Property Manager / Owner")
    owner_email = models.EmailField(blank=True, help_text="Direct Contact Email of Owner")
    owner_phone = models.CharField(max_length=50, blank=True, help_text="Direct Phone / WhatsApp Number of Owner")
    owner_photo = models.ImageField(upload_to='property_managers/', blank=True, null=True, help_text="Profile Photo of Property Manager / Owner")

    # Basic Information
    property_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPE_CHOICES)
    property_category = models.CharField(max_length=30, choices=PROPERTY_CATEGORY_CHOICES, default='RESIDENTIAL')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Location Information
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Ghana')
    postal_code = models.CharField(max_length=20, blank=True)
    digital_address = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Nearest Institution (for student housing)
    nearest_institution = models.CharField(max_length=200, blank=True)
    distance_to_campus = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Distance in km')
    walking_time_estimate = models.PositiveIntegerField(null=True, blank=True, help_text='Walking time in minutes')
    
    # Nearby Landmarks
    nearby_landmarks = models.TextField(blank=True, help_text='Comma-separated landmarks')
    
    # Target Tenant Type
    suitable_for_students = models.BooleanField(default=True)
    suitable_for_workers = models.BooleanField(default=True)
    suitable_for_families = models.BooleanField(default=False)
    suitable_for_couples = models.BooleanField(default=False)
    suitable_for_single_professionals = models.BooleanField(default=False)
    suitable_for_national_service = models.BooleanField(default=False)
    suitable_for_expatriates = models.BooleanField(default=False)
    suitable_for_short_stay = models.BooleanField(default=False)
    
    # Hostel-specific fields
    hostel_type = models.CharField(max_length=20, blank=True, choices=[
        ('BOYS_ONLY', 'Boys Only'),
        ('GIRLS_ONLY', 'Girls Only'),
        ('MIXED', 'Mixed'),
    ])
    ownership_type = models.CharField(max_length=50, blank=True, choices=[
        ('PRIVATE', 'Private Hostel'),
        ('INSTITUTION_AFFILIATED', 'Institution-Affiliated'),
    ])
    
    # Property details
    total_area = models.DecimalField(max_digits=10, decimal_places=2, help_text='Area in square meters')
    floor_number = models.PositiveIntegerField(null=True, blank=True)
    total_floors = models.PositiveIntegerField(null=True, blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    
    # Policies
    house_rules = models.TextField(blank=True)
    prohibited_items = models.TextField(blank=True, help_text='Comma-separated list of prohibited items (e.g. rice cooker, heater, pets, musical instruments)')
    cancellation_policy = models.TextField(blank=True)
    smoking_allowed = models.BooleanField(default=False)
    pets_allowed = models.BooleanField(default=False)
    guests_allowed = models.BooleanField(default=True)
    maximum_guests = models.PositiveIntegerField(default=1)
    
    # Curfew and visitor policy (for hostels)
    curfew_time = models.TimeField(null=True, blank=True)
    visitor_policy = models.TextField(blank=True)
    
    # Verification and status
    is_verified = models.BooleanField(default=False)
    inspection_date = models.DateField(null=True, blank=True)
    safety_score = models.PositiveIntegerField(null=True, blank=True, help_text='Admin-rated safety score 1-10')
    fire_safety_compliance = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PROPERTY_STATUS_CHOICES, default='DRAFT')
    rejection_reason = models.TextField(blank=True)
    
    # Safety Information
    security_personnel = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    gated_community = models.BooleanField(default=False)
    emergency_contacts = models.TextField(blank=True)
    
    # Utilities Information
    water_availability = models.CharField(max_length=50, blank=True)
    electricity_stability = models.CharField(max_length=50, blank=True)
    internet_availability = models.CharField(max_length=50, blank=True)
    utility_billing_method = models.CharField(max_length=50, blank=True, choices=[
        ('INCLUDED_IN_RENT', 'Included in Rent'),
        ('SEPARATE_BILLING', 'Separate Billing'),
    ])
    
    # Metadata
    views_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)
    booking_requests_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Amenities (Many-to-many relationship)
    amenities = models.ManyToManyField(Amenity, through='PropertyAmenity', through_fields=('accommodation_property', 'amenity'), related_name='properties')
    
    class Meta:
        db_table = 'properties'
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.city}"
    
    @property
    def average_rating(self):
        from feedback.models import Review
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0
    @property
    def main_image(self):
        """Returns the primary image, or the first image, or None."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary.image
        first_img = self.images.first()
        if first_img:
            return first_img.image
        return None

    @property
    def all_gallery_images(self):
        """Combines property exterior images and room images into a single gallery list."""
        imgs = list(self.images.all())
        for room in self.rooms.all():
            for r_img in room.images.all():
                imgs.append(r_img)
        return imgs
        
    @property
    def total_reviews(self):
        return self.reviews.count()
        
    @property
    def has_available_rooms(self):
        if not self.is_available:
            return False
        # If physical rooms exist, use slot counts as the ground truth.
        # The status field can be stale; occupied_slots is always up-to-date.
        if self.rooms.exists():
            for room in self.rooms.all():
                # A room is available if it has spare slots regardless of status label
                if room.occupied_slots < room.total_slots:
                    return True
            return False
        # Fallback to room types or unit types
        if self.room_types.exists():
            return self.room_types.filter(available_slots__gt=0).exists()
        if self.unit_types.exists():
            return self.unit_types.filter(available_units__gt=0).exists()
        return self.is_available


class PropertyAmenity(models.Model):
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    is_included = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'property_amenities'
        unique_together = ['accommodation_property', 'amenity']
    
    def __str__(self):
        return f"{self.accommodation_property.title} - {self.amenity.name}"


class PropertyImage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('EXTERIOR', 'Exterior'),
        ('INTERIOR', 'Interior'),
        ('ROOM', 'Room'),
        ('BATHROOM', 'Bathroom'),
        ('KITCHEN', 'Kitchen'),
        ('AMENITY', 'Amenity'),
        ('FLOOR_PLAN', 'Floor Plan'),
        ('OTHER', 'Other'),
    ]
    
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES, default='INTERIOR')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def image_url(self):
        if self.image:
            img_str = str(self.image.name) if hasattr(self.image, 'name') else str(self.image)
            if img_str.startswith('http'):
                return img_str
            # Return the URL directly since the files are tracked in git and guaranteed to exist.
            # Railway sometimes fails storage.exists() due to ephemeral disk quirks.
            return self.image.url
        return ""

    class Meta:
        db_table = 'property_images'
        verbose_name = 'Property Image'
        verbose_name_plural = 'Property Images'
        ordering = ['order', '-uploaded_at']
    
    def __str__(self):
        return f"{self.accommodation_property.title} - {self.image_type}"


class RoomType(models.Model):
    """Room types for hostel properties"""
    OCCUPANCY_TYPE_CHOICES = [
        ('SINGLE', 'Single (1 person)'),
        ('DOUBLE', 'Double (2 in a room)'),
        ('TRIPLE', 'Triple (3 in a room)'),
        ('QUAD', 'Quad (4 in a room)'),
    ]
    
    BED_TYPE_CHOICES = [
        ('SINGLE', 'Single Bed'),
        ('DOUBLE', 'Double Bed'),
        ('BUNK', 'Bunk Bed'),
        ('FUTON', 'Futon'),
    ]
    
    BILLING_MODEL_CHOICES = [
        ('SEMESTER_BASED', 'Semester-Based'),
        ('MONTHLY_BASED', 'Monthly-Based'),
        ('ANNUAL_BASED', 'Annual-Based'),
        ('ACADEMIC_YEAR', 'Academic Year (Combined 2-Semester)'),
    ]
    
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='room_types')
    room_type_name = models.CharField(max_length=100)  # e.g., "Standard Room A"
    
    # Billing Model Assignment (Admin-controlled)
    billing_model = models.CharField(max_length=20, choices=BILLING_MODEL_CHOICES, default='SEMESTER_BASED')
    
    # Room Configuration
    occupancy_type = models.CharField(max_length=20, choices=OCCUPANCY_TYPE_CHOICES, default='SINGLE')
    total_rooms = models.PositiveIntegerField(default=1)
    beds_per_room = models.PositiveIntegerField(default=1)
    
    # Capacity
    total_capacity = models.PositiveIntegerField(default=1)
    available_slots = models.PositiveIntegerField(default=1)
    occupied_slots = models.PositiveIntegerField(default=0)
    waiting_list_enabled = models.BooleanField(default=False)
    
    # Room Features
    bed_type = models.CharField(max_length=20, choices=BED_TYPE_CHOICES, default='SINGLE')
    study_desk_available = models.BooleanField(default=False)
    wardrobe_available = models.BooleanField(default=False)
    air_conditioning = models.BooleanField(default=False)
    fan = models.BooleanField(default=False)
    wifi_available = models.BooleanField(default=False)
    private_bathroom = models.BooleanField(default=False)
    shared_bathroom_ratio = models.CharField(max_length=50, blank=True)
    balcony = models.BooleanField(default=False)
    electricity_backup = models.BooleanField(default=False)
    
    # Gender restriction (for roommate matching)
    gender_restriction = models.CharField(max_length=20, blank=True, choices=[
        ('MALE_ONLY', 'Male Only'),
        ('FEMALE_ONLY', 'Female Only'),
        ('ANY', 'Any Gender'),
    ])
    
    # Lifestyle preferences for roommate matching
    preferred_lifestyle = models.CharField(max_length=50, blank=True, choices=[
        ('QUIET', 'Quiet'),
        ('SOCIAL', 'Social'),
        ('ACADEMIC_FOCUSED', 'Academic-focused'),
        ('BALANCED', 'Balanced'),
    ])
    study_environment_rating = models.PositiveIntegerField(null=True, blank=True, help_text='Study environment rating 1-5')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'room_types'
        verbose_name = 'Room Type'
        verbose_name_plural = 'Room Types'
        ordering = ['room_type_name']
    
    def __str__(self):
        return f"{self.accommodation_property.title} - {self.room_type_name}"

    @property
    def available_rooms_count(self):
        """Calculates available rooms count based on beds per room and available slots."""
        if self.beds_per_room <= 1:
            return self.available_slots
        if self.available_slots <= 0:
            return 0
        import math
        return math.ceil(self.available_slots / self.beds_per_room)

    @property
    def available_display_text(self):
        """Returns clear room availability string preventing single-room slot multiplication confusion."""
        if self.available_slots <= 0:
            return "Fully Booked"
        if self.beds_per_room == 1:
            return f"{self.available_slots} room(s) left"
        else:
            rms = self.available_rooms_count
            return f"{rms} room(s) left ({self.available_slots} beds total)"

    def recalculate_capacity(self):
        """
        Dynamically recalculates available_slots based on actual Booking records.
        """
        from bookings.models import Booking
        # Count active physical bookings (any status that holds a slot, past INITIATED)
        active_bookings_count = Booking.objects.filter(
            room_type=self,
            status__in=[
                'ACTIVE', 'COMPLETED', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 
                'ASSIGNED_AWAITING', 'UNDER_REVIEW', 'LIFESTYLE_PENDING', 
                'LIFESTYLE_COMPLETE', 'AWAITING_COMPATIBILITY', 'AUTO_ASSIGNED', 
                'CONSENT_PENDING', 'CONSENT_ACCEPTED', 'ADMIN_PENDING', 
                'PAYMENT_REQUIRED', 'PAYMENT_PROCESSING', 'PAYMENT_PENDING_VERIFICATION', 
                'PAYMENT_COMPLETE', 'VACATION_RESERVE', 'GRACE_PERIOD', 
                'WAITING_CONSENT', 'COMPATIBILITY_REVIEW', 'REINSTATED'
            ]
        ).count()
        
        # Count soft-locked slots
        soft_locked_slots = 0
        initiated_bookings = Booking.objects.filter(
            room_type=self,
            status__in=['INITIATED', 'TEMPORARILY_CANCELLED']
        )
        for b in initiated_bookings:
            if b.status == 'TEMPORARILY_CANCELLED':
                exp = b.temp_cancel_expires_at or b.slot_hold_expires_at or b.consent_deadline
                if exp and exp > timezone.now():
                    soft_locked_slots += 1
            elif b.is_soft_lock_active():
                soft_locked_slots += 1
                
        total_consumed = active_bookings_count + soft_locked_slots
        self.available_slots = max(0, self.total_capacity - total_consumed)
        self.save(update_fields=['available_slots'])


class RoomTypePricing(models.Model):
    """Multiple pricing models for room types"""
    PAYMENT_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('SEMESTER', 'Semester-based'),
        ('YEARLY', 'Yearly'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
    ]
    
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='pricing_models')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    semester_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weekly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Billing Model Specific Pricing
    academic_year_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Combined 2-semester price with discount')
    two_years_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='2-year advance payment price')
    
    # Billing Model Configuration (Admin-controlled)
    max_semesters = models.PositiveIntegerField(default=3, help_text='Maximum semesters bookable at once (1-3)')
    min_months = models.PositiveIntegerField(default=1, help_text='Minimum months for monthly booking')
    max_months = models.PositiveIntegerField(default=12, help_text='Maximum months bookable at once')
    allow_two_year_advance = models.BooleanField(default=False, help_text='Allow 2-year advance payment for Annual-Based')
    early_checkout_allowed = models.BooleanField(default=True, help_text='Allow early checkout for Annual-Based')
    early_checkout_penalty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Penalty amount for early checkout')
    
    # Grace Period and Overstay Configuration (Part 8, 9)
    grace_period_days = models.PositiveIntegerField(default=7, help_text='Grace period duration in days (3-14)')
    overstay_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.5, help_text='Overstay rate multiplier (1.0-2.0)')
    allow_monthly_extensions = models.BooleanField(default=False, help_text='Allow monthly extensions for this room type')
    monthly_extension_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Monthly rate for extensions')
    
    # Additional Fees
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    utility_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Currency
    currency = models.CharField(max_length=3, default='GHS')
    
    class Meta:
        db_table = 'room_type_pricing'
        verbose_name = 'Room Type Pricing'
        verbose_name_plural = 'Room Type Pricing'
        unique_together = ['room_type', 'payment_type']
    
    def __str__(self):
        return f"{self.room_type.room_type_name} - {self.payment_type}"


class UnitType(models.Model):
    """Unit types for apartment properties"""
    BILLING_MODEL_CHOICES = [
        ('SEMESTER_BASED', 'Semester-Based'),
        ('MONTHLY_BASED', 'Monthly-Based'),
        ('ANNUAL_BASED', 'Annual-Based'),
        ('ACADEMIC_YEAR', 'Academic Year (Combined 2-Semester)'),
    ]
    
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='unit_types')
    unit_name = models.CharField(max_length=100)  # e.g., "Studio Unit", "One Bedroom Unit"
    
    # Billing Model Assignment (Admin-controlled)
    billing_model = models.CharField(max_length=20, choices=BILLING_MODEL_CHOICES, default='MONTHLY_BASED')
    
    # Unit Configuration
    number_of_units = models.PositiveIntegerField(default=1)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    kitchen = models.PositiveIntegerField(default=1)
    balcony = models.BooleanField(default=False)
    
    # Capacity
    total_units = models.PositiveIntegerField(default=1)
    occupied_units = models.PositiveIntegerField(default=0)
    available_units = models.PositiveIntegerField(default=1)
    
    # Features
    furnished_status = models.CharField(max_length=20, choices=[
        ('FURNISHED', 'Furnished'),
        ('SEMI_FURNISHED', 'Semi-Furnished'),
        ('UNFURNISHED', 'Unfurnished'),
    ], default='UNFURNISHED')
    
    air_conditioning = models.BooleanField(default=False)
    fan = models.BooleanField(default=False)
    water_heater = models.BooleanField(default=False)
    refrigerator = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)
    television = models.BooleanField(default=False)
    generator = models.BooleanField(default=False)
    internet = models.BooleanField(default=False)
    
    # Shared apartment option
    shared_apartment_allowed = models.BooleanField(default=False)
    roommate_matching_enabled = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'unit_types'
        verbose_name = 'Unit Type'
        verbose_name_plural = 'Unit Types'
        ordering = ['unit_name']
    
    def __str__(self):
        return f"{self.accommodation_property.title} - {self.unit_name}"

    @property
    def name(self):
        return self.unit_name

    @property
    def unit_type_name(self):
        return self.unit_name

    def recalculate_capacity(self):
        """
        Dynamically recalculates available_units based on actual Booking records.
        """
        from bookings.models import Booking
        # Count active physical bookings (any status that holds a slot, past INITIATED)
        active_bookings_count = Booking.objects.filter(
            unit_type=self,
            status__in=[
                'ACTIVE', 'COMPLETED', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 
                'ASSIGNED_AWAITING', 'UNDER_REVIEW', 'LIFESTYLE_PENDING', 
                'LIFESTYLE_COMPLETE', 'AWAITING_COMPATIBILITY', 'AUTO_ASSIGNED', 
                'CONSENT_PENDING', 'CONSENT_ACCEPTED', 'ADMIN_PENDING', 
                'PAYMENT_REQUIRED', 'PAYMENT_PROCESSING', 'PAYMENT_PENDING_VERIFICATION', 
                'PAYMENT_COMPLETE', 'VACATION_RESERVE', 'GRACE_PERIOD', 
                'WAITING_CONSENT', 'COMPATIBILITY_REVIEW', 'REINSTATED'
            ]
        ).count()
        
        # Count soft-locked slots
        soft_locked_slots = 0
        initiated_bookings = Booking.objects.filter(
            unit_type=self,
            status='INITIATED'
        )
        for b in initiated_bookings:
            if b.is_soft_lock_active():
                soft_locked_slots += 1
                
        total_consumed = active_bookings_count + soft_locked_slots
        self.available_units = max(0, self.total_units - total_consumed)
        self.save(update_fields=['available_units'])


class UnitTypePricing(models.Model):
    """Multiple pricing models for unit types"""
    PAYMENT_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('SEMESTER', 'Semester'),
        ('YEARLY', 'Yearly'),
        ('TWO_YEARS', 'Two Years'),
        ('THREE_YEARS', 'Three Years'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
    ]
    
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE, related_name='pricing_models')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    semester_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    two_years_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    three_years_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weekly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Billing Model Specific Pricing
    academic_year_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Combined 2-semester price with discount')
    
    # Billing Model Configuration (Admin-controlled)
    max_semesters = models.PositiveIntegerField(default=3, help_text='Maximum semesters bookable at once (1-3)')
    min_months = models.PositiveIntegerField(default=1, help_text='Minimum months for monthly booking')
    max_months = models.PositiveIntegerField(default=12, help_text='Maximum months bookable at once')
    allow_two_year_advance = models.BooleanField(default=False, help_text='Allow 2-year advance payment for Annual-Based')
    early_checkout_allowed = models.BooleanField(default=True, help_text='Allow early checkout for Annual-Based')
    early_checkout_penalty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Penalty amount for early checkout')
    
    # Grace Period and Overstay Configuration (Part 8, 9)
    grace_period_days = models.PositiveIntegerField(default=7, help_text='Grace period duration in days (3-14)')
    overstay_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.5, help_text='Overstay rate multiplier (1.0-2.0)')
    allow_monthly_extensions = models.BooleanField(default=False, help_text='Allow monthly extensions for this room type')
    monthly_extension_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Monthly rate for extensions')
    
    # Additional Fees
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    utility_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Currency
    currency = models.CharField(max_length=3, default='GHS')
    
    class Meta:
        db_table = 'unit_type_pricing'
        verbose_name = 'Unit Type Pricing'
        verbose_name_plural = 'Unit Type Pricing'
        unique_together = ['unit_type', 'payment_type']
    
    def __str__(self):
        return f"{self.unit_type.unit_name} - {self.payment_type}"


class RentalDuration(models.Model):
    """Rental duration models for properties"""
    DURATION_TYPE_CHOICES = [
        ('SHORT_STAY', 'Short Stay'),
        ('LONG_TERM_LEASE', 'Long-Term Lease'),
        ('FLEXIBLE_LEASE', 'Flexible Lease'),
    ]
    
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rental_durations')
    duration_type = models.CharField(max_length=20, choices=DURATION_TYPE_CHOICES)
    
    # Short Stay Options
    daily_available = models.BooleanField(default=False)
    weekend_available = models.BooleanField(default=False)
    weekly_available = models.BooleanField(default=False)
    monthly_available = models.BooleanField(default=False)
    
    # Long-Term Lease Options
    six_months_available = models.BooleanField(default=False)
    semester_available = models.BooleanField(default=False)
    one_year_available = models.BooleanField(default=False)
    two_years_available = models.BooleanField(default=False)
    three_years_available = models.BooleanField(default=False)
    custom_lease_available = models.BooleanField(default=False)
    
    # Flexible Lease Options
    minimum_stay_months = models.PositiveIntegerField(null=True, blank=True)
    maximum_stay_months = models.PositiveIntegerField(null=True, blank=True)
    
    # Advance Payment Requirements
    required_advance = models.CharField(max_length=20, choices=[
        ('MONTHLY', 'Monthly'),
        ('SIX_MONTHS', '6 Months'),
        ('ONE_YEAR', '1 Year'),
        ('TWO_YEARS', '2 Years'),
        ('THREE_YEARS', '3 Years'),
    ], blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rental_durations'
        verbose_name = 'Rental Duration'
        verbose_name_plural = 'Rental Durations'
        unique_together = ['accommodation_property', 'duration_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.accommodation_property.title} - {self.duration_type}"


class PropertyVideo(models.Model):
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='videos')
    video_file = models.FileField(upload_to='property_videos/', blank=True, null=True)
    video_url = models.URLField(blank=True)  # For YouTube, Vimeo, etc.
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_virtual_tour = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_videos'
        verbose_name = 'Property Video'
        verbose_name_plural = 'Property Videos'
    
    def __str__(self):
        return f"{self.accommodation_property.title} - Video"


class PropertyViewing(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='viewings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_viewings')
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_viewings'
        verbose_name = 'Property Viewing'
        verbose_name_plural = 'Property Viewings'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.accommodation_property.title} - {self.user.email} - {self.scheduled_date}"


class SavedProperty(models.Model):
    """User saved properties - Phase 4: Property Management (Saving and Organization)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by')
    notes = models.TextField(blank=True, help_text='Personal notes about this property')
    comparison_group = models.CharField(max_length=50, blank=True, help_text='Group name for comparison')
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'saved_properties'
        verbose_name = 'Saved Property'
        verbose_name_plural = 'Saved Properties'
        unique_together = ['user', 'property']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.property.title}"

class Room(models.Model):
    STATUS_CHOICES = [
        # Core availability states (spec Part 7.1)
        ('AVAILABLE', 'Available'),
        ('PARTIALLY_OCCUPIED', 'Partially Occupied'),   # legacy alias for OCCUPIED (SINGLE)
        ('OCCUPIED', 'Occupied (Single — slots remain)'),
        ('FULLY_OCCUPIED', 'Fully Occupied'),
        # Duration-based states
        ('VACATION_RESERVE', 'Vacation Reserve — Held for Student'),
        ('PRACTICAL_CHECKOUT', 'Practical Checkout (48h, Split Stay)'),
        ('GRACE_PERIOD', 'Grace Period'),
        ('OVERSTAY', 'Overstay — Student Not Vacated'),
        # Admin-set states
        ('MAINTENANCE', 'Maintenance — Temporarily Unavailable'),
        ('ARCHIVED', 'Archived — Removed from Listings'),
        # Legacy status kept for backward compatibility
        ('RESERVED', 'Reserved'),
    ]
    accommodation_property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey('RoomType', on_delete=models.CASCADE, null=True, blank=True, related_name='rooms')
    unit_type = models.ForeignKey('UnitType', on_delete=models.CASCADE, null=True, blank=True, related_name='units')
    room_number = models.CharField(max_length=20)
    floor = models.CharField(max_length=10, blank=True)
    total_slots = models.PositiveIntegerField(default=1)
    occupied_slots = models.PositiveIntegerField(default=0)
    pending_slots = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        unique_together = ['accommodation_property', 'room_number']

    def __str__(self):
        return f"{self.accommodation_property.title} - Room {self.room_number}"

    @property
    def available_slots(self):
        return max(0, self.total_slots - self.occupied_slots - self.pending_slots)

    def recalculate_occupancy(self):
        """
        Dynamically recalculates occupied_slots and pending_slots based on actual Booking records.
        """
        from bookings.models import Booking
        from django.db.models import Q
        
        room_filter = Q(assigned_room=self) | Q(room=self)
        
        # Count active physical bookings
        self.occupied_slots = Booking.objects.filter(
            room_filter,
            status__in=['ACTIVE', 'COMPLETED', 'CONFIRMED', 'CONFIRMED_ASSIGNED']
        ).count()
        
        # Count pending physical bookings
        self.pending_slots = Booking.objects.filter(
            room_filter,
            status__in=[
                'ASSIGNED_AWAITING', 'UNDER_REVIEW', 'LIFESTYLE_PENDING', 
                'LIFESTYLE_COMPLETE', 'AWAITING_COMPATIBILITY', 'AUTO_ASSIGNED', 
                'CONSENT_PENDING', 'CONSENT_ACCEPTED', 'ADMIN_PENDING', 
                'PAYMENT_REQUIRED', 'PAYMENT_PROCESSING', 'PAYMENT_PENDING_VERIFICATION', 
                'PAYMENT_COMPLETE', 'VACATION_RESERVE', 'GRACE_PERIOD', 
                'WAITING_CONSENT', 'COMPATIBILITY_REVIEW', 'REINSTATED'
            ]
        ).count()
        
        # Count soft-locked slots
        soft_locked_slots = 0
        initiated_bookings = Booking.objects.filter(
            room_filter,
            status__in=['INITIATED', 'TEMPORARILY_CANCELLED']
        )
        for b in initiated_bookings:
            if b.status == 'TEMPORARILY_CANCELLED':
                exp = b.temp_cancel_expires_at or b.slot_hold_expires_at or b.consent_deadline
                if exp and exp > timezone.now():
                    soft_locked_slots += 1
            elif b.is_soft_lock_active():
                soft_locked_slots += 1
                
        self.pending_slots += soft_locked_slots
        
        # Cap to total_slots just in case
        self.occupied_slots = min(self.occupied_slots, self.total_slots)
        self.pending_slots = min(self.pending_slots, self.total_slots - self.occupied_slots)
        
        self.save(update_fields=['occupied_slots', 'pending_slots'])


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='room_images/')
    image_type = models.CharField(max_length=20, choices=[
        ('BEDROOM', 'Bedroom/Interior'),
        ('WASHROOM', 'Washroom'),
        ('KITCHEN', 'Kitchen'),
        ('OTHER', 'Other')
    ], default='BEDROOM')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.room_number} - {self.get_image_type_display()}"

    @property
    def image_url(self):
        if self.image:
            img_str = str(self.image.name) if hasattr(self.image, 'name') else str(self.image)
            if img_str.startswith('http'):
                return img_str
            return self.image.url
        return ""


class ProximityDestination(models.Model):
    """Structured proximity information for properties"""
    TRAVEL_MODE_CHOICES = [
        ('WALK', 'Walk'),
        ('DRIVE', 'Drive'),
        ('TROTRO', 'Trotro'),
        ('BUS', 'Bus'),
        ('TAXI', 'Taxi'),
    ]
    
    accommodation_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='proximity_destinations')
    destination_name = models.CharField(max_length=200)
    destination_type = models.CharField(max_length=50, choices=[
        ('INSTITUTION', 'Institution'),
        ('MARKET', 'Market'),
        ('PHARMACY', 'Pharmacy'),
        ('TRANSPORT', 'Transport Hub'),
        ('ATM', 'ATM/Bank'),
        ('HOSPITAL', 'Hospital'),
        ('RESTAURANT', 'Restaurant'),
        ('SHOPPING', 'Shopping Mall'),
        ('OTHER', 'Other'),
    ])
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Distance in kilometers')
    travel_time_minutes = models.PositiveIntegerField(null=True, blank=True, help_text='Travel time in minutes')
    travel_mode = models.CharField(max_length=20, choices=TRAVEL_MODE_CHOICES, default='WALK')
    notes = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'proximity_destinations'
        verbose_name = 'Proximity Destination'
        verbose_name_plural = 'Proximity Destinations'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.destination_name} - {self.distance_km} km"

