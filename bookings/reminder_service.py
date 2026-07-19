"""
Pre-Expiry Reminder Notification Service

Handles automated reminder notifications as per Part 11.1.
Sends reminders at specific intervals before booking expiry and during grace period.
"""

from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .constants import BillingModel
from .grace_period_service import GracePeriodService
from .overstay_service import OverstayService
from .vacation_reserve_service import VacationReserveService


class ReminderService:
    """Service for automated reminder notifications"""
    
    @staticmethod
    def check_and_send_reminders(booking, current_date=None):
        """
        Check if any reminders should be sent today and send them
        
        Returns:
            list of sent reminders
        """
        if current_date is None:
            current_date = date.today()
        
        sent_reminders = []
        
        # Check pre-expiry reminders
        pre_expiry_reminder = ReminderService._check_pre_expiry_reminder(booking, current_date)
        if pre_expiry_reminder:
            ReminderService._send_pre_expiry_reminder(booking, pre_expiry_reminder)
            sent_reminders.append(pre_expiry_reminder)
        
        # Check grace period reminders
        grace_reminder = GracePeriodService.should_send_reminder(booking, current_date)
        if grace_reminder:
            ReminderService._send_grace_period_reminder(booking, grace_reminder)
            sent_reminders.append({'type': grace_reminder, 'category': 'grace_period'})
        
        # Check overstay reminders
        overstay_reminder = OverstayService.should_send_overstay_notification(booking, current_date)
        if overstay_reminder:
            ReminderService._send_overstay_reminder(booking, overstay_reminder)
            sent_reminders.append({'type': overstay_reminder, 'category': 'overstay'})
        
        # Check vacation reminders
        vacation_reminder = VacationReserveService.should_send_vacation_reminder(booking, current_date)
        if vacation_reminder:
            ReminderService._send_vacation_reminder(booking, vacation_reminder)
            sent_reminders.append({'type': vacation_reminder, 'category': 'vacation'})
        
        return sent_reminders
    
    @staticmethod
    def _check_pre_expiry_reminder(booking, current_date):
        """
        Check if a pre-expiry reminder should be sent today
        
        Returns:
            str or None: Reminder type if should send
        """
        move_out_date = booking.move_out_date
        days_until_expiry = (move_out_date - current_date).days
        
        # Weekly reminders (4, 2, 1 weeks before)
        if days_until_expiry == 28:  # 4 weeks
            return 'PRE_EXPIRY_4_WEEKS'
        elif days_until_expiry == 14:  # 2 weeks
            return 'PRE_EXPIRY_2_WEEKS'
        elif days_until_expiry == 7:  # 1 week
            return 'PRE_EXPIRY_1_WEEK'
        
        # Daily reminders (3 days before, day of expiry)
        elif days_until_expiry == 3:
            return 'PRE_EXPIRY_3_DAYS'
        elif days_until_expiry == 0:
            return 'PRE_EXPIRY_DAY_OF'
        
        return None
    
    @staticmethod
    def _send_pre_expiry_reminder(booking, reminder_type):
        """Send pre-expiry reminder email"""
        subject = ReminderService._get_pre_expiry_subject(booking, reminder_type)
        
        context = {
            'student_name': booking.tenant.full_name,
            'property_name': booking.accommodation_property.title,
            'room_number': booking.room_assignment.assigned_room_number if booking.room_assignment else 'N/A',
            'move_out_date': booking.move_out_date,
            'reminder_type': reminder_type,
            'billing_model': booking.billing_model,
        }
        
        message = render_to_string('bookings/emails/pre_expiry_reminder.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.tenant.email],
            html_message=message,
            fail_silently=False
        )
    
    @staticmethod
    def _get_pre_expiry_subject(booking, reminder_type):
        """Get subject line for pre-expiry reminder"""
        subjects = {
            'PRE_EXPIRY_4_WEEKS': f'Your stay at {booking.accommodation_property.title} ends in 4 weeks',
            'PRE_EXPIRY_2_WEEKS': f'2 weeks remaining: Your stay at {booking.accommodation_property.title}',
            'PRE_EXPIRY_1_WEEKS': f'Final week: Your stay at {booking.accommodation_property.title} ends soon',
            'PRE_EXPIRY_3_DAYS': f'3 days remaining: Your stay at {booking.accommodation_property.title}',
            'PRE_EXPIRY_DAY_OF': f'Your paid stay at {booking.accommodation_property.title} has ended',
        }
        return subjects.get(reminder_type, 'Reminder about your booking')
    
    @staticmethod
    def _send_grace_period_reminder(booking, reminder_type):
        """Send grace period reminder email"""
        grace_status = GracePeriodService.get_grace_period_status(booking)
        
        subject = f'Grace Period: Day {grace_status["days_in_grace"]} of {grace_status["grace_period_days"]}'
        
        context = {
            'student_name': booking.tenant.full_name,
            'property_name': booking.accommodation_property.title,
            'move_out_date': booking.move_out_date,
            'grace_period_end': grace_status['grace_period_end'],
            'slot_available_date': grace_status['slot_available_date'],
            'days_remaining': grace_status['days_remaining'],
            'days_in_grace': grace_status['days_in_grace'],
            'reminder_type': reminder_type,
        }
        
        message = render_to_string('bookings/emails/grace_period_reminder.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.tenant.email],
            html_message=message,
            fail_silently=False
        )
    
    @staticmethod
    def _send_overstay_reminder(booking, reminder_type):
        """Send overstay reminder email"""
        overstay_status = OverstayService.get_overstay_status(booking)
        
        if overstay_status['escalated']:
            subject = f'URGENT: Overstay escalation - {booking.accommodation_property.title}'
        else:
            subject = f'Overstay notice - {booking.accommodation_property.title}'
        
        context = {
            'student_name': booking.tenant.full_name,
            'property_name': booking.accommodation_property.title,
            'days_in_overstay': overstay_status['days_in_overstay'],
            'total_charge': overstay_status['total_charge'],
            'daily_rate': overstay_status['overstay_daily_rate'],
            'escalated': overstay_status['escalated'],
            'reminder_type': reminder_type,
        }
        
        message = render_to_string('bookings/emails/overstay_reminder.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.tenant.email],
            html_message=message,
            fail_silently=False
        )
        
        # Also notify admin for escalated overstay
        if overstay_status['escalated']:
            ReminderService._notify_admin_overstay(booking, overstay_status)
    
    @staticmethod
    def _notify_admin_overstay(booking, overstay_status):
        """Notify admin about escalated overstay"""
        subject = f'ESCALATED OVERSTAY: {booking.tenant.full_name} - {booking.accommodation_property.title}'
        
        context = {
            'student_name': booking.tenant.full_name,
            'student_email': booking.tenant.email,
            'property_name': booking.accommodation_property.title,
            'days_in_overstay': overstay_status['days_in_overstay'],
            'total_charge': overstay_status['total_charge'],
            'booking_id': booking.id,
        }
        
        message = render_to_string('bookings/emails/admin_overstay_notification.html', context)
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@staymatch.com')
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            html_message=message,
            fail_silently=False
        )
    
    @staticmethod
    def _send_vacation_reminder(booking, reminder_type):
        """Send vacation reserve reminder email"""
        vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
        
        subject = f'Vacation Reminder: Semester 2 starts soon'
        
        context = {
            'student_name': booking.tenant.full_name,
            'property_name': booking.accommodation_property.title,
            'semester2_start': vacation_status['semester2_start'],
            'semester2_end': vacation_status['semester2_end'],
            'days_until_return': (vacation_status['semester2_start'] - date.today()).days,
            'reminder_type': reminder_type,
        }
        
        message = render_to_string('bookings/emails/vacation_reminder.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.tenant.email],
            html_message=message,
            fail_silently=False
        )
    
    @staticmethod
    def get_reminder_schedule(booking):
        """
        Get complete reminder schedule for a booking
        
        Returns:
            list of all scheduled reminders with dates
        """
        return GracePeriodService.get_pre_expiry_reminder_schedule(booking)
    
    @staticmethod
    def send_rebooking_options(booking):
        """
        Send rebooking options to student (Part 11.2)
        
        Called when pre-expiry reminder is sent
        """
        from .rebooking_service import RebookingService
        
        eligibility = RebookingService.check_rebooking_eligibility(booking)
        
        if not eligibility['eligible']:
            return
        
        subject = f'Rebooking Options Available - {booking.accommodation_property.title}'
        
        context = {
            'student_name': booking.tenant.full_name,
            'property_name': booking.accommodation_property.title,
            'move_out_date': booking.move_out_date,
            'days_remaining': eligibility['days_remaining'],
            'options': eligibility['options'],
        }
        
        message = render_to_string('bookings/emails/rebooking_options.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.tenant.email],
            html_message=message,
            fail_silently=False
        )
