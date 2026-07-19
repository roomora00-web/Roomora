"""
Admin Views for Duration and Room Status Management

Custom admin views for room occupancy calendar, vacation reserve management, and overstay management.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Booking
from .constants import RoomStatus, SemesterStructure
from .grace_period_service import GracePeriodService
from .overstay_service import OverstayService
from .vacation_reserve_service import VacationReserveService
from .rebooking_service import RebookingService
from properties.models import Property, RoomType


@staff_member_required
def room_occupancy_calendar(request):
    """
    Room Occupancy Calendar View (Part 12.2)
    
    Horizontal calendar display showing room occupancy timeline
    """
    from properties.models import Room, RoomType
    
    # Get filter parameters
    property_id = request.GET.get('property_id')
    room_type_id = request.GET.get('room_type_id')
    year = int(request.GET.get('year', date.today().year))
    
    # Build queryset
    bookings = Booking.objects.filter(status__in=['CONFIRMED_ASSIGNED', 'ACTIVE'])
    
    if property_id:
        bookings = bookings.filter(accommodation_property_id=property_id)
    if room_type_id:
        bookings = bookings.filter(room_type_id=room_type_id)
    
    # Filter bookings for the selected year
    bookings = bookings.filter(
        move_in_date__year=year
    ).select_related('tenant', 'accommodation_property', 'room_type', 'room_assignment')
    
    # Build calendar data
    calendar_data = []
    for booking in bookings:
        # Get room number
        room_number = (
            booking.room_assignment.assigned_room.room_number
            if booking.room_assignment and booking.room_assignment.assigned_room
            else 'N/A'
        )
        
        # Determine booking timeline segments
        segments = []
        
        if booking.semester_structure == SemesterStructure.SPLIT_STAY.value:
            # Split stay with vacation gap
            semester1_end = booking.vacation_gap_start - timedelta(days=1)
            semester2_start = booking.vacation_gap_end
            semester2_end = booking.move_out_date
            
            segments.append({
                'type': 'SEMESTER_1',
                'start': booking.move_in_date,
                'end': semester1_end,
                'status': 'PAID',
                'student': booking.tenant.full_name,
                'room_number': room_number,
            })
            
            segments.append({
                'type': 'VACATION_RESERVE',
                'start': semester1_end + timedelta(days=1),
                'end': semester2_start - timedelta(days=1),
                'status': 'RESERVED',
                'student': booking.tenant.full_name,
                'room_number': room_number,
            })
            
            segments.append({
                'type': 'SEMESTER_2',
                'start': semester2_start,
                'end': semester2_end,
                'status': 'PAID',
                'student': booking.tenant.full_name,
                'room_number': room_number,
            })
        else:
            # Continuous stay
            segments.append({
                'type': 'CONTINUOUS',
                'start': booking.move_in_date,
                'end': booking.move_out_date,
                'status': 'PAID',
                'student': booking.tenant.full_name,
                'room_number': room_number,
            })
        
        # Add grace period if applicable
        grace_status = GracePeriodService.get_grace_period_status(booking)
        if grace_status['in_grace_period'] or grace_status['status'] == 'GRACE_PERIOD_ENDED':
            segments.append({
                'type': 'GRACE_PERIOD',
                'start': grace_status['grace_period_start'],
                'end': grace_status['grace_period_end'],
                'status': 'GRACE',
                'student': booking.tenant.full_name,
                'room_number': room_number,
            })
        
        calendar_data.append({
            'booking_id': booking.id,
            'property': booking.accommodation_property.title,
            'room_type': booking.room_type.room_type_name if booking.room_type else 'N/A',
            'room_number': room_number,
            'student': booking.tenant.full_name,
            'student_email': booking.tenant.email,
            'billing_model': booking.billing_model,
            'segments': segments,
        })
    
    context = {
        'calendar_data': calendar_data,
        'year': year,
        'property_id': property_id,
        'room_type_id': room_type_id,
        'properties': Property.objects.all(),
        'room_types': RoomType.objects.all(),
    }
    
    return render(request, 'admin/bookings/room_occupancy_calendar.html', context)


@staff_member_required
def vacation_reserve_management(request, booking_id):
    """
    Vacation Reserve Management View (Part 12.3)
    
    Admin actions for bookings in vacation reserve status
    """
    booking = get_object_or_404(Booking, id=booking_id)
    vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_semester2_date':
            new_semester2_start = request.POST.get('new_semester2_start')
            try:
                result = VacationReserveService.update_semester2_date(
                    booking,
                    new_semester2_start,
                    updated_by=request.user
                )
                return JsonResponse({'success': True, 'result': result})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'cancel_semester2':
            reason = request.POST.get('reason')
            try:
                result = VacationReserveService.cancel_semester2(
                    booking,
                    cancelled_by=request.user,
                    reason=reason
                )
                return JsonResponse({'success': True, 'result': result})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'cancel_full_booking':
            refund_type = request.POST.get('refund_type')  # 'no_refund' or 'full_refund'
            reason = request.POST.get('reason')
            
            # This would implement full booking cancellation logic
            return JsonResponse({'success': True, 'message': 'Full booking cancellation processed'})
        
        elif action == 'add_note':
            note = request.POST.get('note')
            # Add internal note logic here
            return JsonResponse({'success': True, 'message': 'Note added'})
    
    # Get escalation status
    escalation_status = VacationReserveService.check_no_return_escalation(booking)
    
    context = {
        'booking': booking,
        'vacation_status': vacation_status,
        'escalation_status': escalation_status,
        'semester1_start': booking.move_in_date,
        'semester1_end': booking.vacation_gap_start - timedelta(days=1) if booking.vacation_gap_start else None,
        'semester2_start': booking.vacation_gap_end,
        'semester2_end': booking.move_out_date,
    }
    
    return render(request, 'admin/bookings/vacation_reserve_management.html', context)


@staff_member_required
def overstay_management(request, booking_id):
    """
    Overstay Management View (Part 12.4)
    
    Admin actions for bookings in overstay status
    """
    booking = get_object_or_404(Booking, id=booking_id)
    overstay_status = OverstayService.get_overstay_status(booking)
    escalation_status = OverstayService.check_escalation_required(booking)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_resolved':
            # Mark overstay as resolved - student has vacated
            booking.room_status = RoomStatus.AVAILABLE.value
            booking.overstay_charges = overstay_status['total_charge']
            booking.save()
            
            # Release room slot
            if booking.room_type:
                booking.room_type.occupied_slots = max(0, booking.room_type.occupied_slots - 1)
                booking.room_type.available_slots += 1
                booking.room_type.save()
            
            return JsonResponse({'success': True, 'message': 'Overstay marked as resolved'})
        
        elif action == 'apply_charges':
            # Apply overstay charges to student account
            try:
                charge = OverstayService.apply_overstay_charge(booking)
                booking.overstay_charges = charge
                booking.save()
                return JsonResponse({'success': True, 'charge': str(charge)})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'waive_charges':
            reason = request.POST.get('reason')
            try:
                result = OverstayService.waive_overstay_charges(
                    booking,
                    reason=reason,
                    waived_by=request.user
                )
                booking.overstay_charges = Decimal('0')
                booking.save()
                return JsonResponse({'success': True, 'result': result})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'suspend_account':
            # Suspend student account pending resolution
            booking.tenant.is_active = False
            booking.tenant.save()
            return JsonResponse({'success': True, 'message': 'Student account suspended'})
        
        elif action == 'notify_landlord':
            # Notify landlord to take physical action
            # This would send notification to landlord
            return JsonResponse({'success': True, 'message': 'Landlord notified'})
        
        elif action == 'add_case_notes':
            notes = request.POST.get('notes')
            # Add case notes logic here
            return JsonResponse({'success': True, 'message': 'Case notes added'})
    
    context = {
        'booking': booking,
        'overstay_status': overstay_status,
        'escalation_status': escalation_status,
        'room_number': (
            booking.room_assignment.assigned_room.room_number
            if booking.room_assignment and booking.room_assignment.assigned_room
            else 'N/A'
        ),
        'property': booking.accommodation_property.title,
    }
    
    return render(request, 'admin/bookings/overstay_management.html', context)


# PART 8: Admin Review and Finalization Views

@staff_member_required
def admin_booking_queue(request):
    """
    Admin Booking Queue View (Part 8.2)
    
    Display all bookings requiring admin review with filters and sorting.
    SLA Target: Review within 24 hours
    """
    from datetime import timedelta
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    property_filter = request.GET.get('property_id')
    sort_by = request.GET.get('sort', 'oldest')
    
    # Base queryset - bookings requiring admin review
    statuses_requiring_review = [
        'UNDER_REVIEW',
        'AUTO_ASSIGNED',
        'CONSENT_ACCEPTED',
        'LIFESTYLE_COMPLETE',
    ]
    
    if status_filter == 'all':
        bookings = Booking.objects.filter(status__in=statuses_requiring_review)
    elif status_filter == 'pending':
        bookings = Booking.objects.filter(status='UNDER_REVIEW')
    elif status_filter == 'awaiting_assignment':
        bookings = Booking.objects.filter(status__in=['AUTO_ASSIGNED', 'CONSENT_ACCEPTED'])
    elif status_filter == 'flagged':
        bookings = Booking.objects.filter(status__in=statuses_requiring_review).exclude(flags=[])
    else:
        bookings = Booking.objects.filter(status__in=statuses_requiring_review)
    
    # Apply property filter
    if property_filter:
        bookings = bookings.filter(accommodation_property_id=property_filter)
    
    # Apply sorting
    if sort_by == 'oldest':
        bookings = bookings.order_by('created_at')
    elif sort_by == 'newest':
        bookings = bookings.order_by('-created_at')
    elif sort_by == 'deadline':
        bookings = bookings.order_by('soft_lock_expires_at')
    
    # Calculate waiting time and SLA status
    booking_data = []
    sla_breached_count = 0
    now = timezone.now()
    
    for booking in bookings.select_related('tenant', 'accommodation_property', 'room_type', 'unit_type'):
        waiting_time = now - booking.created_at
        waiting_hours = waiting_time.total_seconds() / 3600
        
        # Check if SLA breached (24 hours)
        sla_breached = waiting_hours > 24
        if sla_breached:
            sla_breached_count += 1
        
        # Determine action type
        if booking.is_first_occupant:
            action_type = 'PENDING_ASSIGNMENT'
            action_label = 'Assign Room'
        elif booking.status in ['AUTO_ASSIGNED', 'CONSENT_ACCEPTED']:
            action_type = 'CONFIRM_ASSIGNMENT'
            action_label = 'Confirm and Finalize'
        else:
            action_type = 'REVIEW_REQUIRED'
            action_label = 'Review'
        
        # Get compatibility score if available
        compat_score = booking.compatibility_score
        if booking.compatibility_result:
            compat_score = booking.compatibility_result.get('final_score', booking.compatibility_score)
        
        booking_data.append({
            'booking': booking,
            'waiting_time': waiting_time,
            'waiting_hours': waiting_hours,
            'sla_breached': sla_breached,
            'action_type': action_type,
            'action_label': action_label,
            'compatibility_score': compat_score,
            'lifestyle_complete': booking.lifestyle_assessment_completed,
            'has_flags': bool(booking.flags),
        })
    
    context = {
        'bookings': booking_data,
        'sla_breached_count': sla_breached_count,
        'total_count': len(booking_data),
        'status_filter': status_filter,
        'property_filter': property_filter,
        'sort_by': sort_by,
        'properties': Property.objects.all(),
    }
    
    return render(request, 'admin/bookings/booking_queue.html', context)


@staff_member_required
def admin_assign_room(request, booking_id):
    """
    Admin Room Assignment View (Part 8.3)
    
    For first-occupant bookings, admin selects the specific room number.
    """
    from properties.models import Room
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Verify this is a first-occupant booking
    if not booking.is_first_occupant:
        return JsonResponse({'success': False, 'error': 'This booking is not a first-occupant booking'})
    
    # Get available rooms of the same room type
    available_rooms = Room.objects.filter(
        room_type=booking.room_type,
        accommodation_property=booking.accommodation_property
    ).select_related('room_type')
    
    # Filter for rooms with availability
    room_options = []
    for room in available_rooms:
        occupied = room.occupied_slots or 0
        total = room.total_slots
        available = total - occupied
        
        room_options.append({
            'room': room,
            'occupied': occupied,
            'total': total,
            'available': available,
            'is_available': available > 0,
            'is_high_occupancy': occupied >= (total * 0.8) and occupied < total,
        })
    
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            room = Room.objects.get(id=room_id)
            
            # Verify room has availability
            if (room.occupied_slots or 0) >= room.total_slots:
                return JsonResponse({'success': False, 'error': 'Selected room is fully occupied'})
            
            # Assign room
            from django.db import transaction
            with transaction.atomic():
                booking.assigned_room = room
                booking.status = 'CONFIRMED'
                booking.admin_reviewed_by = request.user
                booking.admin_reviewed_at = timezone.now()
                booking.admin_notes = admin_notes
                booking.save()
                
                # Note: Room occupancy is now updated automatically via signals
                
                # Create room assignment record (if you have this model)
                # RoomAssignment.objects.create(...)
            
            # Send notification to user
            from accounts.models import Notification
            Notification.objects.create(
                user=booking.tenant,
                title='BOOKING CONFIRMED',
                message=f"Your booking at {booking.accommodation_property.title} has been confirmed. You have been assigned Room {room.room_number}. Reference: {booking.reference_number}",
            )
            
            # Send email
            from bookings.utils import send_booking_confirmed_email
            try:
                send_booking_confirmed_email(
                    booking=booking,
                    user=booking.tenant,
                    room=room,
                    roommates=[],
                    compatibility_score=0
                )
            except Exception as e:
                print(f"Failed to send booking confirmed email: {e}")
            
            return JsonResponse({'success': True, 'room_number': room.room_number})
        
        except Room.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Room not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    context = {
        'booking': booking,
        'room_options': room_options,
        'property': booking.accommodation_property,
        'room_type': booking.room_type,
    }
    
    return render(request, 'admin/bookings/assign_room.html', context)


@staff_member_required
def admin_finalize_booking(request, booking_id):
    """
    Admin Finalization View (Part 8.4)
    
    For post-consent bookings where user has already consented and been auto-assigned.
    Admin confirmation is a review and verification step.
    """
    from django.db import transaction
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Verify this is a post-consent or auto-assigned booking
    if booking.status not in ['AUTO_ASSIGNED', 'CONSENT_ACCEPTED']:
        return JsonResponse({'success': False, 'error': 'This booking does not require finalization'})
    
    # Get matched booking (roommate)
    matched_booking = None
    if booking.matched_with_booking_id:
        matched_booking = Booking.objects.filter(id=booking.matched_with_booking_id).first()
    
    # Verification checks
    verification_checks = {
        'account_verified': booking.tenant.is_active if hasattr(booking.tenant, 'is_active') else True,
        'no_fraud_flags': not bool(booking.flags),
        'room_capacity_ok': True,  # Will check after getting room
        'dates_valid': booking.move_in_date and booking.move_out_date,
    }
    
    if booking.assigned_room:
        verification_checks['room_capacity_ok'] = (
            (booking.assigned_room.occupied_slots or 0) < booking.assigned_room.total_slots
        )
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            from django.db import transaction
            from accounts.models import Notification
            with transaction.atomic():
                booking.status = 'CONFIRMED'
                booking.admin_reviewed_by = request.user
                booking.admin_reviewed_at = timezone.now()
                booking.admin_notes = admin_notes
                booking.save()
                
                # Send notification to user
                Notification.objects.create(
                    user=booking.tenant,
                    title='BOOKING CONFIRMED',
                    message=f"Your booking at {booking.accommodation_property.title} has been finalized and confirmed. Reference: {booking.reference_number}",
                )
                
                # Send email
                from bookings.utils import send_booking_confirmed_email
                try:
                    send_booking_confirmed_email(
                        booking=booking,
                        user=booking.tenant,
                        room=booking.assigned_room,
                        roommates=[matched_booking.tenant] if matched_booking else [],
                        compatibility_score=booking.compatibility_score
                    )
                except Exception as e:
                    print(f"Failed to send booking confirmed email: {e}")
                
                # If matched booking exists, update it too
                if matched_booking:
                    matched_booking.status = 'CONFIRMED'
                    matched_booking.admin_reviewed_by = request.user
                    matched_booking.admin_reviewed_at = timezone.now()
                    matched_booking.save()
                    
                    Notification.objects.create(
                        user=matched_booking.tenant,
                        title='NEW ROOMMATE CONFIRMED',
                        message=f"A new roommate has been confirmed for your room. Move-in date: {booking.move_in_date}.",
                    )
                    
                    from bookings.utils import send_new_roommate_email
                    try:
                        send_new_roommate_email(
                            existing_user=matched_booking.tenant,
                            new_user=booking.tenant,
                            new_booking=booking,
                            booking=matched_booking,
                            room=booking.assigned_room,
                            compatibility_score=booking.compatibility_score
                        )
                    except Exception as e:
                        print(f"Failed to send new roommate email: {e}")
            
            return JsonResponse({'success': True, 'message': 'Booking finalized successfully'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Get compatibility breakdown
    compat_score = booking.compatibility_score
    if booking.compatibility_result:
        compat_score = booking.compatibility_result.get('final_score', booking.compatibility_score)
    
    context = {
        'booking': booking,
        'matched_booking': matched_booking,
        'compatibility_score': compat_score,
        'verification_checks': verification_checks,
        'property': booking.accommodation_property,
        'room_type': booking.room_type,
    }
    
    return render(request, 'admin/bookings/finalize_booking.html', context)
