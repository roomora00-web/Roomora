"""
Atomic Soft Lock Service

Implements the atomic soft lock mechanism for booking initiation according to the new booking flow specification.

The soft lock:
- Reserves exactly one slot for the user for 2 hours
- Makes that slot appear unavailable to all other browsing users
- Prevents any other user from booking the same slot
- Does not confirm the booking or assign a room number

All operations are atomic using SELECT FOR UPDATE to prevent race conditions.
"""

from typing import Optional, Dict, Tuple
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking
from properties.models import Room, RoomType, UnitType


class SoftLockResult:
    """Result of a soft lock operation"""
    
    def __init__(self, success: bool, booking: Optional[Booking] = None, message: str = ""):
        self.success = success
        self.booking = booking
        self.message = message
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'booking_id': self.booking.id if self.booking else None,
            'reference_number': self.booking.reference_number if self.booking else None,
            'message': self.message
        }


class SoftLockService:
    """Service for atomic soft lock operations"""
    
    @staticmethod
    def check_slot_availability(room_id: Optional[int], unit_type_id: Optional[int]) -> Tuple[bool, str]:
        """
        Check real-time slot availability using SELECT FOR UPDATE.
        Returns tuple of (available, message)
        """
        with transaction.atomic():
            if room_id:
                # Lock the room type row
                room = Room.objects.select_for_update().filter(id=room_id).first()
                if not room:
                    return False, "Room type not found"
                
                if room.available_slots <= 0:
                    return False, "This room type is currently unavailable. Rooms at popular properties fill up quickly."
                
                return True, f"{room.available_slots} slots available"
            
            elif unit_type_id:
                # Lock the unit type row
                unit_type = UnitType.objects.select_for_update().filter(id=unit_type_id).first()
                if not unit_type:
                    return False, "Unit type not found"
                
                if unit_type.available_units <= 0:
                    return False, "This unit type is currently unavailable. Units at popular properties fill up quickly."
                
                return True, f"{unit_type.available_units} units available"
            
            else:
                return False, "Either room_type_id or unit_type_id must be provided"
    
    @staticmethod
    def calculate_occupancy_position(room_id: Optional[int], unit_type_id: Optional[int]) -> Tuple[int, bool]:
        """
        Calculate the occupancy position (1=first occupant, 2=second, etc.)
        Returns tuple of (position, is_first_occupant)
        """
        if room_id:
            # Count existing bookings for this room type
            existing_count = Booking.objects.filter(
                room_id=room_id,
                status__in=['INITIATED', 'UNDER_REVIEW', 'ASSIGNED_AWAITING', 'CONFIRMED_ASSIGNED', 'ACTIVE']
            ).count()
            
            position = existing_count + 1
            is_first = position == 1
            return position, is_first
        
        elif unit_type_id:
            # Count existing bookings for this unit type
            existing_count = Booking.objects.filter(
                unit_type_id=unit_type_id,
                status__in=['INITIATED', 'UNDER_REVIEW', 'ASSIGNED_AWAITING', 'CONFIRMED_ASSIGNED', 'ACTIVE']
            ).count()
            
            position = existing_count + 1
            is_first = position == 1
            return position, is_first
        
        return 1, True
    
    @staticmethod
    def execute_atomic_soft_lock(
        user,
        property_id: int,
        room_id: Optional[int],
        unit_type_id: Optional[int],
        house_rules_acknowledged_at: Optional[timezone.datetime] = None
    ) -> SoftLockResult:
        """
        Execute atomic soft lock in a single database transaction.
        
        This performs the following atomically:
        1. Room record: pending_slots incremented by 1
        2. Room record: available_slots decremented by 1
        3. Booking record: created with status INITIATED
        4. Booking reference: generated (format SM-YYYYMMDD-XXXX)
        5. Soft lock expiry: set to exactly 6 hours from this moment
        6. Occupancy position: calculated (1 if first occupant, 2 if second, etc.)
        7. Is first occupant flag: set to True or False
        """
        from properties.models import Property
        
        with transaction.atomic():
            # Step 0: Check for existing unexpired INITIATED booking
            existing_booking = Booking.objects.filter(
                tenant=user,
                accommodation_property_id=property_id,
                room_id=room_id,
                unit_type_id=unit_type_id,
                status='INITIATED',
                soft_lock_expires_at__gt=timezone.now()
            ).first()
            
            if existing_booking:
                if house_rules_acknowledged_at:
                    existing_booking.house_rules_acknowledged = True
                    existing_booking.house_rules_acknowledged_at = house_rules_acknowledged_at
                    existing_booking.save(update_fields=['house_rules_acknowledged', 'house_rules_acknowledged_at'])
                return SoftLockResult(success=True, booking=existing_booking, message="Resumed existing booking")

            # Step 1: Check availability with row lock
            available, message = SoftLockService.check_slot_availability(room_id, unit_type_id)
            if not available:
                return SoftLockResult(success=False, message=message)
            
            # Step 2: Get property
            property_obj = Property.objects.select_for_update().filter(id=property_id).first()
            if not property_obj:
                return SoftLockResult(success=False, message="Property not found")
            
            # Step 3: Calculate occupancy position
            occupancy_position, is_first_occupant = SoftLockService.calculate_occupancy_position(
                room_id, unit_type_id
            )
            
            # Step 4: Create booking with INITIATED status
            # Resolve room_type from the room if room_id is provided
            room_type_id_resolved = None
            if room_id:
                try:
                    from properties.models import Room as RoomModel
                    room_obj = RoomModel.objects.get(id=room_id)
                    room_type_id_resolved = room_obj.room_type_id
                except Exception:
                    pass

            booking = Booking.objects.create(
                tenant=user,
                accommodation_property=property_obj,
                room_id=room_id,
                room_type_id=room_type_id_resolved,  # Critical: enables post_save signal to call recalculate_capacity()
                unit_type_id=unit_type_id,
                status='INITIATED',
                house_rules_acknowledged=True,
                house_rules_acknowledged_at=house_rules_acknowledged_at or timezone.now(),
                soft_lock_expires_at=timezone.now() + timedelta(hours=2),
                occupancy_position=occupancy_position,
                is_first_occupant=is_first_occupant,
                move_in_date=timezone.now().date(),  # Placeholder, will be set in next step
                monthly_rent=0,  # Placeholder, will be calculated in next step
                total_amount=0  # Placeholder, will be calculated in next step
            )
            
            # Step 5: Slots are now updated automatically via Django post_save signals
            # when the booking is created (room_type.recalculate_capacity() is called).
            
            # Step 6: Create timeline entry
            from bookings.models import BookingStatusTimeline
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status='',
                new_status='INITIATED',
                triggered_by=user,
                triggered_by_type='USER',
                reason='Soft lock initiated - slot reserved for 2 hours'
            )
            
            return SoftLockResult(
                success=True,
                booking=booking,
                message=f"Slot reserved successfully. Reference: {booking.reference_number}"
            )

    
    @staticmethod
    def release_soft_lock(booking: Booking) -> bool:
        """
        Release a soft lock when booking expires or is cancelled.
        This is the reverse of the atomic soft lock operation.
        """
        with transaction.atomic():
            # Check if soft lock is still active
            if not booking.is_soft_lock_active():
                return False
            
            # Release slot: Slots are now updated automatically via Django post_save signals
            # when the booking status is changed to EXPIRED below.
            
            # Update booking status
            booking.status = 'EXPIRED'
            booking.soft_lock_expires_at = None
            
            # Create timeline entry
            from bookings.models import BookingStatusTimeline
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status='INITIATED',
                new_status='EXPIRED',
                triggered_by=None,
                triggered_by_type='SYSTEM',
                reason='Soft lock expired - slot released'
            )
            
            booking.save()
            return True
    
    @staticmethod
    def get_time_remaining(booking: Booking) -> Optional[timedelta]:
        """
        Get the time remaining until soft lock expiry.
        Returns None if no soft lock is active.
        """
        if not booking.soft_lock_expires_at:
            return None
        
        if booking.is_soft_lock_expired():
            return timedelta(0)
        
        return booking.soft_lock_expires_at - timezone.now()
