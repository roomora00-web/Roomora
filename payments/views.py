from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from .models import PaymentRecord
from .services import PaymentService, InvalidSignatureError

logger = logging.getLogger(__name__)


class PaystackWebhookView(View):
    """
    Receives Paystack webhook events (POST) and browser callback redirects (GET).
    Verifies signature and processes payment events.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
        
    def get(self, request):
        """
        Handles browser redirect from Paystack after customer completes checkout.
        """
        reference = request.GET.get('reference') or request.GET.get('trxref')
        if not reference:
            return redirect('accounts:dashboard')
        
        # Find PaymentRecord
        payment = PaymentRecord.objects.filter(payment_reference=reference).first()
        if not payment:
            from bookings.models import Booking
            booking = Booking.objects.filter(reference_number=reference).first()
            if booking:
                payment = PaymentRecord.objects.filter(booking=booking).first()
        
        if payment:
            try:
                PaymentService().verify_payment_status(payment.id)
                payment.refresh_from_db()
            except Exception as e:
                logger.error(f"Error verifying payment on GET callback: {e}")
            
            if payment.payment_status == 'completed':
                return redirect('payments:payment_confirmation', payment_id=payment.id)
            elif payment.payment_status == 'failed':
                return redirect('payments:payment_failed', payment_id=payment.id)
            else:
                return redirect('payments:payment_confirmation', payment_id=payment.id)
        
        return redirect('accounts:dashboard')

    def post(self, request):
        signature = request.headers.get('x-paystack-signature')
        if not signature:
            return HttpResponse(status=400)
        
        try:
            PaymentService().handle_webhook(
                event_data=request.body,
                signature=signature
            )
            return HttpResponse(status=200)
        except InvalidSignatureError:
            logger.warning('Invalid webhook signature received')
            return HttpResponse(status=401)
        except Exception as e:
            logger.error(f'Webhook processing error: {e}')
            return HttpResponse(status=500)


class InitiatePaymentView(APIView):
    """
    Initiates payment process after admin assigns room.
    Creates payment record and returns payment details.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        booking_reference = request.data.get('booking_reference')
        
        if not booking_reference:
            return Response(
                {'error': 'booking_reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from bookings.models import Booking
            booking = Booking.objects.get(reference_number=booking_reference)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user owns this booking
        if booking.tenant != request.user:
            return Response(
                {'error': 'You do not have permission to initiate payment for this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if payment already exists
        if booking.payment_records.exists():
            existing_payment = booking.payment_records.first()
            if existing_payment.payment_status == 'completed':
                return Response(
                    {'error': 'Payment already completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({
                'payment_id': str(existing_payment.id),
                'payment_reference': existing_payment.payment_reference,
                'amount_breakdown': {
                    'accommodation': float(existing_payment.amount_accommodation),
                    'platform_fee': float(existing_payment.amount_platform_fee),
                    'total': float(existing_payment.amount_total)
                },
                'payment_window_closes_at': existing_payment.payment_window_closes_at.isoformat(),
                'payment_status': existing_payment.payment_status
            })
        
        # Create new payment
        service = PaymentService()
        payment = service.initiate_payment(booking, request.user)
        
        return Response({
            'payment_id': str(payment.id),
            'payment_reference': payment.payment_reference,
            'amount_breakdown': {
                'accommodation': float(payment.amount_accommodation),
                'platform_fee': float(payment.amount_platform_fee),
                'total': float(payment.amount_total)
            },
            'payment_window_closes_at': payment.payment_window_closes_at.isoformat(),
            'payment_status': payment.payment_status
        }, status=status.HTTP_201_CREATED)


class PaymentStatusView(APIView):
    """
    Returns current payment status and details.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user owns this payment
        if payment.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this payment'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'payment_id': str(payment.id),
            'payment_reference': payment.payment_reference,
            'payment_status': payment.payment_status,
            'amount_total': float(payment.amount_total),
            'amount_breakdown': {
                'accommodation': float(payment.amount_accommodation),
                'platform_fee': float(payment.amount_platform_fee),
                'total': float(payment.amount_total)
            },
            'payment_method': payment.payment_method,
            'time_remaining_seconds': payment.time_remaining_seconds,
            'can_retry': payment.can_retry,
            'is_expired': payment.is_expired,
            'payment_window_closes_at': payment.payment_window_closes_at.isoformat(),
            'attempt_count': payment.attempt_count,
            'failure_reason': payment.failure_reason
        })


class InitializeGatewayTransactionView(APIView):
    """
    Initializes transaction with Paystack for specific payment method.
    Returns authorization URL or USSD prompt details.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        payment_method = request.data.get('payment_method')
        mobile_number = request.data.get('mobile_number')
        
        if not payment_method:
            return Response(
                {'error': 'payment_method is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate payment method
        valid_methods = [choice[0] for choice in PaymentRecord.PAYMENT_METHOD_CHOICES]
        if payment_method not in valid_methods:
            return Response(
                {'error': f'Invalid payment_method. Must be one of: {valid_methods}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Require mobile number for MoMo payments
        if payment_method in ['mtn_momo', 'vodafone_cash', 'airteltigo_money'] and not mobile_number:
            return Response(
                {'error': 'mobile_number is required for mobile money payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user owns this payment
        if payment.user != request.user:
            return Response(
                {'error': 'You do not have permission to initialize this payment'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if payment can be retried
        if not payment.can_retry:
            return Response(
                {'error': 'Payment cannot be retried. Status: ' + payment.payment_status},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize with Paystack
        service = PaymentService()
        result = service.initialize_paystack_transaction(payment, payment_method, mobile_number)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class BankTransferClaimView(APIView):
    """
    User claims they have completed bank transfer.
    Moves payment to pending_verification status.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user owns this payment
        if payment.user != request.user:
            return Response(
                {'error': 'You do not have permission to claim this payment'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update payment status
        payment.payment_status = 'pending_verification'
        payment.payment_method = 'bank_transfer'
        payment.save()
        
        # Schedule admin reminder
        from .tasks import bank_transfer_reminder
        bank_transfer_reminder.apply_async(
            args=[str(payment.id)],
            countdown=3600  # 1 hour
        )
        
        return Response({
            'status': 'pending_verification',
            'message': 'Admin will verify your transfer within 2 hours during business hours'
        })


class AdminVerifyTransferView(APIView):
    """
    Admin endpoint to verify bank transfer.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        # Verify user is admin
        if request.user.user_type != 'ADMIN':
            return Response(
                {'error': 'Only admins can verify transfers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        verified = request.data.get('verified', False)
        admin_notes = request.data.get('admin_notes', '')
        
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if verified:
            # Process as successful payment
            service = PaymentService()
            # Create mock transaction data for bank transfer
            transaction_data = {
                'reference': payment.payment_reference,
                'id': f'BANK-{payment.payment_reference}',
                'status': 'success',
                'gateway_response': 'Bank transfer verified by admin'
            }
            service.process_successful_payment(transaction_data)
            
            return Response({
                'booking_confirmed': True,
                'notifications_sent': True
            })
        else:
            # Mark as failed
            payment.payment_status = 'failed'
            payment.failure_reason = admin_notes or 'Bank transfer verification failed'
            payment.save()
            
            return Response({
                'status': 'failed',
                'message': 'Bank transfer verification failed'
            })


class AdminInitiateRefundView(APIView):
    """
    Admin endpoint to initiate refund.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        # Verify user is admin
        if request.user.user_type != 'ADMIN':
            return Response(
                {'error': 'Only admins can initiate refunds'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refund_amount = request.data.get('refund_amount')
        reason = request.data.get('reason', '')
        
        if not refund_amount:
            return Response(
                {'error': 'refund_amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process refund
        service = PaymentService()
        result = service.process_refund(payment, refund_amount, reason)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class AdminDisburseView(APIView):
    """
    Admin endpoint to mark payment as disbursed to landlord.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        # Verify user is admin
        if request.user.user_type != 'ADMIN':
            return Response(
                {'error': 'Only admins can process disbursements'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        disbursement_method = request.data.get('disbursement_method', 'bank_transfer')
        disbursement_reference = request.data.get('disbursement_reference', '')
        notes = request.data.get('notes', '')
        
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark as disbursed
        payment.disbursed_to_landlord = True
        payment.disbursement_amount = payment.amount_accommodation
        payment.disbursed_at = timezone.now()
        payment.disbursed_by = request.user
        payment.save()
        
        return Response({
            'disbursed': True,
            'amount': float(payment.disbursement_amount),
            'disbursed_at': payment.disbursed_at.isoformat(),
            'disbursed_by': request.user.email
        })


class PaymentReceiptView(APIView):
    """
    Returns payment receipt details.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            payment = PaymentRecord.objects.get(id=payment_id)
        except PaymentRecord.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user owns this payment or is admin
        if payment.user != request.user and request.user.user_type != 'ADMIN':
            return Response(
                {'error': 'You do not have permission to view this receipt'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'payment_reference': payment.payment_reference,
            'booking_reference': payment.booking.reference_number,
            'property': payment.booking.accommodation_property.title,
            'room': payment.booking.assigned_room.room_number if payment.booking.assigned_room else 'TBD',
            'amount_breakdown': {
                'accommodation': float(payment.amount_accommodation),
                'platform_fee': float(payment.amount_platform_fee),
                'total': float(payment.amount_total)
            },
            'payment_method': payment.get_payment_method_display(),
            'payment_status': payment.get_payment_status_display(),
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
            'user': {
                'name': f"{payment.user.first_name} {payment.user.last_name}",
                'email': payment.user.email
            }
        })
