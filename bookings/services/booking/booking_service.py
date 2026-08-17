"""
BookingService - Core booking operations.
Handles booking creation, initialization, and core business logic.
"""

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
import uuid

from bookings.models import Booking, BookingStatusTimeline
from bookings.exceptions import (
    DuplicateBookingError,
    EmailVerificationRequiredError,
    SlotUnavailableError,
    ValidationError
)


class BookingService:
    """Service for core booking operations."""
    
    def __init__(self):
        pass
    
    @transaction.atomic
    def create_initial_booking(self, tenant, property_obj, room_type=None, unit_type=None):
        """
        Create an initial booking with soft-lock.
        
        Args:
            tenant: User object
            property_obj: Property object
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            
        Returns:
            Booking object with INITIATED status
            
        Raises:
            EmailVerificationRequiredError: If user email is not verified
            DuplicateBookingError: If user has an active booking
            SlotUnavailableError: If no slots available
            ValidationError: If validation fails
        """
        # Validate email verification
        if not tenant.email_verified:
            raise EmailVerificationRequiredError()
        
        # Validate room/unit selection
        if not room_type and not unit_type:
            raise ValidationError("Either room_type or unit_type must be provided")
        
        # Check for existing active bookings
        if self._has_active_booking(tenant):
            raise DuplicateBookingError()
        
        # Check availability
        if room_type and room_type.available_slots <= 0:
            raise SlotUnavailableError("No available slots for this room type")
        
        if unit_type and unit_type.available_units <= 0:
            raise SlotUnavailableError("No available units for this unit type")
        
        # Determine booking type
        booking_type = 'PRIVATE'
        if room_type and room_type.occupancy_type in ['DOUBLE', 'TRIPLE', 'QUAD']:
            booking_type = 'ROOMMATE_MATCH'
        
        # Create booking
        booking = Booking.objects.create(
            tenant=tenant,
            accommodation_property=property_obj,
            room_type=room_type,
            unit_type=unit_type,
            booking_type=booking_type,
            status='INITIATED',
            move_in_date=timezone.now().date(),  # Placeholder, updated later
            monthly_rent=0,  # Placeholder, updated later
            total_amount=0  # Placeholder, updated later
        )
        
        # Set soft-lock
        booking.set_soft_lock(hours=2)
        
        # Reserve slot
        if not booking.reserve_slot():
            booking.delete()
            raise SlotUnavailableError("Failed to reserve slot")
        
        # Create timeline entry
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='',
            new_status='INITIATED',
            reason='Booking initiated and soft-locked',
            triggered_by=tenant
        )
        
        return booking
    
    def _has_active_booking(self, tenant):
        """Check if user has an active booking."""
        active_statuses = [
            'INITIATED', 'UNDER_REVIEW', 'ASSIGNED_AWAITING',
            'CONFIRMED_ASSIGNED', 'ACTIVE', 'WAITLISTED'
        ]
        return Booking.objects.filter(
            tenant=tenant,
            status__in=active_statuses
        ).exists()
    
    def get_booking_by_id(self, booking_id, tenant=None):
        """
        Get booking by ID.
        
        Args:
            booking_id: Booking ID
            tenant: Optional tenant to verify ownership
            
        Returns:
            Booking object
            
        Raises:
            Booking.DoesNotExist: If booking not found
        """
        if tenant:
            return Booking.objects.get(id=booking_id, tenant=tenant)
        return Booking.objects.get(id=booking_id)
    
    def get_booking_by_reference(self, reference_number):
        """
        Get booking by reference number.
        
        Args:
            reference_number: Booking reference number
            
        Returns:
            Booking object
            
        Raises:
            Booking.DoesNotExist: If booking not found
        """
        return Booking.objects.get(reference_number=reference_number)
    
    def cancel_booking(self, booking, reason="Cancelled by user", triggered_by=None):
        """
        Cancel a booking.
        
        Args:
            booking: Booking object
            reason: Cancellation reason
            triggered_by: User who triggered cancellation
            
        Returns:
            Updated booking object
        """
        from bookings.services.booking.slot_reservation_service import SlotReservationService
        
        with transaction.atomic():
            previous_status = booking.status
            
            # Update status
            booking.status = 'TEMPORARILY_CANCELLED'
            booking.save()
            
            # Release slot
            slot_service = SlotReservationService()
            slot_service.release_slot(booking)
            
            # Create timeline entry
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status=previous_status,
                new_status='TEMPORARILY_CANCELLED',
                reason=reason,
                triggered_by=triggered_by
            )
        
        return booking
    
    def reinstate_booking(self, booking, triggered_by=None):
        """
        Reinstate a temporarily cancelled booking.
        
        Args:
            booking: Booking object
            triggered_by: User who triggered reinstatement
            
        Returns:
            Updated booking object
        """
        from bookings.services.booking.slot_reservation_service import SlotReservationService
        
        with transaction.atomic():
            previous_status = booking.status
            
            # Check if still within soft-lock period
            if booking.soft_lock_expires_at and booking.soft_lock_expires_at < timezone.now():
                raise ValidationError("Cannot reinstate booking - soft-lock has expired")
            
            # Re-reserve slot
            slot_service = SlotReservationService()
            if not slot_service.reserve_slot(booking):
                raise SlotUnavailableError("Slot no longer available")
            
            # Update status
            booking.status = 'INITIATED'
            booking.save()
            
            # Create timeline entry
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status=previous_status,
                new_status='INITIATED',
                reason='Booking reinstated',
                triggered_by=triggered_by
            )
        
        return booking
    
    def permanently_cancel_booking(self, booking, reason="Permanently cancelled", triggered_by=None):
        """
        Permanently cancel a booking.
        
        Args:
            booking: Booking object
            reason: Cancellation reason
            triggered_by: User who triggered cancellation
            
        Returns:
            Updated booking object
        """
        from bookings.services.booking.slot_reservation_service import SlotReservationService
        
        with transaction.atomic():
            previous_status = booking.status
            
            # Update status
            booking.status = 'PERMANENTLY_CANCELLED'
            booking.save()
            
            # Release slot
            slot_service = SlotReservationService()
            slot_service.release_slot(booking)
            
            # Create timeline entry
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status=previous_status,
                new_status='PERMANENTLY_CANCELLED',
                reason=reason,
                triggered_by=triggered_by
            )
        
        return booking
    
    def check_soft_lock_validity(self, booking):
        """
        Check if booking soft-lock is still valid.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            SoftLockExpiredError: If soft-lock has expired
        """
        if booking.soft_lock_expires_at and booking.soft_lock_expires_at < timezone.now():
            from bookings.exceptions import SoftLockExpiredError
            raise SoftLockExpiredError()
        return True
    
    def requires_roommate_matching(self, booking):
        """
        Check if booking requires roommate matching.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if roommate matching required
        """
        if booking.booking_type == 'ROOMMATE_MATCH':
            return True
        if booking.room_type and booking.room_type.occupancy_type in ['DOUBLE', 'TRIPLE', 'QUAD']:
            return True
        return False
