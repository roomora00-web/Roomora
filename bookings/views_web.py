"""Web views for Phase 6: Bookings Management"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from django.http import JsonResponse
import json

from .models import (
    Booking, BookingConsent, RoomAssignment, BookingStatusTimeline,
    RoommateMatch, BookingHistory, VisitRequest
)
from properties.models import Property, RoomType, UnitType
from accounts.models import UserProfile


@login_required
def my_bookings_view(request):
    """Phase 6.1: My Bookings Overview Page"""
    bookings = Booking.objects.filter(tenant=request.user).select_related(
        'accommodation_property', 'room_type', 'unit_type'
    ).prefetch_related('roommate_matches')
    
    total_user_bookings = bookings.count()
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'ALL':
        if status_filter in ['PAYMENT_COMPLETE', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 'PAID']:
            bookings = bookings.filter(status__in=['BOTH_ACCEPTED', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 'APPROVED', 'PAYMENT_COMPLETE', 'PAID', 'PAYMENT_VERIFIED', 'ACTIVE'])
        elif status_filter in ['INITIATED', 'PENDING', 'UNDER_REVIEW']:
            bookings = bookings.filter(status__in=['INITIATED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPATIBILITY_REVIEW', 'PAYMENT_REQUIRED', 'LIFESTYLE_PENDING'])
        else:
            bookings = bookings.filter(status=status_filter)
    
    # Sort options
    sort_by = request.GET.get('sort', 'most_recent')
    if sort_by == 'most_recent':
        bookings = bookings.order_by('-created_at')
    elif sort_by == 'lease_start':
        bookings = bookings.order_by('move_in_date')
    elif sort_by == 'status_priority':
        # Custom ordering by status priority
        status_priority = {
            'ACTIVE': 0,
            'APPROVED_ASSIGNED': 1,
            'BOTH_ACCEPTED': 2,
            'WAITING_CONSENT': 3,
            'COMPATIBILITY_REVIEW': 4,
            'UNDER_REVIEW': 5,
            'INITIATED': 5,
            'SUBMITTED': 6,
            'TEMPORARILY_CANCELLED': 8,
            'COMPLETED': 7,
            'CANCELLED': 8,
            'REJECTED': 9,
            'WAITLISTED': 10,
        }
        bookings = sorted(bookings, key=lambda x: status_priority.get(x.status, 100))
    
    # Organize by status for display
    active_bookings = [b for b in bookings if b.status == 'ACTIVE']
    pending_bookings = [b for b in bookings if b.status in ['INITIATED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPATIBILITY_REVIEW', 'PAYMENT_REQUIRED']]
    awaiting_consent = [b for b in bookings if b.status in ['WAITING_CONSENT', 'CONSENT_PENDING']]
    approved_bookings = [b for b in bookings if b.status in ['BOTH_ACCEPTED', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 'APPROVED', 'PAYMENT_COMPLETE', 'PAID', 'PAYMENT_VERIFIED']]
    completed_bookings = [b for b in bookings if b.status == 'COMPLETED']
    temporarily_cancelled_bookings = [b for b in bookings if b.status == 'TEMPORARILY_CANCELLED']
    cancelled_bookings = [b for b in bookings if b.status in ['CANCELLED', 'REJECTED']]
    waitlisted_bookings = [b for b in bookings if b.status == 'WAITLISTED']
    
    confirmed_and_active = approved_bookings + active_bookings
    
    context = {
        'confirmed_and_active': confirmed_and_active,
        'active_bookings': active_bookings,
        'pending_bookings': pending_bookings,
        'awaiting_consent': awaiting_consent,
        'approved_bookings': approved_bookings,
        'completed_bookings': completed_bookings,
        'temporarily_cancelled_bookings': temporarily_cancelled_bookings,
        'cancelled_bookings': cancelled_bookings,
        'waitlisted_bookings': waitlisted_bookings,
        'total_bookings': bookings.count() if hasattr(bookings, 'count') else len(bookings),
        'total_user_bookings': total_user_bookings,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def booking_detail_view(request, booking_id):
    """Phase 6.4: Booking Detail Page"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Access control: only tenant or admin
    if booking.tenant != request.user and request.user.user_type not in ['ADMIN', 'LANDLORD']:
        messages.error(request, 'You do not have access to this booking.')
        return redirect('my-bookings')
    
    # Get related data
    timeline = BookingStatusTimeline.objects.filter(booking=booking).order_by('created_at')
    room_assignment = getattr(booking, 'room_assignment', None)
    roommates = []
    compatibility_score = booking.compatibility_score
    
    if room_assignment and room_assignment.assigned_roommates.exists():
        roommates = list(room_assignment.assigned_roommates.all())
    elif booking.preferred_roommates.exists():
        roommates = list(booking.preferred_roommates.all())
    
    # Calculate lease progress if active
    lease_progress = None
    if booking.status == 'ACTIVE':
        today = timezone.now().date()
        if booking.move_in_date <= today <= booking.move_out_date:
            total_days = (booking.move_out_date - booking.move_in_date).days
            days_elapsed = (today - booking.move_in_date).days
            lease_progress = {
                'percentage': min(100, int((days_elapsed / total_days) * 100)) if total_days > 0 else 0,
                'days_remaining': (booking.move_out_date - today).days,
                'days_elapsed': days_elapsed,
            }
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'timeline': timeline,
        'room_assignment': room_assignment,
        'roommates': roommates,
        'compatibility_score': compatibility_score,
        'lease_progress': lease_progress,
    }
    
    return render(request, 'bookings/booking_detail.html', context)


@login_required
def consent_modal_view(request, booking_id):
    """Phase 6.6: Consent Modal (Review & Accept Match)"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tenant != request.user:
        return redirect('my-bookings')
    
    if booking.status not in ['WAITING_CONSENT', 'ASSIGNED_AWAITING', 'COMPATIBILITY_REVIEW', 'TEMPORARILY_CANCELLED']:
        messages.warning(request, 'This booking is not awaiting your consent.')
        return redirect('bookings:booking-detail', booking_id=booking_id)
    
    # Get consent record
    consent = getattr(booking, 'new_consent_record', None)
    time_remaining = None
    
    if booking.consent_deadline:
        time_remaining = max(0, (booking.consent_deadline - timezone.now()).total_seconds() / 3600)  # hours
    
    # Get compatibility breakdown
    roommate = None
    match_score = booking.compatibility_score or 0
    alignment_factors = []
    difference_factors = []
    
    # Try to get data from actual compatibility result first
    if booking.compatibility_result:
        result = booking.compatibility_result
        match_score = result.get('score', match_score)
        alignment_factors = [a.get('description') or a.get('factor') for a in result.get('alignments', [])]
        
        for diff in result.get('differences', []):
            difference_factors.append({
                'category': diff.get('factor', 'Difference'),
                'your_pref': diff.get('your_value', 'You'),
                'roommate_pref': diff.get('roommate_value', 'Them'),
                'tip': diff.get('suggestion', 'Be open to compromise')
            })
    
    # Resolve roommate occupant accurately
    if not roommate:
        if booking.preferred_roommates.exists():
            roommate = booking.preferred_roommates.first()
        elif booking.room:
            co_booking = Booking.objects.filter(room=booking.room).exclude(id=booking.id).first()
            if co_booking:
                roommate = co_booking.tenant

    # Resolve assigned room & room type details accurately
    room_obj = booking.room or getattr(booking, 'assigned_room', None)
    room_number = room_obj.room_number if room_obj else None
    
    room_type_obj = booking.room_type or (room_obj.room_type if room_obj else None)
    unit_type_obj = booking.unit_type
    
    room_type_name = None
    if room_type_obj:
        room_type_name = getattr(room_type_obj, 'room_type_name', None) or getattr(room_type_obj, 'name', None)
    elif unit_type_obj:
        room_type_name = getattr(unit_type_obj, 'unit_name', None) or getattr(unit_type_obj, 'name', None)

    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'room': room_obj,
        'room_number': room_number,
        'room_type_name': room_type_name,
        'roommate': roommate,
        'match_score': int(match_score),
        'match_verdict': 'Excellent match' if match_score >= 85 else 'Good match' if match_score >= 75 else 'Acceptable match',
        'alignment_factors': alignment_factors,
        'difference_factors': difference_factors,
        'time_remaining': time_remaining,
        'consent_timeout': booking.consent_deadline,
        'consent': consent,
    }
    
    return render(request, 'bookings/consent_modal.html', context)


@login_required
def accept_consent_view(request, booking_id):
    """Handle user acceptance of roommate match"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tenant != request.user:
        messages.error(request, 'Only the booking tenant can accept.')
        return redirect('my-bookings')
    
    if request.method == 'POST':
        confirmed = request.POST.get('confirmed') == 'on'
        
        if not confirmed:
            messages.error(request, 'Please confirm your acceptance.')
            return redirect('consent-modal', booking_id=booking_id)
        
        booking.user_consent = True
        booking.user_consent_date = timezone.now()
        
        # Check if roommate already accepted
        if booking.roommate_consent:
            booking.status = 'BOTH_ACCEPTED'
        else:
            booking.status = 'WAITING_CONSENT'  # Still waiting for roommate
        
        booking.save()
        
        # Log status transition
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='WAITING_CONSENT',
            new_status=booking.status,
            triggered_by=request.user,
            triggered_by_type='USER',
            reason='User accepted roommate match'
        )
        
        # Trigger notification to roommate if they haven't accepted yet
        if not booking.roommate_consent and booking.preferred_roommates.exists():
            roommate = booking.preferred_roommates.first()
            print(f"\n{'='*50}")
            print(f"[NOTIFICATION SYSTEM] EMAIL DISPATCHED")
            print(f"To: {roommate.email}")
            print(f"Subject: New Roommate Match — {booking.accommodation_property.title}")
            print(f"Body: Hi {roommate.first_name},\n")
            print(f"A new user ({request.user.first_name}) has accepted a roommate match for your room ")
            print(f"with a {booking.compatibility_score}% compatibility score.")
            print(f"\nPlease log in to review and accept the match.")
            print(f"{'='*50}\n")
        
        messages.success(request, 'Booking accepted! We\'ll notify you once your roommate responds.')
        return redirect('booking-detail', booking_id=booking_id)
    
    return redirect('consent-modal', booking_id=booking_id)


@login_required
def cancel_booking_view(request, booking_id):
    """Phase 6.7: Booking Cancellation Flow"""
    from django.http import JsonResponse
    import json
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tenant != request.user:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'error': 'You can only cancel your own bookings.'})
        messages.error(request, 'You can only cancel your own bookings.')
        return redirect('my-bookings')
    
    if not booking.status in ['INITIATED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPATIBILITY_REVIEW', 'WAITING_CONSENT']:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'error': f'Cannot cancel a booking with status {booking.get_status_display()}.'})
        messages.error(request, f'Cannot cancel a booking with status {booking.get_status_display()}.')
        return redirect('booking-detail', booking_id=booking_id)
    
    if request.method == 'POST':
        # Handle JSON request from confirmation page
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
            except:
                data = {}
            reason = data.get('cancellation_reason', 'User cancelled from confirmation page')
        else:
            reason = request.POST.get('cancellation_reason', '')
        
        booking.status = 'CANCELLED'
        booking.cancellation_reason = reason
        booking.cancellation_initiated_by = 'user'
        booking.save()
        
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status=booking.status,
            new_status='CANCELLED',
            triggered_by=request.user,
            triggered_by_type='USER',
            reason=f'Cancelled: {reason}'
        )
        
        # Phase 9: Unlock lifestyle profile if it was locked
        if hasattr(request.user, 'lifestyle_profile'):
            profile = request.user.lifestyle_profile
            if profile.is_locked:
                profile.is_locked = False
                profile.save()
        
        # Release room slot if assigned
        if booking.assigned_room and booking.assigned_room.pending_slots > 0:
            booking.assigned_room.pending_slots -= 1
            booking.assigned_room.save()
        
        BookingHistory.objects.create(
            booking=booking,
            action='CANCELLED',
            description=f'Booking cancelled. Reason: {reason}',
            performed_by=request.user
        )
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True, 'redirect_url': '/bookings/my-bookings/'})
        
        messages.success(request, 'Your booking has been cancelled. The room slot is now available.')
        return redirect('my-bookings')
    
    context = {
        'booking': booking,
        'cancellation_reasons': [
            'Found elsewhere',
            'Changed my mind',
            'Issues with property',
            'Personal circumstances',
            'Other',
        ]
    }
    
    return render(request, 'bookings/cancel_booking.html', context)


def submit_visit_request(request):
    """AJAX endpoint to receive and store a VisitRequest with full notifications"""
    from django.conf import settings
    from django.core.mail import send_mail
    from accounts.services import NotificationService
    import urllib.parse

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        property_obj = get_object_or_404(Property, id=property_id)
        
        visit = VisitRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            property=property_obj,
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            visit_date=data.get('visit_date'),
            visit_time=data.get('visit_time'),
            party_size=data.get('party_size', '1 person'),
            contact_method=data.get('contact_method', 'Email'),
            notes=data.get('notes', '')
        )

        owner_name = property_obj.owner_name or (property_obj.uploaded_by.get_full_name() if property_obj.uploaded_by else "Property Manager")
        owner_email = property_obj.owner_email or (property_obj.uploaded_by.email if property_obj.uploaded_by else "admin@roomora.com")
        owner_phone = property_obj.owner_phone or "+233244123456"

        # 1. Send Email Notification to Property Manager
        if owner_email:
            send_mail(
                subject=f"📅 New Visit Request: {property_obj.title}",
                message=(
                    f"Hello {owner_name},\n\n"
                    f"A new property visit request has been submitted on Roomora for {property_obj.title}.\n\n"
                    f"--- Visit Details ---\n"
                    f"• Student Name: {visit.name}\n"
                    f"• Student Email: {visit.email}\n"
                    f"• Student Phone: {visit.phone}\n"
                    f"• Requested Date: {visit.visit_date}\n"
                    f"• Requested Time: {visit.visit_time}\n"
                    f"• Party Size: {visit.party_size}\n"
                    f"• Preferred Contact Method: {visit.contact_method}\n"
                    f"• Notes: {visit.notes or 'None'}\n\n"
                    f"Please contact the student to confirm the appointment."
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'roomora00@gmail.com'),
                recipient_list=[owner_email],
                fail_silently=True
            )

        # 2. Send Dashboard Notification & Confirmation Email to Student (if logged in or email provided)
        if request.user.is_authenticated:
            NotificationService.send_notification(
                user=request.user,
                title="📅 VISIT REQUEST SUBMITTED",
                message=f"Your visit request for {property_obj.title} on {visit.visit_date} at {visit.visit_time} has been sent to manager {owner_name} ({owner_phone}).",
                notification_type="INFO",
                send_email=True
            )
        elif visit.email:
            send_mail(
                subject=f"Visit Request Confirmation - {property_obj.title}",
                message=(
                    f"Hello {visit.name},\n\n"
                    f"Your visit request for {property_obj.title} on {visit.visit_date} at {visit.visit_time} has been received.\n\n"
                    f"Manager Contact:\n"
                    f"• Name: {owner_name}\n"
                    f"• Phone: {owner_phone}\n"
                    f"• Email: {owner_email}\n\n"
                    f"Thank you for choosing Roomora!"
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'roomora00@gmail.com'),
                recipient_list=[visit.email],
                fail_silently=True
            )

        # 3. Construct direct WhatsApp URL for instant manager chat
        clean_phone = owner_phone.replace('+', '').replace(' ', '').replace('-', '')
        wa_text = urllib.parse.quote(f"Hello {owner_name}, I just submitted a visit request for {property_obj.title} on {visit.visit_date} at {visit.visit_time}.")
        whatsapp_url = f"https://wa.me/{clean_phone}?text={wa_text}"
        
        return JsonResponse({
            'success': True,
            'message': 'Visit request submitted successfully',
            'whatsapp_url': whatsapp_url
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bookings.models import Booking, RoomAssignment, ConflictReport

@login_required
def report_conflict_view(request, assignment_id):
    """Phase 13: Conflict Resolution Form"""
    assignment = get_object_or_404(RoomAssignment, id=assignment_id, booking__tenant=request.user)
    
    if request.method == 'POST':
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        attempted_direct_resolution = request.POST.get('attempted_direct_resolution') == 'on'
        preferred_resolution = request.POST.get('preferred_resolution')
        
        report = ConflictReport.objects.create(
            reporter=request.user,
            room_assignment=assignment,
            issue_type=issue_type,
            description=description,
            attempted_direct_resolution=attempted_direct_resolution,
            preferred_resolution=preferred_resolution
        )
        
        # Notify Admins (Phase 13)
        from accounts.models import User, Notification
        admin_users = User.objects.filter(user_type='ADMIN')
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                title='New Conflict Report',
                message=f"Conflict reported by {request.user.email} in Room {assignment.assigned_room.room_number}. Issue: {report.get_issue_type_display()}. Preferred Resolution: {report.get_preferred_resolution_display()}.",
            )
        
        messages.success(request, 'Your conflict report has been submitted. An admin will review it shortly.')
        return redirect('accounts:dashboard')
        
    return render(request, 'bookings/conflict_report.html', {'assignment': assignment})

from functools import wraps

def user_only_view(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'ADMIN':
            from django.shortcuts import redirect
            return redirect('bookings:admin-approval-dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
def vacation_reserve_update_view(request, booking_id):
    """Update Semester 2 Date for Hostels OR Lease Extension for Apartments"""
    from .models import Booking
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Access control
    if booking.tenant != request.user and request.user.user_type not in ['ADMIN', 'LANDLORD']:
        messages.error(request, 'You do not have access to this booking.')
        return redirect('bookings:my-bookings')
        
    prop = booking.accommodation_property
    is_apartment = False
    if booking.unit_type or (prop and prop.property_type in ['APARTMENT', 'STUDIO', 'FLAT', 'TOWNHOUSE', 'VILLA', 'DUPLEX', 'STUDENT_APARTMENT', 'COMPOUND_HOUSE']):
        is_apartment = True

    if request.method == 'POST':
        import json
        from datetime import datetime
        
        new_date_str = None
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                new_date_str = data.get('new_move_out_date') or data.get('vacation_gap_end') or data.get('new_semester2_start')
            except Exception:
                pass
        else:
            new_date_str = request.POST.get('new_move_out_date') or request.POST.get('vacation_gap_end') or request.POST.get('new_semester2_start')

        if new_date_str:
            try:
                parsed_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                if is_apartment:
                    booking.move_out_date = parsed_date
                    if booking.move_in_date:
                        delta_days = (booking.move_out_date - booking.move_in_date).days
                        booking.duration_days = max(1, delta_days)
                        booking.duration_months = max(1, round(delta_days / 30.0))
                    booking.save()
                    msg = f'Apartment lease successfully extended to {booking.move_out_date.strftime("%b %d, %Y")}.'
                else:
                    booking.vacation_gap_end = parsed_date
                    booking.semester_2_start_date = parsed_date
                    booking.save()
                    msg = f'Semester 2 start date updated to {parsed_date.strftime("%b %d, %Y")}.'

                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({'success': True, 'message': msg})

                messages.success(request, msg)
                return redirect('bookings:enter-room', booking_id=booking.id)
            except ValueError:
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
                messages.error(request, 'Invalid date selected.')

    from datetime import date
    min_date = date.today()
    context = {
        'booking': booking,
        'property': prop,
        'is_apartment': is_apartment,
        'min_date': min_date
    }
    return render(request, 'bookings/vacation_reserve_update.html', context)


@login_required
def enter_room_view(request, booking_id):
    """Phase 6.5: Interactive Room Portal Page"""
    from .models import Booking, RoomAssignment, RoomMessage
    from accounts.models import LifestyleProfile
    from datetime import date

    booking = get_object_or_404(Booking, id=booking_id)

    # Access control: only tenant, admin, or landlord
    if booking.tenant != request.user and request.user.user_type not in ['ADMIN', 'LANDLORD']:
        messages.error(request, 'You do not have access to this room portal.')
        return redirect('bookings:my-bookings')

    prop = booking.accommodation_property

    # Ensure assigned_room exists for the booking if property has rooms
    if not booking.assigned_room and prop and prop.rooms.exists():
        room = prop.rooms.filter(room_type=booking.room_type).first() or prop.rooms.first()
        if room:
            booking.assigned_room = room
            booking.save(update_fields=['assigned_room'])

    # Determine property type (Apartment vs Hostel)
    is_apartment = False
    if booking.unit_type or (prop and prop.property_type in ['APARTMENT', 'STUDIO', 'FLAT', 'TOWNHOUSE', 'VILLA', 'DUPLEX', 'STUDENT_APARTMENT', 'COMPOUND_HOUSE']):
        is_apartment = True

    # Determine single occupancy status (1 person stay)
    is_single_occupancy = False
    if is_apartment:
        is_single_occupancy = True
    elif booking.room_type:
        occ = (booking.room_type.occupancy_type or '').upper()
        name = (booking.room_type.room_type_name or '').lower()
        if occ in ['SINGLE', '1_IN_A_ROOM', 'ONE_PERSON', '1_PERSON'] or 'single' in name or '1 in a room' in name or '1-in-a-room' in name or booking.room_type.total_capacity == 1 or booking.room_type.beds_per_room == 1:
            is_single_occupancy = True
    elif booking.assigned_room and (booking.assigned_room.total_slots == 1 or getattr(booking.assigned_room, 'capacity', 1) == 1):
        is_single_occupancy = True
    elif not booking.requires_roommate_matching:
        is_single_occupancy = True

    # Property Owner / Management details
    import urllib.parse
    owner_name = prop.owner_name or (prop.uploaded_by.get_full_name() if prop.uploaded_by else "Property Manager")
    owner_email = prop.owner_email or (prop.uploaded_by.email if prop.uploaded_by else "support@roomora.com")
    owner_phone = prop.owner_phone or (getattr(prop.uploaded_by, 'phone_number', '') if prop.uploaded_by else "+233 20 554 1122")
    owner_photo = prop.owner_photo.url if getattr(prop, 'owner_photo', None) else None
    
    clean_phone = owner_phone.replace('+', '').replace(' ', '').replace('-', '')
    wa_text = f"Hello {owner_name}, I am a tenant at {prop.title} (Booking Ref: {booking.reference_number})."
    whatsapp_owner_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(wa_text)}"

    # Build image gallery prioritizing actual room photos
    all_showcase_images = []
    
    # 1. Assigned physical room photos
    if booking.assigned_room and hasattr(booking.assigned_room, 'images'):
        for rimg in booking.assigned_room.images.all():
            if rimg.image_url:
                all_showcase_images.append({
                    'url': rimg.image_url,
                    'label': f"Room {booking.assigned_room.room_number} Photo",
                    'badge': rimg.get_image_type_display() if hasattr(rimg, 'get_image_type_display') else 'Room Photo'
                })
            
    # 2. Property images (prioritize room/bedroom/bathroom/kitchen/living room over exterior)
    if prop and prop.images.exists():
        sorted_prop_imgs = sorted(
            prop.images.all(),
            key=lambda img: 0 if img.image_type in ['ROOM', 'BEDROOM', 'BATHROOM', 'KITCHEN', 'LIVING_ROOM'] else 1
        )
        for pimg in sorted_prop_imgs:
            if pimg.image_url:
                all_showcase_images.append({
                    'url': pimg.image_url,
                    'label': pimg.caption or f"{prop.title} Interior",
                    'badge': pimg.get_image_type_display() if hasattr(pimg, 'get_image_type_display') else 'Property Photo'
                })

    # 3. Other rooms in property if room images are scarce
    if len(all_showcase_images) < 4 and prop and prop.rooms.exists():
        for rm in prop.rooms.exclude(id=booking.assigned_room.id if booking.assigned_room else None):
            for rimg in rm.images.all():
                if rimg.image_url:
                    all_showcase_images.append({
                        'url': rimg.image_url,
                        'label': f"Room {rm.room_number} Interior",
                        'badge': 'Room Photo'
                    })

    # Room assignment & discussion messages
    room_assignment = getattr(booking, 'room_assignment', None)
    if not room_assignment:
        room_assignment = RoomAssignment.objects.filter(booking=booking).first()

    if not room_assignment:
        room_assignment, _ = RoomAssignment.objects.get_or_create(
            booking=booking,
            defaults={
                'assigned_room': booking.assigned_room,
                'room_type': booking.room_type,
                'unit_type': booking.unit_type,
                'is_active': True
            }
        )

    room_messages = RoomMessage.objects.filter(room_assignment=room_assignment).order_by('created_at')

    # Lifestyle profile
    lifestyle_profile = LifestyleProfile.objects.filter(user=request.user).first()

    # Lease progress calculation
    lease_progress = None
    today = date.today()
    if booking.move_in_date and booking.move_out_date:
        total_days = (booking.move_out_date - booking.move_in_date).days
        days_elapsed = (today - booking.move_in_date).days if today >= booking.move_in_date else 0
        days_remaining = (booking.move_out_date - today).days if today <= booking.move_out_date else 0
        lease_progress = {
            'percentage': max(0, min(100, int((days_elapsed / total_days) * 100))) if total_days > 0 else 0,
            'days_elapsed': max(0, days_elapsed),
            'days_remaining': max(0, days_remaining),
            'total_days': max(1, total_days)
        }

    # Roommates list
    roommates = []
    if room_assignment and hasattr(room_assignment, 'assigned_roommates') and room_assignment.assigned_roommates.exists():
        roommates = room_assignment.assigned_roommates.exclude(id=request.user.id)

    from bookings.models import RoomSetupDeclaration
    all_declarations = RoomSetupDeclaration.objects.filter(room_assignment=room_assignment).order_by('-created_at') if room_assignment else []
    my_declarations = [d for d in all_declarations if d.user == request.user]
    roommate_declarations = [d for d in all_declarations if d.user != request.user]

    context = {
        'booking': booking,
        'property': prop,
        'is_apartment': is_apartment,
        'is_single_occupancy': is_single_occupancy,
        'owner_name': owner_name,
        'owner_email': owner_email,
        'owner_phone': owner_phone,
        'owner_photo': owner_photo,
        'whatsapp_owner_url': whatsapp_owner_url,
        'all_showcase_images': all_showcase_images,
        'room_assignment': room_assignment,
        'room_messages': room_messages,
        'my_declarations': my_declarations,
        'roommate_declarations': roommate_declarations,
        'all_declarations': all_declarations,
        'lifestyle_profile': lifestyle_profile,
        'lease_progress': lease_progress,
        'roommates': roommates,
        'today': today,
    }

    return render(request, 'bookings/enter_room.html', context)

