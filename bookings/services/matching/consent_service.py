"""
ConsentService - Consent management for roommate matching.
Handles user and roommate consent tracking and deadlines.
"""

from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from bookings.exceptions import ConsentExpiredError, ValidationError


class ConsentService:
    """Service for consent management."""
    
    CONSENT_DEADLINE_HOURS = 24  # 24-hour consent deadline
    
    def __init__(self):
        pass
    
    @transaction.atomic
    def record_user_consent(self, booking, user_ip=None):
        """
        Record user's consent for a roommate match.
        
        Args:
            booking: Booking object
            user_ip: Optional IP address of user
            
        Returns:
            Updated booking object
            
        Raises:
            ConsentExpiredError: If consent deadline has expired
        """
        # Check if consent deadline has expired
        if booking.consent_deadline and booking.consent_deadline < timezone.now():
            raise ConsentExpiredError()
        
        # Update booking consent fields
        booking.user_consent = True
        booking.user_consent_date = timezone.now()
        booking.user_consent_ip = user_ip
        booking.save()
        
        return booking
    
    @transaction.atomic
    def record_roommate_consent(self, booking, roommate, user_ip=None):
        """
        Record roommate's consent for a match.
        
        Args:
            booking: Booking object
            roommate: User object (the roommate)
            user_ip: Optional IP address of roommate
            
        Returns:
            Updated booking object
            
        Raises:
            ConsentExpiredError: If consent deadline has expired
        """
        # Check if consent deadline has expired
        if booking.consent_deadline and booking.consent_deadline < timezone.now():
            raise ConsentExpiredError()
        
        # Update booking consent fields
        booking.roommate_consent = True
        booking.roommate_consent_date = timezone.now()
        booking.roommate_consent_ip = user_ip
        booking.roommate = roommate
        booking.save()
        
        return booking
    
    def set_consent_deadline(self, booking, hours=None):
        """
        Set consent deadline for a booking.
        
        Args:
            booking: Booking object
            hours: Hours from now (default: CONSENT_DEADLINE_HOURS)
            
        Returns:
            Updated booking object
        """
        if hours is None:
            hours = self.CONSENT_DEADLINE_HOURS
        
        booking.consent_deadline = timezone.now() + timedelta(hours=hours)
        booking.save()
        
        return booking
    
    def check_consent_status(self, booking):
        """
        Check consent status of a booking.
        
        Args:
            booking: Booking object
            
        Returns:
            dict: Consent status information
        """
        status = {
            'user_consent_given': booking.user_consent,
            'roommate_consent_given': booking.roommate_consent,
            'both_consent_given': booking.user_consent and booking.roommate_consent,
            'deadline_expired': False,
            'deadline': booking.consent_deadline,
            'hours_remaining': None,
        }
        
        if booking.consent_deadline:
            if booking.consent_deadline < timezone.now():
                status['deadline_expired'] = True
            else:
                remaining = booking.consent_deadline - timezone.now()
                status['hours_remaining'] = remaining.total_seconds() / 3600
        
        return status
    
    def is_consent_complete(self, booking):
        """
        Check if both user and roommate have given consent.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if both consents given
        """
        return booking.user_consent and booking.roommate_consent
    
    def revoke_consent(self, booking, consent_type='user'):
        """
        Revoke consent (user or roommate).
        
        Args:
            booking: Booking object
            consent_type: 'user' or 'roommate'
            
        Returns:
            Updated booking object
        """
        if consent_type == 'user':
            booking.user_consent = False
            booking.user_consent_date = None
            booking.user_consent_ip = None
        elif consent_type == 'roommate':
            booking.roommate_consent = False
            booking.roommate_consent_date = None
            booking.roommate_consent_ip = None
            booking.roommate = None
        
        booking.save()
        return booking
    
    def send_consent_notification(self, booking, recipient_type='roommate'):
        """
        Send notification to request consent.
        
        Args:
            booking: Booking object
            recipient_type: 'user' or 'roommate'
            
        Returns:
            bool: True if notification sent successfully
        """
        # This would integrate with your notification system
        # For now, return True as placeholder
        from accounts.models import Notification
        
        if recipient_type == 'roommate' and booking.roommate:
            Notification.objects.create(
                recipient=booking.roommate,
                notification_type='ROOMMATE_CONSENT_REQUEST',
                title='Roommate Consent Request',
                message=f'You have been matched with {booking.tenant.get_full_name()}. Please review and provide consent.',
                related_booking=booking
            )
            return True
        
        return False
    
    def get_consent_summary(self, booking):
        """
        Get a summary of consent information for display.
        
        Args:
            booking: Booking object
            
        Returns:
            dict: Consent summary
        """
        status = self.check_consent_status(booking)
        
        return {
            'status': 'COMPLETE' if status['both_consent_given'] else 'PENDING',
            'user_consent': {
                'given': status['user_consent_given'],
                'date': booking.user_consent_date,
            },
            'roommate_consent': {
                'given': status['roommate_consent_given'],
                'date': booking.roommate_consent_date,
                'roommate': booking.roommate.get_full_name() if booking.roommate else None,
            },
            'deadline': {
                'date': status['deadline'],
                'expired': status['deadline_expired'],
                'hours_remaining': status['hours_remaining'],
            }
        }
