"""
Event Handlers - Handlers for domain events.
Processes domain events and triggers side effects.
"""

from bookings.events import event_dispatcher
from bookings.models import Booking, BookingStatusTimeline
from accounts.models import Notification, LifestyleProfile
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


def handle_booking_created(event):
    """Handle booking created event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='BOOKING_CREATED',
        title='Booking Created',
        message=f'Your booking for {booking.accommodation_property.name} has been created successfully.',
        related_booking=booking
    )
    
    # Send confirmation email
    try:
        send_mail(
            subject='Booking Confirmation',
            message=f'Your booking for {booking.accommodation_property.name} has been created. Reference: {booking.reference_number}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.tenant.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Failed to send booking created email: {e}")


def handle_booking_status_changed(event):
    """Handle booking status changed event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='BOOKING_STATUS_CHANGED',
        title=f'Booking Status Updated to {event.data["new_status"]}',
        message=f'Your booking status has been updated to {event.data["new_status"]}. Reason: {event.data["reason"]}',
        related_booking=booking
    )
    
    # Send email for critical status changes
    critical_statuses = ['UNDER_REVIEW', 'CONFIRMED_ASSIGNED', 'ACTIVE', 'REJECTED']
    if event.data['new_status'] in critical_statuses:
        try:
            send_mail(
                subject=f'Booking Status: {event.data["new_status"]}',
                message=f'Your booking status has been updated to {event.data["new_status"]}. Reference: {booking.reference_number}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.tenant.email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send status change email: {e}")


def handle_booking_cancelled(event):
    """Handle booking cancelled event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='BOOKING_CANCELLED',
        title='Booking Cancelled',
        message=f'Your booking has been {event.data["cancellation_type"].lower()}. Reason: {event.data["reason"]}',
        related_booking=booking
    )
    
    # Send cancellation email
    try:
        send_mail(
            subject='Booking Cancelled',
            message=f'Your booking has been {event.data["cancellation_type"].lower()}. Reference: {booking.reference_number}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.tenant.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Failed to send cancellation email: {e}")


def handle_booking_reinstated(event):
    """Handle booking reinstated event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='BOOKING_REINSTATED',
        title='Booking Reinstated',
        message='Your booking has been reinstated. Please complete your booking within 2 hours.',
        related_booking=booking
    )


def handle_room_assigned(event):
    """Handle room assigned event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='ROOM_ASSIGNED',
        title='Room Assigned',
        message=f'Your room has been assigned: {booking.assigned_room.room_number if booking.assigned_room else "TBD"}',
        related_booking=booking
    )
    
    # Lock lifestyle profile if roommate matching
    if booking.booking_type == 'ROOMMATE_MATCH':
        try:
            profile = booking.tenant.lifestyle_profile
            profile.is_locked = True
            profile.save()
        except LifestyleProfile.DoesNotExist:
            pass


def handle_consent_given(event):
    """Handle consent given event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    if event.data['consent_type'] == 'user':
        # Notify roommate if exists
        if booking.roommate:
            Notification.objects.create(
                recipient=booking.roommate,
                notification_type='ROOMMATE_CONSENT_REQUEST',
                title='Roommate Consent Request',
                message=f'{booking.tenant.get_full_name()} has given consent for roommate matching.',
                related_booking=booking
            )
    else:
        # Notify user
        Notification.objects.create(
            recipient=booking.tenant,
            notification_type='ROOMMATE_CONSENT_GIVEN',
            title='Roommate Consent Received',
            message=f'Your roommate has given consent.',
            related_booking=booking
        )


def handle_compatibility_calculated(event):
    """Handle compatibility calculated event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='COMPATIBILITY_CALCULATED',
        title='Compatibility Match Found',
        message=f'Compatibility score: {event.data["compatibility_score"]}%. Routing decision: {event.data["routing_decision"]}',
        related_booking=booking
    )


def handle_booking_activated(event):
    """Handle booking activated event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='BOOKING_ACTIVATED',
        title='Booking Activated',
        message=f'Your booking is now active. Welcome to {booking.accommodation_property.name}!',
        related_booking=booking
    )
    
    # Send welcome email
    try:
        send_mail(
            subject='Welcome! Your Booking is Active',
            message=f'Your booking is now active. Welcome to {booking.accommodation_property.name}! Reference: {booking.reference_number}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.tenant.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Failed to send activation email: {e}")


def handle_booking_completed(event):
    """Handle booking completed event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='BOOKING_COMPLETED',
        title='Booking Completed',
        message='Thank you for staying with us! Your booking has been completed.',
        related_booking=booking
    )


def handle_payment_received(event):
    """Handle payment received event."""
    booking = Booking.objects.get(id=event.data['booking_id'])
    
    # Create notification for tenant
    Notification.objects.create(
        recipient=booking.tenant,
        notification_type='PAYMENT_RECEIVED',
        title='Payment Received',
        message=f'Payment of ${event.data["amount"]} has been received.',
        related_booking=booking
    )


# Register all event handlers
event_dispatcher.subscribe('BOOKING_CREATED', handle_booking_created)
event_dispatcher.subscribe('BOOKING_STATUS_CHANGED', handle_booking_status_changed)
event_dispatcher.subscribe('BOOKING_CANCELLED', handle_booking_cancelled)
event_dispatcher.subscribe('BOOKING_REINSTATED', handle_booking_reinstated)
event_dispatcher.subscribe('ROOM_ASSIGNED', handle_room_assigned)
event_dispatcher.subscribe('CONSENT_GIVEN', handle_consent_given)
event_dispatcher.subscribe('COMPATIBILITY_CALCULATED', handle_compatibility_calculated)
event_dispatcher.subscribe('BOOKING_ACTIVATED', handle_booking_activated)
event_dispatcher.subscribe('BOOKING_COMPLETED', handle_booking_completed)
event_dispatcher.subscribe('PAYMENT_RECEIVED', handle_payment_received)
