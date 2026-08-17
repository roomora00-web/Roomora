"""
RoomAssignmentService - Room assignment operations.
Handles physical room assignment and roommate linking.
"""

from django.db import transaction
from django.db.models import F

from bookings.exceptions import RoomAssignmentError, SlotUnavailableError


class RoomAssignmentService:
    """Service for room assignment operations."""
    
    def __init__(self):
        pass
    
    @transaction.atomic
    def assign_room(self, booking, room, assigned_by=None):
        """
        Assign a physical room to a booking.
        
        Args:
            booking: Booking object
            room: Room object
            assigned_by: User who made the assignment
            
        Returns:
            RoomAssignment object
            
        Raises:
            RoomAssignmentError: If assignment fails
            SlotUnavailableError: If room has no available slots
        """
        from bookings.models import RoomAssignment
        from properties.models import Room
        
        # Check room availability
        room = Room.objects.select_for_update().get(id=room.id)
        if (room.occupied_slots + room.pending_slots) >= room.total_slots:
            raise SlotUnavailableError("Room has no available slots")
        
        # Create room assignment
        assignment = RoomAssignment.objects.create(
            booking=booking,
            room_type=booking.room_type,
            unit_type=booking.unit_type,
            assigned_room=room,
            assigned_by=assigned_by
        )
        
        # Update booking
        booking.assigned_room = room
        booking.save()
        
        # Update room slots
        room.pending_slots += 1
        room.save()
        
        return assignment
    
    @transaction.atomic
    def auto_assign_room(self, booking, assigned_by=None):
        """
        Automatically assign the best available room.
        
        Args:
            booking: Booking object
            assigned_by: User who made the assignment
            
        Returns:
            RoomAssignment object
            
        Raises:
            RoomAssignmentError: If no rooms available
        """
        from properties.models import Room
        from bookings.models import RoomAssignment
        
        # Find available room with most occupants (to fill rooms efficiently)
        available_room = Room.objects.filter(
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type
        ).filter(
            total_slots__gt=F('occupied_slots') + F('pending_slots')
        ).order_by('-occupied_slots').first()
        
        if not available_room:
            raise RoomAssignmentError("No available rooms found")
        
        return self.assign_room(booking, available_room, assigned_by)
    
    @transaction.atomic
    def link_roommates(self, booking, roommates):
        """
        Link roommates to a booking's room assignment.
        
        Args:
            booking: Booking object
            roommates: List of User objects
            
        Returns:
            Updated RoomAssignment object
        """
        from bookings.models import RoomAssignment
        
        assignment = RoomAssignment.objects.filter(booking=booking).first()
        if not assignment:
            raise RoomAssignmentError("No room assignment found for booking")
        
        # Add roommates
        for roommate in roommates:
            assignment.assigned_roommates.add(roommate)
        
        return assignment
    
    @transaction.atomic
    def create_bidirectional_roommate_links(self, booking, roommates):
        """
        Create bidirectional roommate links between all occupants.
        
        Args:
            booking: Booking object
            roommates: List of User objects (other occupants)
        """
        from bookings.models import RoomAssignment, Booking
        
        # Add roommates to new user's assignment
        assignment = RoomAssignment.objects.filter(booking=booking).first()
        if assignment:
            for roommate in roommates:
                assignment.assigned_roommates.add(roommate)
        
        # Update existing occupants' assignments to include new user
        existing_bookings = Booking.objects.filter(
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type,
            assigned_room=booking.assigned_room,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED'],
            tenant__in=roommates
        )
        
        for existing_booking in existing_bookings:
            existing_assignment = RoomAssignment.objects.filter(booking=existing_booking).first()
            if not existing_assignment:
                # Create missing assignment
                existing_assignment = RoomAssignment.objects.create(
                    booking=existing_booking,
                    room_type=existing_booking.room_type,
                    unit_type=existing_booking.unit_type,
                    assigned_room=booking.assigned_room,
                    assigned_by=booking.tenant
                )
            existing_assignment.assigned_roommates.add(booking.tenant)
    
    @transaction.atomic
    def confirm_room_assignment(self, booking):
        """
        Confirm a room assignment (convert pending slot to occupied).
        Triggers payment process according to payment specification.
        
        Args:
            booking: Booking object
            
        Returns:
            Updated booking object
        """
        from properties.models import Room
        
        if not booking.assigned_room:
            raise RoomAssignmentError("No room assigned to booking")
        
        room = Room.objects.select_for_update().get(id=booking.assigned_room.id)
        
        if room.pending_slots > 0:
            room.pending_slots -= 1
        room.occupied_slots += 1
        # Auto-sync room status based on slot counts
        if room.occupied_slots >= room.total_slots:
            room.status = 'FULLY_OCCUPIED'
        elif room.occupied_slots > 0:
            room.status = 'PARTIALLY_OCCUPIED'
        else:
            room.status = 'AVAILABLE'
        room.save()
        
        # Trigger payment process after admin confirms room assignment
        # This implements the payment specification: payment comes after admin approval
        try:
            from payments.services import PaymentService
            payment_service = PaymentService()
            payment_service.initiate_payment(booking, booking.tenant)
        except Exception as e:
            # Log error but don't fail the room assignment
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to initiate payment for booking {booking.id}: {e}')
        
        return booking
    
    @transaction.atomic
    def release_room_assignment(self, booking):
        """
        Release a room assignment.
        
        Args:
            booking: Booking object
            
        Returns:
            Updated booking object
        """
        from properties.models import Room
        from bookings.models import RoomAssignment
        
        if booking.assigned_room:
            room = Room.objects.select_for_update().get(id=booking.assigned_room.id)
            
            if room.occupied_slots > 0:
                room.occupied_slots -= 1
            room.save()
        
        # Delete room assignment
        RoomAssignment.objects.filter(booking=booking).delete()
        
        # Update booking
        booking.assigned_room = None
        booking.save()
        
        return booking
    
    def get_room_occupants(self, room):
        """
        Get all occupants of a room.
        
        Args:
            room: Room object
            
        Returns:
            QuerySet of Booking objects for occupants
        """
        from bookings.models import Booking
        
        return Booking.objects.filter(
            assigned_room=room,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
        ).select_related('tenant')
