"""
AvailabilityService - Availability checking operations.
Handles property, room, and unit availability checks.
"""

from django.db.models import F, Q
from bookings.exceptions import SlotUnavailableError


class AvailabilityService:
    """Service for availability checking."""
    
    def __init__(self):
        pass
    
    def check_property_availability(self, property_obj):
        """
        Check if a property is available for booking.
        
        Args:
            property_obj: Property object
            
        Returns:
            dict: Availability information
        """
        return {
            'available': property_obj.is_available,
            'status': property_obj.status,
            'approved': property_obj.status == 'APPROVED',
        }
    
    def check_room_type_availability(self, room_type):
        """
        Check if a room type has available slots.
        
        Args:
            room_type: RoomType object
            
        Returns:
            dict: Availability information
        """
        available_slots = getattr(room_type, 'available_slots', 0)
        
        return {
            'available': available_slots > 0,
            'available_slots': available_slots,
            'room_type': room_type,
        }
    
    def check_unit_type_availability(self, unit_type):
        """
        Check if a unit type has available units.
        
        Args:
            unit_type: UnitType object
            
        Returns:
            dict: Availability information
        """
        available_units = getattr(unit_type, 'available_units', 0)
        
        return {
            'available': available_units > 0,
            'available_units': available_units,
            'unit_type': unit_type,
        }
    
    def check_room_availability(self, room):
        """
        Check if a physical room has available slots.
        
        Args:
            room: Room object
            
        Returns:
            dict: Availability information
        """
        total_slots = room.total_slots
        occupied_slots = room.occupied_slots
        pending_slots = room.pending_slots
        available_slots = total_slots - occupied_slots - pending_slots
        
        return {
            'available': available_slots > 0,
            'total_slots': total_slots,
            'occupied_slots': occupied_slots,
            'pending_slots': pending_slots,
            'available_slots': available_slots,
            'room': room,
        }
    
    def get_available_rooms(self, property_obj, room_type=None):
        """
        Get list of available rooms for a property.
        
        Args:
            property_obj: Property object
            room_type: Optional RoomType filter
            
        Returns:
            QuerySet of Room objects
        """
        from properties.models import Room
        
        queryset = Room.objects.filter(
            accommodation_property=property_obj,
            total_slots__gt=F('occupied_slots') + F('pending_slots')
        )
        
        if room_type:
            queryset = queryset.filter(room_type=room_type)
        
        return queryset.order_by('-occupied_slots')
    
    def get_total_available_capacity(self, property_obj):
        """
        Get total available capacity for a property.
        
        Args:
            property_obj: Property object
            
        Returns:
            dict: Capacity information
        """
        from properties.models import Room
        
        rooms = Room.objects.filter(accommodation_property=property_obj)
        
        total_slots = rooms.aggregate(
            total_slots=Sum('total_slots'),
            occupied_slots=Sum('occupied_slots'),
            pending_slots=Sum('pending_slots')
        )
        
        available_slots = (
            total_slots['total_slots'] - 
            total_slots['occupied_slots'] - 
            total_slots['pending_slots']
        )
        
        return {
            'total_slots': total_slots['total_slots'] or 0,
            'occupied_slots': total_slots['occupied_slots'] or 0,
            'pending_slots': total_slots['pending_slots'] or 0,
            'available_slots': max(0, available_slots),
        }
    
    def check_date_availability(self, property_obj, start_date, end_date):
        """
        Check if property is available for specific dates.
        
        Args:
            property_obj: Property object
            start_date: Start date
            end_date: End date
            
        Returns:
            dict: Date availability information
        """
        from bookings.models import Booking
        
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            accommodation_property=property_obj,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED', 'INITIATED', 'UNDER_REVIEW']
        ).filter(
            Q(move_in_date__lte=end_date) & Q(move_out_date__gte=start_date)
        )
        
        return {
            'available': overlapping_bookings.count() == 0,
            'overlapping_bookings': overlapping_bookings.count(),
        }
