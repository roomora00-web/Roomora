from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PaymentRecord


@login_required
def payment_screen_view(request, payment_id):
    """
    Display the payment screen where user selects payment method.
    """
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    
    # Verify user owns this payment
    if payment.user != request.user:
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('accounts:dashboard')
    
    # Check if payment is already completed
    if payment.payment_status == 'completed':
        return redirect('payments:payment_confirmation', payment_id=payment.id)
    
    # Check if payment is expired
    if payment.is_expired:
        messages.error(request, 'This payment has expired. Please contact support.')
        return redirect('accounts:dashboard')
    
    booking = payment.booking
    
    # Calculate duration display
    duration_display = f"{booking.duration_months} month(s)" if booking.duration_months else f"{booking.duration_days} day(s)"
    
    context = {
        'payment': payment,
        'booking': booking,
        'duration_display': duration_display,
    }
    
    return render(request, 'payments/payment_screen.html', context)


@login_required
def payment_confirmation_view(request, payment_id):
    """
    Display payment confirmation screen after successful payment.
    Updates booking status to admin review and redirects to booking confirmation.
    """
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    
    # Verify user owns this payment or is admin
    if payment.user != request.user and request.user.user_type != 'ADMIN':
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('accounts:dashboard')
    
    # Check if payment is actually completed
    if payment.payment_status != 'completed':
        messages.warning(request, 'Payment has not been completed yet.')
        return redirect('payments:payment_screen', payment_id=payment.id)
    
    booking = payment.booking
    
    # Update booking status to move to admin review
    if booking.status == 'PAYMENT_REQUIRED':
        booking.status = 'UNDER_REVIEW'
        booking.payment_status = 'PAID'
        booking.save()
        
        # Create booking history
        from bookings.models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            action='PAYMENT_COMPLETED',
            description='Payment completed successfully. Booking submitted for admin review.',
            performed_by=request.user
        )
        
        # Send notification to user
        from accounts.models import Notification
        Notification.objects.create(
            user=request.user,
            title='Payment Successful',
            message=f'Your payment of GH₵ {payment.amount_total} has been received. Your booking {booking.reference_number} is now under admin review.',
            notification_type='SUCCESS'
        )
    
    duration_display = f"{booking.duration_months} month(s)" if booking.duration_months else f"{booking.duration_days} day(s)"
    
    context = {
        'payment': payment,
        'booking': booking,
        'duration_display': duration_display,
    }
    
    return render(request, 'payments/payment_confirmation.html', context)


@login_required
def bank_transfer_view(request, payment_id):
    """
    Display bank transfer details and instructions.
    """
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    
    # Verify user owns this payment
    if payment.user != request.user:
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('accounts:dashboard')
    
    # Check if payment is already completed
    if payment.payment_status == 'completed':
        return redirect('payments:payment_confirmation', payment_id=payment.id)
    
    # Check if payment is expired
    if payment.is_expired:
        messages.error(request, 'This payment has expired. Please contact support.')
        return redirect('accounts:dashboard')
    
    booking = payment.booking
    
    context = {
        'payment': payment,
        'booking': booking,
    }
    
    return render(request, 'payments/bank_transfer.html', context)


@login_required
def payment_failed_view(request, payment_id):
    """
    Display payment failure screen with retry options.
    """
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    
    # Verify user owns this payment
    if payment.user != request.user:
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('accounts:dashboard')
    
    # Check if payment can be retried
    if not payment.can_retry:
        messages.error(request, 'This payment cannot be retried.')
        return redirect('accounts:dashboard')
    
    booking = payment.booking
    
    # Calculate duration display
    duration_display = f"{booking.duration_months} month(s)" if booking.duration_months else f"{booking.duration_days} day(s)"
    
    context = {
        'payment': payment,
        'booking': booking,
        'duration_display': duration_display,
    }
    
    return render(request, 'payments/payment_failed.html', context)
