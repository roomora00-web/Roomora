"""
Notification Service for Booking Events (Part 13)

Centralized service for handling all user and admin notifications throughout the booking lifecycle.
"""

from django.utils import timezone
from accounts.services import NotificationService as CoreNotificationService

def _send_notification(**kwargs):
    if not kwargs.get('user'):
        return
    CoreNotificationService.send_notification(
        user=kwargs.get('user'),
        title=kwargs.get('title'),
        message=kwargs.get('message'),
        notification_type=kwargs.get('notification_type', 'INFO'),
        send_email=True,
        email_template='accounts/emails/booking_update.html'
    )


class NotificationService:
    """Service for managing booking-related notifications"""
    
    @staticmethod
    def notify_booking_initiated(booking):
        """
        Notify user when booking is initiated (Part 13)
        """
        _send_notification(
            user=booking.tenant,
            title='BOOKING INITIATED',
            message=f"Your booking has been initiated successfully!\n\nProperty: {booking.accommodation_property.title}\nRoom Type: {booking.room_type.room_type_name if booking.room_type else 'N/A'}\nReference: {booking.reference_number}\n\nComplete your booking within 48 hours to secure your slot.",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_house_rules_acknowledged(booking):
        """
        Notify user when house rules are acknowledged
        """
        _send_notification(
            user=booking.tenant,
            title='HOUSE RULES ACKNOWLEDGED',
            message=f"You have acknowledged the house rules for {booking.accommodation_property.title}.\n\nYou can now proceed to select your duration.",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_duration_selected(booking):
        """
        Notify user when duration is selected
        """
        _send_notification(
            user=booking.tenant,
            title='DURATION SELECTED',
            message=f"Your stay duration has been set:\n\nMove-in: {booking.move_in_date.strftime('%B %d, %Y')}\nMove-out: {booking.move_out_date.strftime('%B %d, %Y')}\nDuration: {booking.duration_days} days\n\nNext: Complete your lifestyle questionnaire.",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_lifestyle_submitted(booking):
        """
        Notify user when lifestyle questionnaire is submitted
        """
        _send_notification(
            user=booking.tenant,
            title='LIFESTYLE QUESTIONNAIRE SUBMITTED',
            message=f"Your lifestyle preferences have been saved.\n\nWe are now finding the best roommate match for you based on your preferences.\n\nReference: {booking.reference_number}",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_compatibility_result(booking, score):
        """
        Notify user when compatibility result is ready
        """
        if score >= 85:
            message = f"Great news! We found an excellent match for you.\n\nCompatibility Score: {score}%\n\nYou have been automatically assigned to a room with a compatible roommate.\n\nPlease review and confirm your booking."
            notification_type = 'SUCCESS'
        else:
            message = f"We found a potential roommate match for you.\n\nCompatibility Score: {score}%\n\nPlease review the compatibility details and decide if you would like to accept this match.\n\nYou have 24 hours to respond."
            notification_type = 'INFO'
        
        _send_notification(
            user=booking.tenant,
            title='ROOMMATE MATCH FOUND',
            message=message,
            notification_type=notification_type
        )
    
    @staticmethod
    def notify_consent_accepted(booking):
        """
        Notify user when consent is accepted
        """
        _send_notification(
            user=booking.tenant,
            title='BOOKING ACCEPTED',
            message=f"You have accepted your roommate match.\n\nYour booking is now pending final admin confirmation.\n\nReference: {booking.reference_number}\n\nYou will receive a confirmation email once your booking is finalized.",
            notification_type='SUCCESS'
        )
    
    @staticmethod
    def notify_consent_rejected(booking):
        """
        Notify user when consent is rejected
        """
        _send_notification(
            user=booking.tenant,
            title='BOOKING REJECTED',
            message=f"You have declined this roommate match.\n\nYour booking has been temporarily cancelled.\n\nYou have 24 hours to reinstate your booking and try again with different preferences.\n\nReference: {booking.reference_number}",
            notification_type='WARNING'
        )
    
    @staticmethod
    def notify_booking_reinstated(booking):
        """
        Notify user when booking is reinstated
        """
        _send_notification(
            user=booking.tenant,
            title='BOOKING REINSTATED',
            message=f"Your booking has been reinstated successfully.\n\nYou can now proceed with the booking process.\n\nReference: {booking.reference_number}",
            notification_type='SUCCESS'
        )
    
    @staticmethod
    def notify_booking_permanently_cancelled(booking, reason=''):
        """
        Notify user when booking is permanently cancelled
        """
        message = f"Your booking has been permanently cancelled.\n\nReference: {booking.reference_number}"
        
        if reason:
            message += f"\n\nReason: {reason}"
        
        if booking.refund_status == 'pending':
            message += f"\n\nRefund Status: Processing\nAmount: GH₵ {booking.refund_amount or booking.total_amount}\nExpected: 3-5 business days"
        
        _send_notification(
            user=booking.tenant,
            title='BOOKING CANCELLED',
            message=message,
            notification_type='ERROR'
        )
    
    @staticmethod
    def notify_booking_confirmed(booking):
        """
        Notify user when booking is confirmed by admin
        """
        _send_notification(
            user=booking.tenant,
            title='BOOKING CONFIRMED',
            message=f"Congratulations! Your booking has been confirmed.\n\nProperty: {booking.accommodation_property.title}\nRoom: {booking.assigned_room.room_number if booking.assigned_room else 'To be assigned'}\nMove-in: {booking.move_in_date.strftime('%B %d, %Y')}\n\nA confirmation email has been sent to your email address.\n\nReference: {booking.reference_number}",
            notification_type='SUCCESS'
        )
    
    @staticmethod
    def notify_roommate_introduction(booking, matched_booking):
        """
        Notify both parties when they are matched as roommates
        """
        # Notify current user
        _send_notification(
            user=booking.tenant,
            title='MEET YOUR ROOMMATE',
            message=f"You have been matched with {matched_booking.tenant.full_name}!\n\nCompatibility Score: {booking.compatibility_score}%\n\nYou can contact your roommate to coordinate on shared items and establish communication before move-in.\n\nReference: {booking.reference_number}",
            notification_type='INFO'
        )
        
        # Notify matched roommate
        _send_notification(
            user=matched_booking.tenant,
            title='MEET YOUR ROOMMATE',
            message=f"You have been matched with {booking.tenant.full_name}!\n\nCompatibility Score: {matched_booking.compatibility_score}%\n\nYou can contact your roommate to coordinate on shared items and establish communication before move-in.\n\nReference: {matched_booking.reference_number}",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_admin_review_required(booking):
        """
        Notify admins when a booking requires review
        """
        # This would typically send to admin users
        # For now, we'll create a system notification
        _send_notification(
            user=None,  # System notification for admins
            title='ADMIN REVIEW REQUIRED',
            message=f"Booking requires admin review.\n\nApplicant: {booking.tenant.full_name}\nProperty: {booking.accommodation_property.title}\nRoom Type: {booking.room_type.room_type_name if booking.room_type else 'N/A'}\nStatus: {booking.status}\nReference: {booking.reference_number}\n\nAction Required: Review and process this booking.",
            notification_type='URGENT'
        )
    
    @staticmethod
    def notify_admin_booking_assigned(booking, admin_user):
        """
        Notify admin when booking is assigned
        """
        _send_notification(
            user=admin_user,
            title='BOOKING ASSIGNED',
            message=f"You have assigned Room {booking.assigned_room.room_number if booking.assigned_room else 'N/A'} to {booking.tenant.full_name}.\n\nReference: {booking.reference_number}\n\nBooking status updated to CONFIRMED.",
            notification_type='SUCCESS'
        )
    
    @staticmethod
    def notify_admin_booking_finalized(booking, admin_user):
        """
        Notify admin when booking is finalized
        """
        _send_notification(
            user=admin_user,
            title='BOOKING FINALIZED',
            message=f"You have finalized the booking for {booking.tenant.full_name}.\n\nReference: {booking.reference_number}\n\nBooking status updated to CONFIRMED.",
            notification_type='SUCCESS'
        )
    
    @staticmethod
    def notify_move_in_reminder(booking, days_before=7):
        """
        Notify user before move-in date
        """
        _send_notification(
            user=booking.tenant,
            title=f'MOVE-IN IN {days_before} DAYS',
            message=f"Your move-in date is approaching!\n\nMove-in Date: {booking.move_in_date.strftime('%B %d, %Y')}\nProperty: {booking.accommodation_property.title}\nRoom: {booking.assigned_room.room_number if booking.assigned_room else 'To be assigned'}\n\nPlease ensure you have completed all payments and preparations.",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_grace_period_started(booking):
        """
        Notify user when grace period starts
        """
        _send_notification(
            user=booking.tenant,
            title='GRACE PERIOD STARTED',
            message=f"Your booking has ended and you are now in your grace period.\n\nGrace Period Ends: {booking.grace_period_end.strftime('%B %d, %Y')}\n\nPlease ensure you vacate the room by this date to avoid overstay charges.",
            notification_type='WARNING'
        )
    
    @staticmethod
    def notify_overstay_started(booking):
        """
        Notify user when overstay begins
        """
        _send_notification(
            user=booking.tenant,
            title='OVERSTAY CHARGES BEGINNING',
            message=f"Your grace period has ended. You are now in overstay status.\n\nOverstay charges will begin accruing immediately.\nDaily Rate: GH₵ {booking.overstay_daily_rate or 'N/A'}\n\nPlease contact administration immediately to resolve this matter.",
            notification_type='URGENT'
        )
    
    @staticmethod
    def notify_vacation_reserve_started(booking):
        """
        Notify user when vacation reserve starts
        """
        _send_notification(
            user=booking.tenant,
            title='VACATION RESERVE ACTIVE',
            message=f"Your vacation reserve is now active.\n\nYour room is being held for your Semester 2 return.\nReturn Date: {booking.vacation_reserve_end.strftime('%B %d, Y') if booking.vacation_reserve_end else 'TBD'}\n\nYou will receive reminders before your return date.",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_semester2_return_reminder(booking, days_before=7):
        """
        Notify user before Semester 2 return
        """
        _send_notification(
            user=booking.tenant,
            title=f'SEMESTER 2 RETURN IN {days_before} DAYS',
            message=f"Your Semester 2 return date is approaching.\n\nReturn Date: {booking.semester_2_start_date.strftime('%B %d, Y')}\nProperty: {booking.accommodation_property.title}\n\nPlease ensure you are prepared to return.",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_semester2_cancelled(booking):
        """
        Notify user when Semester 2 is cancelled
        """
        _send_notification(
            user=booking.tenant,
            title='SEMESTER 2 CANCELLED',
            message=f"Your Semester 2 booking has been cancelled.\n\nReference: {booking.reference_number}\n\nRefund Status: {booking.refund_status}\nAmount: GH₵ {booking.refund_amount or 'Processing'}",
            notification_type='INFO'
        )
    
    @staticmethod
    def notify_payment_received(booking, amount):
        """
        Notify user when payment is received
        """
        _send_notification(
            user=booking.tenant,
            title='PAYMENT RECEIVED',
            message=f"Payment of GH₵ {amount} has been received for your booking.\n\nReference: {booking.reference_number}\n\nTotal Paid: GH₵ {booking.amount_paid}\nRemaining Balance: GH₵ {booking.total_amount - booking.amount_paid}",
            notification_type='SUCCESS'
        )
    
    @staticmethod
    def notify_payment_overdue(booking):
        """
        Notify user when payment is overdue
        """
        _send_notification(
            user=booking.tenant,
            title='PAYMENT OVERDUE',
            message=f"Your payment is now overdue.\n\nAmount Due: GH₵ {booking.total_amount - booking.amount_paid}\nReference: {booking.reference_number}\n\nPlease complete your payment to avoid cancellation.",
            notification_type='URGENT'
        )
    
    @staticmethod
    def notify_booking_modified(booking, changes):
        """
        Notify user when booking is modified by admin
        """
        changes_text = "\n".join([f"- {key}: {value}" for key, value in changes.items()])
        
        _send_notification(
            user=booking.tenant,
            title='BOOKING MODIFIED',
            message=f"Your booking has been modified by administration.\n\nChanges:\n{changes_text}\n\nReference: {booking.reference_number}\n\nIf you have questions, please contact support.",
            notification_type='INFO'
        )
