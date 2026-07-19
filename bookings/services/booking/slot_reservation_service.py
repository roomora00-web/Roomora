"""
SlotReservationService - Slot management operations.
Handles slot reservation, release, and availability tracking.
"""

from django.db import transaction
from django.db.models import F

from bookings.exceptions import SlotUnavailableError


class SlotReservationService:
    """Service for slot reservation and management."""
    
    def __init__(self):
        pass
    
    @transaction.atomic
    def reserve_slot(self, booking):
        """
        Reserve a slot for a booking.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if slot reserved successfully
            
        Raises:
            SlotUnavailableError: If slot cannot be reserved
        """
        # Physical room path
        if booking.assigned_room:
            room = booking.assigned_room
            room = type(room).objects.select_for_update().get(id=room.id)
            
            if (room.occupied_slots + room.pending_slots) < room.total_slots:
                room.pending_slots += 1
                room.save()
                return True
            return False
        
        # Fallback to RoomType/UnitType
        if booking.room_type:
            room_type = booking.room_type
            room_type = type(room_type).objects.select_for_update().get(id=room_type.id)
            
            if hasattr(room_type, 'available_slots') and room_type.available_slots > 0:
                room_type.available_slots -= 1
                room_type.save()
                return True
        
        if booking.unit_type:
            unit_type = booking.unit_type
            unit_type = type(unit_type).objects.select_for_update().get(id=unit_type.id)
            
            if hasattr(unit_type, 'available_units') and unit_type.available_units > 0:
                unit_type.available_units -= 1
                unit_type.save()
                return True
        
        return False
    
    @transaction.atomic
    def release_slot(self, booking):
        """
        Release a reserved slot for a booking.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if slot released successfully
        """
        # Physical room path
        if booking.assigned_room:
            room = booking.assigned_room
            room = type(room).objects.select_for_update().get(id=room.id)
            
            if room.pending_slots > 0:
                room.pending_slots -= 1
                room.save()
                return True
            return False
        
        # Fallback to RoomType/UnitType
        if booking.room_type:
            room_type = booking.room_type
            room_type = type(room_type).objects.select_for_update().get(id=room_type.id)
            
            if hasattr(room_type, 'available_slots'):
                room_type.available_slots += 1
                room_type.save()
                return True
        
        if booking.unit_type:
            unit_type = booking.unit_type
            unit_type = type(unit_type).objects.select_for_update().get(id=unit_type.id)
            
            if hasattr(unit_type, 'available_units'):
                unit_type.available_units += 1
                unit_type.save()
                return True
        
        return False
    
    @transaction.atomic
    def confirm_slot(self, booking):
        """
        Convert a pending slot reservation to occupied.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if slot confirmed successfully
        """
        if booking.assigned_room:
            room = booking.assigned_room
            room = type(room).objects.select_for_update().get(id=room.id)
            
            if room.pending_slots > 0:
                room.pending_slots -= 1
                room.occupied_slots += 1
                room.save()
                return True
            return False
        
        return False
    
    def check_slot_availability(self, room_type=None, unit_type=None):
        """
        Check if slots are available.
        
        Args:
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            
        Returns:
            bool: True if slots available
        """
        if room_type:
            if hasattr(room_type, 'available_slots'):
                return room_type.available_slots > 0
            return True  # Assume available if field doesn't exist
        
        if unit_type:
            if hasattr(unit_type, 'available_units'):
                return unit_type.available_units > 0
            return True  # Assume available if field doesn't exist
        
        return False
    
    def get_available_slots_count(self, room_type=None, unit_type=None):
        """
        Get count of available slots.
        
        Args:
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            
        Returns:
            int: Number of available slots
        """
        if room_type:
            if hasattr(room_type, 'available_slots'):
                return room_type.available_slots
            return 0
        
        if unit_type:
            if hasattr(unit_type, 'available_units'):
                return unit_type.available_units
            return 0
        
        return 0
