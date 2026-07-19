"""
BookingValidationService - Validation rules for bookings.
Handles all booking validation logic.
"""

from bookings.exceptions import ValidationError, EmailVerificationRequiredError


class BookingValidationService:
    """Service for booking validation."""
    
    def __init__(self):
        pass
    
    def validate_booking_request(self, tenant, property_obj, room_type=None, unit_type=None):
        """
        Validate a booking request.
        
        Args:
            tenant: User object
            property_obj: Property object
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            
        Raises:
            ValidationError: If validation fails
            EmailVerificationRequiredError: If email not verified
        """
        # Validate email verification
        if not tenant.email_verified:
            raise EmailVerificationRequiredError()
        
        # Validate room/unit selection
        if not room_type and not unit_type:
            raise ValidationError("Either room_type or unit_type must be provided")
        
        # Validate property status
        if property_obj.status != 'APPROVED':
            raise ValidationError("Property is not available for booking")
        
        if not property_obj.is_available:
            raise ValidationError("Property is currently unavailable")
        
        # Validate room/unit belongs to property
        if room_type and room_type.accommodation_property != property_obj:
            raise ValidationError("Room type does not belong to this property")
        
        if unit_type and unit_type.accommodation_property != property_obj:
            raise ValidationError("Unit type does not belong to this property")
            
        # Validate gender restrictions
        user_gender = tenant.gender
        
        # 1. Check Property Level Restriction (Hostels only)
        if property_obj.property_type == 'HOSTEL' and property_obj.hostel_type:
            if property_obj.hostel_type == 'BOYS_ONLY' and user_gender != 'MALE':
                raise ValidationError("This hostel is for males only. You cannot book a room here.")
            elif property_obj.hostel_type == 'GIRLS_ONLY' and user_gender != 'FEMALE':
                raise ValidationError("This hostel is for females only. You cannot book a room here.")
                
        # 2. Check Room Level Restriction (Hostels or Shared Apartments)
        if room_type and room_type.gender_restriction:
            if room_type.gender_restriction == 'MALE_ONLY' and user_gender != 'MALE':
                raise ValidationError("This specific room is reserved for males only.")
            elif room_type.gender_restriction == 'FEMALE_ONLY' and user_gender != 'FEMALE':
                raise ValidationError("This specific room is reserved for females only.")
    
    def validate_agreement_checkboxes(self, understand_pricing, complete_profile, accept_match, acknowledge_rules):
        """
        Validate that all agreement checkboxes are accepted.
        
        Args:
            understand_pricing: Boolean
            complete_profile: Boolean
            accept_match: Boolean
            acknowledge_rules: Boolean
            
        Raises:
            ValidationError: If any checkbox not accepted
        """
        if not all([understand_pricing, complete_profile, accept_match, acknowledge_rules]):
            raise ValidationError("Please accept all agreements to proceed with booking")
    
    def validate_dates(self, move_in_date, move_out_date):
        """
        Validate move-in and move-out dates.
        
        Args:
            move_in_date: Date object
            move_out_date: Date object
            
        Raises:
            ValidationError: If dates are invalid
        """
        if move_out_date and move_out_date <= move_in_date:
            raise ValidationError("Move-out date must be after move-in date")
    
    def validate_booking_modification(self, booking, new_status=None):
        """
        Validate that booking can be modified.
        
        Args:
            booking: Booking object
            new_status: Optional new status to validate
            
        Raises:
            ValidationError: If booking cannot be modified
        """
        # Check if booking is in terminal state
        terminal_states = ['COMPLETED', 'PERMANENTLY_CANCELLED', 'REJECTED']
        if booking.status in terminal_states:
            raise ValidationError(f"Cannot modify booking in {booking.status} state")
        
        # Check if soft-lock has expired
        if booking.soft_lock_expires_at and booking.soft_lock_expires_at < timezone.now():
            raise ValidationError("Booking soft-lock has expired")
    
    def validate_user_ownership(self, booking, user):
        """
        Validate that user owns the booking.
        
        Args:
            booking: Booking object
            user: User object
            
        Raises:
            ValidationError: If user does not own booking
        """
        if booking.tenant != user:
            raise ValidationError("You do not have permission to modify this booking")
