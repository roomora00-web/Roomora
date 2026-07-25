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
    
    # The payment webhook (services.py) securely handles the state transition.
    # We do not modify the booking status here in the UI anymore to prevent race conditions.
    
    duration_display = f"{booking.duration_months} month(s)" if booking.duration_months else f"{booking.duration_days} day(s)"
    accommodation_property = booking.accommodation_property
    room = booking.assigned_room or booking.room
    room_type = booking.room_type or (room.room_type if room else None)
    unit_type = booking.unit_type or (room.unit_type if room else None)
    
    from accounts.models import LifestyleProfile
    lifestyle_profile = LifestyleProfile.objects.filter(user=request.user).first()
    
    # Collect room and property gallery images
    gallery_images = []
    if room and hasattr(room, 'images') and room.images.exists():
        gallery_images = list(room.images.all())
    if not gallery_images and accommodation_property:
        gallery_images = accommodation_property.all_gallery_images[:6]
    
    context = {
        'payment': payment,
        'booking': booking,
        'property': accommodation_property,
        'room': room,
        'room_type': room_type,
        'unit_type': unit_type,
        'amenities': accommodation_property.amenities.all() if accommodation_property else [],
        'gallery_images': gallery_images,
        'lifestyle_profile': lifestyle_profile,
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


@login_required
def official_receipt_view(request, payment_id):
    """
    Display printable official payment receipt document.
    """
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    
    # Verify user owns this payment or is admin
    if payment.user != request.user and getattr(request.user, 'user_type', None) != 'ADMIN':
        messages.error(request, 'You do not have permission to view this receipt.')
        return redirect('accounts:dashboard')
    
    booking = payment.booking
    duration_display = f"{booking.duration_months} month(s)" if booking.duration_months else f"{booking.duration_days} day(s)"
    accommodation_property = booking.accommodation_property
    room = booking.assigned_room or booking.room
    room_type = booking.room_type or (room.room_type if room else None)
    unit_type = booking.unit_type or (room.unit_type if room else None)
    
    context = {
        'payment': payment,
        'booking': booking,
        'property': accommodation_property,
        'room': room,
        'room_type': room_type,
        'unit_type': unit_type,
        'duration_display': duration_display,
    }
    
    return render(request, 'payments/official_receipt.html', context)
