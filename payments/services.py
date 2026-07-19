from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import requests
import hmac
import hashlib
import json
import logging

from .models import PaymentRecord

User = get_user_model()
logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service class for handling all payment-related operations.
    Integrates with Paystack API for payment processing.
    """
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.callback_url = settings.PAYSTACK_CALLBACK_URL
        self.escrow_subaccount = settings.PAYSTACK_ESCROW_SUBACCOUNT
        self.payment_window_hours = settings.PAYMENT_WINDOW_HOURS
        self.platform_fee_percentage = settings.PLATFORM_FEE_PERCENTAGE
    
    def initiate_payment(self, booking, user):
        """
        Called when admin confirms room assignment.
        Creates payment record and prepares gateway.
        """
        from bookings.models import Booking
        
        # Calculate amounts
        accommodation_amount = booking.total_price
        platform_fee = accommodation_amount * Decimal(str(self.platform_fee_percentage))
        total_charged = accommodation_amount + platform_fee
        
        # Create payment record
        payment = PaymentRecord.objects.create(
            booking=booking,
            user=user,
            amount_accommodation=accommodation_amount,
            amount_platform_fee=platform_fee,
            amount_total=total_charged,
            payment_status='initiated',
            payment_window_opens_at=timezone.now(),
            payment_window_closes_at=timezone.now() + timezone.timedelta(hours=self.payment_window_hours)
        )
        
        # Update booking status
        booking.status = 'PAYMENT_REQUIRED'
        booking.save()
        
        # Schedule 2-hour expiry task
        from .tasks import payment_window_expiry, payment_reminder_1hr, payment_reminder_30min
        payment_window_expiry.apply_async(
            args=[str(payment.id)],
            eta=payment.payment_window_closes_at
        )
        
        # Schedule reminder notifications
        payment_reminder_1hr.apply_async(
            args=[str(payment.id)],
            eta=payment.payment_window_opens_at + timezone.timedelta(hours=1)
        )
        payment_reminder_30min.apply_async(
            args=[str(payment.id)],
            eta=payment.payment_window_closes_at - timezone.timedelta(minutes=30)
        )
        
        # Notify user
        self._send_notification(
            user=user,
            notification_type='payment_required',
            booking=booking,
            payment=payment
        )
        
        return payment
    
    def initialize_paystack_transaction(self, payment, payment_method, mobile_number=None):
        """
        Calls Paystack API to initialize a transaction.
        Returns authorization URL or USSD prompt trigger.
        """
        payment.attempt_count += 1
        payment.last_attempt_at = timezone.now()
        payment.payment_method = payment_method
        payment.payment_status = 'processing'
        payment.save()
        
        # Paystack initialization payload
        payload = {
            'email': payment.user.email,
            'amount': int(payment.amount_total * 100),  # Paystack uses pesewas (smallest unit)
            'reference': payment.payment_reference,
            'currency': 'GHS',
            'metadata': {
                'booking_reference': payment.booking.reference_number,
                'user_id': str(payment.user.id),
                'payment_id': str(payment.id),
                'property_name': payment.booking.accommodation_property.title,
                'room_number': payment.booking.assigned_room.room_number if payment.booking.assigned_room else '',
            },
            'callback_url': self.callback_url,
        }
        
        # Mobile money specific
        if payment_method in ['mtn_momo', 'vodafone_cash', 'airteltigo_money']:
            payload['mobile_money'] = {
                'phone': mobile_number,
                'provider': self._get_momo_provider(payment_method)
            }
        
        # Split payment — platform fee stays, accommodation goes to escrow
        if self.escrow_subaccount:
            payload['split'] = {
                'type': 'flat',
                'bearer_type': 'account',
                'subaccounts': [
                    {
                        'subaccount': self.escrow_subaccount,
                        'amount': int(payment.amount_accommodation * 100)
                    }
                ]
            }
        
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                json=payload,
                headers=headers,
                timeout=30
            )
            data = response.json()
            
            if data['status']:
                payment.gateway_response = data
                payment.save()
                return {
                    'success': True,
                    'authorization_url': data['data'].get('authorization_url'),
                    'access_code': data['data'].get('access_code'),
                    'reference': payment.payment_reference
                }
            else:
                payment.payment_status = 'failed'
                payment.failure_reason = data.get('message', 'Gateway error')
                payment.save()
                return {'success': False, 'error': data.get('message')}
        except requests.RequestException as e:
            payment.payment_status = 'failed'
            payment.failure_reason = f'Network error: {str(e)}'
            payment.save()
            logger.error(f'Paystack initialization error: {e}')
            return {'success': False, 'error': 'Network error occurred'}
    
    def handle_webhook(self, event_data, signature):
        """
        Receives Paystack webhook. Verifies signature.
        Processes payment completion or failure.
        """
        # Verify webhook signature
        computed_hmac = hmac.new(
            self.secret_key.encode('utf-8'),
            event_data,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        if computed_hmac != signature:
            logger.warning('Webhook signature mismatch')
            raise InvalidSignatureError('Webhook signature mismatch')
        
        event = json.loads(event_data)
        
        if event['event'] == 'charge.success':
            self.process_successful_payment(event['data'])
        elif event['event'] == 'charge.failed':
            self.process_failed_payment(event['data'])
    
    def process_successful_payment(self, transaction_data):
        """
        Called when Paystack confirms payment success.
        This is the moment booking becomes confirmed.
        """
        reference = transaction_data['reference']
        
        try:
            payment = PaymentRecord.objects.get(payment_reference=reference)
        except PaymentRecord.DoesNotExist:
            logger.error(f'Payment not found for reference: {reference}')
            return
        
        if payment.payment_status == 'completed':
            return  # Already processed (webhook may fire multiple times)
        
        with transaction.atomic():
            # Update payment record
            payment.payment_status = 'completed'
            payment.paid_at = timezone.now()
            payment.gateway_reference = transaction_data.get('id')
            payment.gateway_response = transaction_data
            payment.save()
            
            # Update booking status
            booking = payment.booking
            booking.status = 'PAYMENT_COMPLETE'
            booking.save()
            
            # Lock lifestyle profile
            self._lock_lifestyle_profile(
                user_id=booking.tenant_id,
                booking_id=booking.id
            )
            
            # If shared room — lock existing occupant too if room now full
            if booking.assigned_room and booking.assigned_room.occupied_slots == booking.assigned_room.total_slots:
                for other_booking in self._get_room_active_bookings(booking.assigned_room):
                    if other_booking.id != booking.id:
                        self._lock_lifestyle_profile(
                            user_id=other_booking.tenant_id,
                            booking_id=other_booking.id
                        )
            
            # Cancel the payment expiry Celery task
            self._cancel_payment_expiry_task(payment.id)
        
        # Send notifications (outside transaction)
        self._send_booking_confirmed_notifications(booking, payment)
    
    def process_failed_payment(self, transaction_data):
        """
        Called when Paystack reports payment failure.
        User can retry within remaining time window.
        """
        reference = transaction_data['reference']
        
        try:
            payment = PaymentRecord.objects.get(payment_reference=reference)
        except PaymentRecord.DoesNotExist:
            logger.error(f'Payment not found for reference: {reference}')
            return
        
        payment.payment_status = 'failed'
        payment.failure_reason = transaction_data.get('gateway_response', 'Payment failed')
        payment.save()
        
        # Check if time window still open
        if timezone.now() < payment.payment_window_closes_at:
            # User can retry
            self._send_notification(
                user=payment.user,
                notification_type='payment_failed_can_retry',
                payment=payment
            )
        else:
            # Window closed — booking expires
            self.expire_payment(payment)
    
    def expire_payment(self, payment):
        """
        Called by Celery task when 2-hour window closes
        without successful payment.
        """
        if payment.payment_status == 'completed':
            return  # Already paid — do nothing
        
        with transaction.atomic():
            payment.payment_status = 'expired'
            payment.save()
            
            booking = payment.booking
            booking.status = 'PAYMENT_EXPIRED'
            booking.save()
            
            # Release slot
            if booking.assigned_room:
                room = booking.assigned_room
                room.pending_slots = max(0, room.pending_slots - 1)
                room.save()
            
            # Unlock lifestyle profile (booking failed)
            self._unlock_lifestyle_profile_on_failure(booking)
        
        self._send_notification(
            user=payment.user,
            notification_type='payment_expired',
            booking=booking
        )
    
    def process_refund(self, payment, refund_amount, reason):
        """
        Initiates refund via Paystack.
        """
        if not payment.gateway_reference:
            return {'success': False, 'error': 'No gateway reference available'}
        
        payload = {
            'transaction': payment.gateway_reference,
            'amount': int(refund_amount * 100),  # In pesewas
            'merchant_note': reason
        }
        
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://api.paystack.co/refund',
                json=payload,
                headers=headers,
                timeout=30
            )
            data = response.json()
            
            if data['status']:
                payment.refund_amount = refund_amount
                payment.refund_initiated_at = timezone.now()
                payment.refund_gateway_reference = data['data'].get('id')
                payment.refund_reason = reason
                payment.payment_status = 'refunded' if refund_amount == payment.amount_total else 'partially_refunded'
                payment.save()
                
                self._send_notification(
                    user=payment.user,
                    notification_type='refund_initiated',
                    amount=refund_amount,
                    method=payment.payment_method
                )
                
                return {'success': True, 'refund_reference': data['data'].get('id')}
            else:
                return {'success': False, 'error': data.get('message')}
        except requests.RequestException as e:
            logger.error(f'Refund processing error: {e}')
            return {'success': False, 'error': 'Network error occurred'}
    
    def verify_payment_status(self, payment_id):
        """
        Verifies payment status with Paystack verification API.
        Used when gateway status is uncertain.
        """
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            logger.error(f'Payment not found for ID: {payment_id}')
            return
        
        if payment.payment_status == 'completed':
            return  # Already resolved
        
        try:
            response = requests.get(
                f'https://api.paystack.co/transaction/verify/{payment.payment_reference}',
                headers={'Authorization': f'Bearer {self.secret_key}'},
                timeout=30
            )
            data = response.json()
            
            if data['data']['status'] == 'success':
                self.process_successful_payment(data['data'])
            elif data['data']['status'] == 'failed':
                self.process_failed_payment(data['data'])
            else:
                # Still pending — check again in 5 minutes if window still open
                if timezone.now() < payment.payment_window_closes_at:
                    from .tasks import verify_payment_status
                    verify_payment_status.apply_async(
                        args=[str(payment_id)],
                        countdown=300  # 5 minutes
                    )
        except requests.RequestException as e:
            logger.error(f'Payment verification error: {e}')
    
    def _get_momo_provider(self, payment_method):
        """Map payment method to Paystack MoMo provider"""
        provider_map = {
            'mtn_momo': 'MTN',
            'vodafone_cash': 'VODAFONE',
            'airteltigo_money': 'AIRTEL_TIGO'
        }
        return provider_map.get(payment_method, 'MTN')
    
    def _send_notification(self, user, notification_type, **kwargs):
        """Send notification to user (placeholder for notification system)"""
        # This will be implemented with the notification system
        logger.info(f'Notification sent to {user.email}: {notification_type}')
    
    def _send_booking_confirmed_notifications(self, booking, payment):
        """Send booking confirmation notifications"""
        # Notify user
        self._send_notification(
            user=booking.tenant,
            notification_type='booking_confirmed',
            booking=booking,
            payment=payment
        )
        
        # Notify roommate if shared room
        if booking.assigned_room and booking.assigned_room.total_slots > 1:
            for other_booking in self._get_room_active_bookings(booking.assigned_room):
                if other_booking.id != booking.id:
                    self._send_notification(
                        user=other_booking.tenant,
                        notification_type='roommate_confirmed',
                        booking=booking
                    )
    
    def _lock_lifestyle_profile(self, user_id, booking_id):
        """Lock lifestyle profile for user"""
        # Placeholder for lifestyle profile locking logic
        logger.info(f'Locking lifestyle profile for user {user_id} on booking {booking_id}')
    
    def _unlock_lifestyle_profile_on_failure(self, booking):
        """Unlock lifestyle profile when booking fails"""
        # Placeholder for lifestyle profile unlocking logic
        logger.info(f'Unlocking lifestyle profile for user {booking.tenant_id} on booking {booking.id}')
    
    def _get_room_active_bookings(self, room):
        """Get active bookings for a room"""
        from bookings.models import Booking
        return Booking.objects.filter(
            assigned_room=room,
            status__in=['CONFIRMED', 'ACTIVE', 'PAYMENT_COMPLETE']
        )
    
    def _cancel_payment_expiry_task(self, payment_id):
        """Cancel payment expiry Celery task"""
        # Placeholder for task cancellation logic
        logger.info(f'Cancelling payment expiry task for payment {payment_id}')


class InvalidSignatureError(Exception):
    """Raised when webhook signature verification fails"""
    pass
