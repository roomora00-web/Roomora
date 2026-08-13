from django.db import transaction
from django.utils import timezone
from properties.models import Room
from accounts.models import Notification
from bookings.models import BookingHistory

class AssignmentService:
    @staticmethod
    def auto_assign_physical_room(booking):
        """
        Auto-assigns a physical room or unit to a booking after payment.
        Bypasses the Admin Queue and sets status to CONFIRMED_ASSIGNED.
        """
        # 1. If room is already assigned OR property is an Apartment unit, activate immediately
        if booking.assigned_room or (booking.accommodation_property and booking.accommodation_property.property_type == 'APARTMENT') or booking.unit_type:
            AssignmentService._activate_booking(booking)
            return True

        # 2. Find an available room of the same room type for hostels
        if booking.room_type:
            available_rooms = Room.objects.filter(
                room_type=booking.room_type,
                accommodation_property=booking.accommodation_property
            ).select_related('room_type')
            
            best_room = None
            for room in sorted(available_rooms, key=lambda r: r.occupied_slots or 0, reverse=True):
                occupied = room.occupied_slots or 0
                if occupied < room.total_slots:
                    best_room = room
                    break
                    
            if best_room:
                with transaction.atomic():
                    booking.assigned_room = best_room
                    booking.save()
                    AssignmentService._activate_booking(booking)
                return True
            
        # 3. Fallback: activate booking as confirmed assigned
        AssignmentService._activate_booking(booking)
        return True

    @staticmethod
    def _activate_booking(booking):
        booking.status = 'CONFIRMED_ASSIGNED'  # Standard status before move-in.
        booking.save()
        
        # Create history
        BookingHistory.objects.create(
            booking=booking,
            action='AUTO_ASSIGNED_ROOM',
            description=f'Automatically assigned to room {booking.assigned_room.room_number}.',
            performed_by=booking.tenant
        )
        
        # Send Notification
        Notification.objects.create(
            user=booking.tenant,
            title='Room Assigned!',
            message=f'Great news! Your booking is complete and you have been assigned Room {booking.assigned_room.room_number}.',
            notification_type='SUCCESS'
        )
        
        # Send Email
        try:
            from bookings.utils import send_booking_confirmed_email
            send_booking_confirmed_email(
                booking=booking,
                user=booking.tenant,
                room=booking.assigned_room,
                roommates=[],
                compatibility_score=None
            )
        except Exception as e:
            print(f"Failed to send booking confirmed email: {e}")
