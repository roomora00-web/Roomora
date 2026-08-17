from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import PaymentRecord
from .services import PaymentService

logger = logging.getLogger(__name__)


@shared_task
def payment_window_expiry(payment_id):
    """
    Celery task that fires exactly at the 2-hour mark.
    Checks if payment has been received and expires if not.
    """
    try:
        payment = PaymentRecord.objects.get(id=payment_id)
    except PaymentRecord.DoesNotExist:
        logger.error(f'Payment not found for expiry task: {payment_id}')
        return
    
    if payment.payment_status == 'completed':
        return  # Already paid — do nothing
    
    service = PaymentService()
    service.expire_payment(payment)
    
    logger.info(f'Payment {payment_id} expired after 2-hour window')


@shared_task
def payment_reminder_1hr(payment_id):
    """
    Sends notification when 1 hour remains in payment window.
    """
    try:
        payment = PaymentRecord.objects.get(id=payment_id)
    except PaymentRecord.DoesNotExist:
        logger.error(f'Payment not found for 1hr reminder: {payment_id}')
        return
    
    if payment.payment_status == 'completed':
        return  # Already paid
    
    # Send notification
    send_payment_reminder_email(
        payment=payment,
        hours_remaining=1,
        urgency='normal'
    )
    
    logger.info(f'1-hour reminder sent for payment {payment_id}')


@shared_task
def payment_reminder_30min(payment_id):
    """
    Sends urgent notification when 30 minutes remain in payment window.
    """
    try:
        payment = PaymentRecord.objects.get(id=payment_id)
    except PaymentRecord.DoesNotExist:
        logger.error(f'Payment not found for 30min reminder: {payment_id}')
        return
    
    if payment.payment_status == 'completed':
        return  # Already paid
    
    # Send urgent notification
    send_payment_reminder_email(
        payment=payment,
        hours_remaining=0.5,
        urgency='urgent'
    )
    
    logger.info(f'30-minute urgent reminder sent for payment {payment_id}')


@shared_task
def verify_payment_status(payment_id):
    """
    Verifies payment status with Paystack verification API.
    Used when gateway status is uncertain (e.g., after timeout).
    """
    service = PaymentService()
    service.verify_payment_status(payment_id)
    
    logger.info(f'Payment verification task completed for {payment_id}')


@shared_task
def bank_transfer_reminder(payment_id):
    """
    Reminds admin to verify bank transfer after 1 hour.
    """
    try:
        payment = PaymentRecord.objects.get(id=payment_id)
    except PaymentRecord.DoesNotExist:
        logger.error(f'Payment not found for bank transfer reminder: {payment_id}')
        return
    
    if payment.payment_status != 'pending_verification':
        return
    
    # Notify admin
    send_admin_bank_transfer_reminder(payment)
    
    logger.info(f'Bank transfer reminder sent to admin for payment {payment_id}')


def send_payment_reminder_email(payment, hours_remaining, urgency):
    """
    Send payment reminder email to user.
    """
    subject = f"Payment Reminder - {hours_remaining} hour(s) remaining"
    
    if urgency == 'urgent':
        subject = f"URGENT: Payment expires in {int(hours_remaining * 60)} minutes"
    
    message = f"""
Dear {payment.user.first_name},

This is a reminder that your payment for booking {payment.booking.reference_number} 
is due within {hours_remaining} hour(s).

Amount: {payment.amount_total} {payment.currency}
Property: {payment.booking.accommodation_property.title}
Room: {payment.booking.assigned_room.room_number if payment.booking.assigned_room else 'TBD'}

Payment Reference: {payment.payment_reference}

Please complete your payment to secure your booking.

If you have already paid, please disregard this message.

Best regards,
StayMatch Team
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [payment.user.email],
            fail_silently=False
        )
    except Exception as e:
        logger.error(f'Failed to send payment reminder email: {e}')


def send_admin_bank_transfer_reminder(payment):
    """
    Send reminder to admin to verify bank transfer.
    """
    subject = f"Bank Transfer Verification Required - {payment.payment_reference}"
    
    message = f"""
Admin,

A bank transfer payment requires verification:

Payment Reference: {payment.payment_reference}
Amount: {payment.amount_total} {payment.currency}
User: {payment.user.email}
Booking: {payment.booking.reference_number}

Please verify this transfer in the admin panel.

Best regards,
StayMatch System
"""
    
    try:
        # Send to admin email (you may want to configure multiple admin emails)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],  # Or specific admin email
            fail_silently=False
        )
    except Exception as e:
        logger.error(f'Failed to send admin bank transfer reminder: {e}')
