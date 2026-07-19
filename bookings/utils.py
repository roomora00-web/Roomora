"""Email utility functions for booking notifications"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_booking_under_review_email(booking, user):
    """Send email when booking is submitted and under review"""
    from django.urls import reverse
    
    try:
        context = {
            'user': user,
            'booking': booking,
            'property': booking.accommodation_property,
            'room_type': booking.room_type,
            'unit_type': booking.unit_type,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        }
        
        html_content = render_to_string('bookings/emails/booking_under_review.html', context)
        
        email = EmailMultiAlternatives(
            subject=f'Booking Submitted - {booking.accommodation_property.title}',
            body=f'Your booking for {booking.accommodation_property.title} has been submitted and is under review.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()
        logger.info(f"Booking under review email sent to {user.email} for booking {booking.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send booking under review email to {user.email}: {str(e)}")
        print(f"ERROR: Failed to send booking under review email to {user.email}: {str(e)}")
        return False


def send_booking_confirmed_email(booking, user, room, roommates=None, compatibility_score=None):
    """Send email when booking is confirmed with room assignment"""
    from django.urls import reverse
    
    try:
        context = {
            'user': user,
            'booking': booking,
            'property': booking.accommodation_property,
            'room': room,
            'roommates': roommates,
            'compatibility_score': compatibility_score,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        }
        
        html_content = render_to_string('bookings/emails/booking_confirmed_with_roommates.html', context)
        
        email = EmailMultiAlternatives(
            subject=f'Booking Confirmed - {booking.accommodation_property.title}',
            body=f'Your booking for {booking.accommodation_property.title} has been confirmed. Room {room.room_number} assigned.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()
        logger.info(f"Booking confirmed email sent to {user.email} for booking {booking.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send booking confirmed email to {user.email}: {str(e)}")
        print(f"ERROR: Failed to send booking confirmed email to {user.email}: {str(e)}")
        return False


def send_new_roommate_email(existing_user, new_user, new_booking, booking, room, compatibility_score):
    """Send email to existing occupants when a new roommate is assigned"""
    from django.urls import reverse
    
    try:
        context = {
            'user': existing_user,
            'new_roommate': new_user,
            'new_booking': new_booking,
            'booking': booking,
            'property': booking.accommodation_property,
            'room': room,
            'compatibility_score': compatibility_score,
            'occupied_slots': room.occupied_slots,
            'total_slots': room.total_slots,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        }
        
        html_content = render_to_string('bookings/emails/new_roommate_assigned.html', context)
        
        email = EmailMultiAlternatives(
            subject=f'New Roommate Assigned - {booking.accommodation_property.title}',
            body=f'A new roommate has been assigned to your room at {booking.accommodation_property.title}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[existing_user.email]
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()
        logger.info(f"New roommate email sent to {existing_user.email} for new roommate {new_user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send new roommate email to {existing_user.email}: {str(e)}")
        print(f"ERROR: Failed to send new roommate email to {existing_user.email}: {str(e)}")
        return False
