"""
Email Service for Booking Confirmation and Notifications

Handles sending booking confirmation emails and other booking-related emails.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


class EmailService:
    """Service for sending booking-related emails"""
    
    @staticmethod
    def send_booking_confirmation(booking):
        """
        Send booking confirmation email to user (Part 9)
        
        Email includes:
        - Booking reference number
        - Property details
        - Room type and unit type
        - Move-in/move-out dates
        - Duration
        - Price breakdown
        - Roommate information (if applicable)
        - Next steps
        """
        if not booking.tenant.email:
            return {'success': False, 'error': 'No email address for tenant'}
        
        context = {
            'booking': booking,
            'tenant': booking.tenant,
            'property': booking.accommodation_property,
            'room_type': booking.room_type,
            'unit_type': booking.unit_type,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@staymatch.com'),
        }
        
        # Get roommate information if applicable
        if booking.matched_with_booking_id:
            from .models import Booking
            matched_booking = Booking.objects.filter(id=booking.matched_with_booking_id).first()
            if matched_booking:
                context['roommate'] = matched_booking.tenant
                context['compatibility_score'] = booking.compatibility_score
        
        # Render email content
        subject = f"Booking Confirmed - {context['booking_ref']} - {booking.accommodation_property.title}"
        
        html_message = render_to_string(
            'emails/booking_confirmation.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/booking_confirmation.txt',
            context
        )
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[booking.tenant.email],
                html_message=html_message,
                fail_silently=False
            )
            
            return {
                'success': True,
                'message': f'Confirmation email sent to {booking.tenant.email}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_consent_reminder(booking):
        """
        Send consent reminder email (Part 12)
        
        Reminds user that consent deadline is approaching
        """
        if not booking.tenant.email:
            return {'success': False, 'error': 'No email address for tenant'}
        
        context = {
            'booking': booking,
            'tenant': booking.tenant,
            'property': booking.accommodation_property,
            'consent_deadline': booking.consent_deadline,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
        }
        
        subject = f"Action Required: Consent Deadline Approaching - {context['booking_ref']}"
        
        html_message = render_to_string(
            'emails/consent_reminder.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/consent_reminder.txt',
            context
        )
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[booking.tenant.email],
                html_message=html_message,
                fail_silently=False
            )
            
            return {'success': True, 'message': 'Consent reminder sent'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_lifestyle_reminder(booking):
        """
        Send lifestyle questionnaire reminder (Part 12)
        
        Reminds user to complete lifestyle questionnaire
        """
        if not booking.tenant.email:
            return {'success': False, 'error': 'No email address for tenant'}
        
        context = {
            'booking': booking,
            'tenant': booking.tenant,
            'property': booking.accommodation_property,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
        }
        
        subject = f"Reminder: Complete Your Lifestyle Questionnaire - {context['booking_ref']}"
        
        html_message = render_to_string(
            'emails/lifestyle_reminder.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/lifestyle_reminder.txt',
            context
        )
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[booking.tenant.email],
                html_message=html_message,
                fail_silently=False
            )
            
            return {'success': True, 'message': 'Lifestyle reminder sent'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_soft_lock_expiry_warning(booking):
        """
        Send soft-lock expiry warning (Part 12)
        
        Warns user that their booking slot will expire soon
        """
        if not booking.tenant.email:
            return {'success': False, 'error': 'No email address for tenant'}
        
        context = {
            'booking': booking,
            'tenant': booking.tenant,
            'property': booking.accommodation_property,
            'expiry_time': booking.soft_lock_expires_at,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
        }
        
        subject = f"Urgent: Your Booking Slot Expires Soon - {context['booking_ref']}"
        
        html_message = render_to_string(
            'emails/soft_lock_expiry_warning.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/soft_lock_expiry_warning.txt',
            context
        )
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[booking.tenant.email],
                html_message=html_message,
                fail_silently=False
            )
            
            return {'success': True, 'message': 'Soft-lock expiry warning sent'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_booking_cancelled(booking, reason=''):
        """
        Send booking cancellation notification (Part 13)
        
        Notifies user that their booking has been cancelled
        """
        if not booking.tenant.email:
            return {'success': False, 'error': 'No email address for tenant'}
        
        context = {
            'booking': booking,
            'tenant': booking.tenant,
            'property': booking.accommodation_property,
            'cancellation_reason': reason,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
        }
        
        subject = f"Booking Cancelled - {context['booking_ref']}"
        
        html_message = render_to_string(
            'emails/booking_cancelled.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/booking_cancelled.txt',
            context
        )
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[booking.tenant.email],
                html_message=html_message,
                fail_silently=False
            )
            
            return {'success': True, 'message': 'Cancellation notification sent'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_roommate_introduction(booking, matched_booking):
        """
        Send roommate introduction email (Part 13)
        
        Introduces matched roommates to each other
        """
        if not booking.tenant.email or not matched_booking.tenant.email:
            return {'success': False, 'error': 'Missing email addresses'}
        
        context = {
            'booking': booking,
            'matched_booking': matched_booking,
            'tenant': booking.tenant,
            'roommate': matched_booking.tenant,
            'property': booking.accommodation_property,
            'compatibility_score': booking.compatibility_score,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
        }
        
        subject = f"Meet Your Roommate - {context['booking_ref']}"
        
        html_message = render_to_string(
            'emails/roommate_introduction.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/roommate_introduction.txt',
            context
        )
        
        try:
            # Send to both parties
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[booking.tenant.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Swap context for the other roommate
            context['tenant'] = matched_booking.tenant
            context['roommate'] = booking.tenant
            context['booking'] = matched_booking
            
            html_message_swapped = render_to_string(
                'emails/roommate_introduction.html',
                context
            )
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=[matched_booking.tenant.email],
                html_message=html_message_swapped,
                fail_silently=False
            )
            
            return {'success': True, 'message': 'Roommate introductions sent'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_admin_review_notification(booking):
        """
        Send admin review notification (Part 13)
        
        Notifies admins that a booking requires review
        """
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        
        if not admin_emails:
            return {'success': False, 'error': 'No admin emails configured'}
        
        context = {
            'booking': booking,
            'tenant': booking.tenant,
            'property': booking.accommodation_property,
            'booking_ref': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
            'site_name': getattr(settings, 'SITE_NAME', 'StayMatch'),
            'admin_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/admin/bookings/queue/",
        }
        
        subject = f"Admin Review Required - {context['booking_ref']}"
        
        html_message = render_to_string(
            'emails/admin_review_notification.html',
            context
        )
        
        plain_message = render_to_string(
            'emails/admin_review_notification.txt',
            context
        )
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@staymatch.com'),
                recipient_list=admin_emails,
                html_message=html_message,
                fail_silently=False
            )
            
            return {'success': True, 'message': 'Admin review notification sent'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
