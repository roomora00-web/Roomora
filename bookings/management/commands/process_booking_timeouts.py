from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking, BookingStatusTimeline
from accounts.models import Notification

class Command(BaseCommand):
    help = 'Processes temporary cancellation timeouts for bookings'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        # 0. Check Consent Timeouts (NEW)
        # For bookings in COMPATIBILITY_REVIEW, if consent_timeout_date is past, auto-reject
        expired_consents = Booking.objects.filter(
            status='COMPATIBILITY_REVIEW',
            consent_timeout_date__lt=now
        )
        
        for booking in expired_consents:
            booking.status = 'TEMPORARILY_CANCELLED'
            booking.cancellation_initiated_by = 'system'
            booking.slot_hold_expires_at = now + timezone.timedelta(hours=6)
            booking.temp_cancel_expires_at = now + timezone.timedelta(hours=24)
            booking.consent_timeout_date = None
            booking.save()
            
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status='COMPATIBILITY_REVIEW',
                new_status='TEMPORARILY_CANCELLED',
                triggered_by_type='SYSTEM',
                reason='Consent timeout expired'
            )
            
            # Notify user about timeout
            Notification.objects.create(
                user=booking.tenant,
                title='CONSENT TIMEOUT',
                message=f'''Your consent period for roommate matching has expired.
Reference: {booking.reference_number}
Property: {booking.accommodation_property.title}

Your booking is temporarily on hold for 24 hours.
You can reinstate it within this window by going to My Bookings.

After 24 hours, the booking will be permanently cancelled.'''
            )
            
            # Notify existing occupants
            from bookings.models import Booking as BookingModel
            existing_bookings = BookingModel.objects.filter(
                accommodation_property=booking.accommodation_property,
                room_type=booking.room_type,
                assigned_room=booking.assigned_room,
                status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
            ).exclude(tenant=booking.tenant)
            
            for existing_booking in existing_bookings:
                Notification.objects.create(
                    user=existing_booking.tenant,
                    title='ROOMMATE MATCH EXPIRED',
                    message=f'''A proposed roommate match for your room has expired.
Room: {booking.assigned_room.room_number if booking.assigned_room else "Assigned"}

The user did not respond within the consent period.
Your room remains open for new roommate matches.
No action required from you.'''
                )
            
            self.stdout.write(self.style.SUCCESS(f"Processed consent timeout for Booking {booking.id}"))
        
        # 1. Check 6-Hour Slot Holds
        # For bookings in TEMPORARILY_CANCELLED, if slot_hold_expires_at is past, release the pending slot
        expired_holds = Booking.objects.filter(
            status='TEMPORARILY_CANCELLED',
            slot_hold_expires_at__lt=now
        )
        
        for booking in expired_holds:
            if booking.assigned_room and booking.assigned_room.pending_slots > 0:
                booking.assigned_room.pending_slots -= 1
                booking.assigned_room.save()
            # Clear the hold so we don't process it again
            booking.slot_hold_expires_at = None
            booking.save()
            self.stdout.write(self.style.SUCCESS(f"Released 6-hour slot hold for Booking {booking.id}"))

        # 2. Check 24-Hour Permanent Cancellations
        # For bookings in TEMPORARILY_CANCELLED, if temp_cancel_expires_at is past, permanently cancel
        expired_cancels = Booking.objects.filter(
            status='TEMPORARILY_CANCELLED',
            temp_cancel_expires_at__lt=now
        )
        
        for booking in expired_cancels:
            booking.status = 'PERMANENTLY_CANCELLED'
            booking.cancellation_date = now
            booking.cancellation_refund = booking.total_amount # Refund full amount
            # Clear the temp cancel expiry
            booking.temp_cancel_expires_at = None
            
            # If the 6-hour hold didn't expire yet for some reason, release the slot now
            if booking.slot_hold_expires_at:
                if booking.assigned_room and booking.assigned_room.pending_slots > 0:
                    booking.assigned_room.pending_slots -= 1
                    booking.assigned_room.save()
                booking.slot_hold_expires_at = None
                
            booking.save()
            
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status='TEMPORARILY_CANCELLED',
                new_status='PERMANENTLY_CANCELLED',
                triggered_by_type='SYSTEM',
                reason='24-hour reinstatement window expired'
            )
            
            self.stdout.write(self.style.SUCCESS(f"Permanently cancelled Booking {booking.id}"))
            
            # John's Notification
            Notification.objects.create(
                user=booking.tenant,
                title='BOOKING PERMANENTLY CLOSED',
                message=f'''Takoradi Hostel — {booking.get_room_type_display() if hasattr(booking, 'get_room_type_display') else "Double Room"}
Reference: {booking.reference_number}

Your 24-hour reinstatement window has passed.
Your booking has been permanently cancelled.

Refund Status: Processing
Amount: GH₵ {booking.total_amount}
Expected: 3-5 business days

What would you like to do next?''',
            )
            
            # Benedict's Notification
            from bookings.models import Booking as BookingModel
            existing_bookings = BookingModel.objects.filter(
                assigned_room=booking.assigned_room,
                status__in=['ACTIVE', 'APPROVED_ASSIGNED', 'CONFIRMED_ASSIGNED']
            ).exclude(tenant=booking.tenant)
            
            roommate = existing_bookings.first().tenant if existing_bookings.exists() else None
            if roommate:
                Notification.objects.create(
                    user=roommate,
                    title='ROOM UPDATE',
                    message=f'''The user who was proposed as your roommate for Room {booking.assigned_room.room_number if booking.assigned_room else "Assigned"} did not confirm their booking.

Your room is now open for a new roommate match.
You will be notified when a compatible user books this room.

No action required from you.'''
                )
                
        self.stdout.write(self.style.SUCCESS('Successfully processed all booking timeouts.'))
