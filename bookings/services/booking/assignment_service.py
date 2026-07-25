from django.db import transaction
from django.utils import timezone
from properties.models import Room
from accounts.models import Notification
from bookings.models import BookingHistory

class AssignmentService:
    @staticmethod
    def auto_assign_physical_room(booking):
        """
        Auto-assigns a physical room to a booking after payment.
        Bypasses the Admin Queue.
        """
        # If room is already assigned (e.g. via Route C compatibility match), just activate it
        if booking.assigned_room:
            AssignmentService._activate_booking(booking)
            return True

        # Find an available room of the same room type
        available_rooms = Room.objects.filter(
            room_type=booking.room_type,
            accommodation_property=booking.accommodation_property
        ).select_related('room_type')
        
        # Pick the first room with available slots
        # To avoid fragmenting rooms, we can order by occupied_slots descending
        # so we fill up partially filled rooms first (if shared), or just pick any.
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
            
        # If no room could be found, fall back to Admin Queue
        booking.status = 'UNDER_REVIEW'
        booking.save()
        return False

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
