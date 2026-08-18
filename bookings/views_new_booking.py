"""
New Booking Flow Views

Implements the new booking initiation flow according to the specification:
- Prerequisite validation (5 checks)
- House rules acknowledgment
- Atomic soft lock
- Celery task scheduling
- Notification sending
- Duration selection (Part 3)
- Lifestyle preferences (Part 4)
- Routing engine (Part 5)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
from accounts.models import Notification, LifestyleProfile
from properties.models import Property, RoomType, UnitType
from bookings.models import Booking, HouseRulesAcknowledgment, BookingHistory
from bookings.services.booking.prerequisite_service import PrerequisiteService
from bookings.services.booking.soft_lock_service import SoftLockService
from bookings.services.booking.duration_service import DurationService
from bookings.tasks import schedule_soft_lock_tasks


LIFESTYLE_QUIET_HOURS_STILL_NEEDED_CHOICES = [
    ('YES', 'Yes, definitely — even when studying outside, I need quiet to sleep'),
    ('SOMEWHAT', 'Somewhat — some quiet is helpful'),
    ('NOT_REALLY', 'Not really — I can manage with noise'),
    ('NO', 'No — I study elsewhere and am not in the room much'),
]

LIFESTYLE_QUIET_TIMES_CHOICES = [
    ('EVENINGS', 'Evenings (after 6pm)'),
    ('LATE_NIGHTS', 'Late nights (after 10pm)'),
    ('EXAMS', 'Before and during exams'),
    ('WEEKENDS', 'Weekends'),
    ('ALL', 'All the time'),
]

LIFESTYLE_TEMPERATURE_RANGE_CHOICES = [
    ('VERY_COLD', 'Very Cold — Around 16–18°C'),
    ('COOL', 'Cool — Around 18–20°C'),
    ('MODERATE', 'Moderate — Around 20–23°C'),
    ('WARM', 'Warm — Around 23–25°C'),
    ('VERY_WARM', 'Very Warm — Above 25°C'),
]

LIFESTYLE_PRIVACY_MEANING_CHOICES = [
    ('ROUTINES', 'Privacy during personal routines (bathroom, dressing)'),
    ('QUIET_TIME', 'Quiet personal time alone in the room'),
    ('BELONGINGS', 'No one going through my belongings'),
    ('SEPARATE_SOCIAL', 'Separate social life from roommate'),
    ('LIMITED_INTERACTION', 'Limited interaction overall'),
]


@login_required
def initiate_booking(request, property_id):
    """
    Main booking initiation endpoint.
    """
    from properties.models import Room, RoomType
    from accounts.models import LifestyleProfile
    from bookings.services.matching.compatibility_service import CompatibilityService
    
    user = request.user
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Step 1: Validate prerequisites
    failed_prerequisite = PrerequisiteService.get_first_failed_prerequisite(user)
    if failed_prerequisite:
        if "active or pending booking" in failed_prerequisite.message:
            active_booking = Booking.objects.filter(
                tenant=user,
                accommodation_property_id=property_id,
                status__in=['INITIATED', 'TEMPORARILY_CANCELLED', 'WAITING_CONSENT', 'LIFESTYLE_PENDING', 'PAYMENT_REQUIRED', 'COMPATIBILITY_REVIEW']
            ).first()
            if active_booking:
                if active_booking.status in ['WAITING_CONSENT', 'TEMPORARILY_CANCELLED', 'COMPATIBILITY_REVIEW']:
                    return redirect('bookings:user-consent', booking_id=active_booking.id)
                elif active_booking.status == 'LIFESTYLE_PENDING':
                    return redirect('bookings:lifestyle_questionnaire', booking_id=active_booking.id, screen=1)
                elif active_booking.status == 'PAYMENT_REQUIRED':
                    return redirect('bookings:booking_confirmation', booking_id=active_booking.id)
                return redirect('bookings:booking_initiated', booking_id=active_booking.id)
            return render(request, 'bookings/active_booking_error.html', {'property': property_obj})
        if failed_prerequisite.redirect_url:
            request.session['intended_booking'] = {
                'property_id': property_id,
                'room_id': request.GET.get('room_id'),
            }
            messages.error(request, failed_prerequisite.message)
            return redirect(failed_prerequisite.redirect_url)
        else:
            messages.error(request, failed_prerequisite.message)
            return redirect('landing:property_detail', pk=property_id)
    
    room_id = request.GET.get('room_id')
    unit_type_id = request.GET.get('unit_type_id')
    room_type_id = request.GET.get('room_type_id')
    
    # Fallback if frontend mistakenly passed room_type.id as room_id
    if room_id and not room_type_id:
        if not Room.objects.filter(id=room_id).exists() and RoomType.objects.filter(id=room_id).exists():
            room_type_id = room_id
            room_id = None
            
    if room_type_id and not room_id:
        room_type = get_object_or_404(RoomType, id=room_type_id)
        # Select room with available_slots > 0
        available_rooms = [r for r in room_type.rooms.all() if r.available_slots > 0]
        room = available_rooms[0] if available_rooms else room_type.rooms.exclude(status__in=['ARCHIVED', 'MAINTENANCE']).first()
            
        # Auto-create room instance if RoomType has no room records yet
        if not room:
            room = Room.objects.create(
                accommodation_property=property_obj,
                room_type=room_type,
                room_number=f"Room 1",
                total_slots=room_type.total_capacity or 1,
                occupied_slots=0,
                pending_slots=0,
                status='AVAILABLE'
            )
        room_id = room.id
        
    room = get_object_or_404(Room, id=room_id) if room_id else None
    
    user_gender = user.gender
    if property_obj.property_type == 'HOSTEL' and property_obj.hostel_type:
        if property_obj.hostel_type == 'BOYS_ONLY' and user_gender != 'MALE':
            messages.error(request, "This hostel is for males only. You cannot book a room here.")
            return redirect('landing:property_detail', pk=property_id)
        elif property_obj.hostel_type == 'GIRLS_ONLY' and user_gender != 'FEMALE':
            messages.error(request, "This hostel is for females only. You cannot book a room here.")
            return redirect('landing:property_detail', pk=property_id)
            
    if room and room.room_type.gender_restriction:
        if room.room_type.gender_restriction == 'MALE_ONLY' and user_gender != 'MALE':
            messages.error(request, "This specific room is reserved for males only.")
            return redirect('landing:property_detail', pk=property_id)
        elif room.room_type.gender_restriction == 'FEMALE_ONLY' and user_gender != 'FEMALE':
            messages.error(request, "This specific room is reserved for females only.")
            return redirect('landing:property_detail', pk=property_id)

    # --- COMPATIBILITY CHECK FOR PARTIALLY OCCUPIED ROOMS ---
    if room and room.status in ['PARTIALLY_OCCUPIED', 'OCCUPIED'] and room.total_slots > 1:
        # User hasn't explicitly consented to low compatibility yet
        if not request.GET.get('force_proceed'):
            from accounts.models import LifestyleProfile
            from bookings.services.booking.compatibility_service import CompatibilityService as BookingCompatibilityService
            
            active_statuses = ['ACTIVE', 'CONFIRMED', 'CONFIRMED_ASSIGNED', 'ASSIGNED_AWAITING', 'PAYMENT_COMPLETE']
            occupants = [b.tenant for b in Booking.objects.filter(assigned_room=room, status__in=active_statuses).exclude(tenant=user)]
            
            # Simple fallback if no active booking found but status is partially occupied
            if not occupants:
                pass 
            else:
                user_profile = LifestyleProfile.objects.filter(user=user, is_complete=True).first()
                occupant_profiles = list(LifestyleProfile.objects.filter(user__in=occupants, is_complete=True))
                
                if user_profile and occupant_profiles:
                    room_comp = BookingCompatibilityService.calculate_room_compatibility(user_profile, occupant_profiles)
                    avg_score = room_comp.get('score', 0)
                    
                    if avg_score < 85:
                        # Find alternative partially occupied rooms if any exist
                        alt_rooms = Room.objects.filter(
                            accommodation_property=property_obj, 
                            status='PARTIALLY_OCCUPIED'
                        ).exclude(id=room.id)
                        
                        alternatives = []
                        for alt in alt_rooms:
                            alt_occupants = [b.tenant for b in Booking.objects.filter(assigned_room=alt, status__in=active_statuses).exclude(tenant=user)]
                            alt_profiles = list(LifestyleProfile.objects.filter(user__in=alt_occupants, is_complete=True))
                            if alt_profiles:
                                alt_comp = BookingCompatibilityService.calculate_room_compatibility(user_profile, alt_profiles)
                                alt_avg = alt_comp.get('score', 0)
                            else:
                                alt_avg = 100
                            alternatives.append({
                                'room': alt,
                                'score': int(alt_avg)
                            })
                        
                        alternatives.sort(key=lambda x: x['score'], reverse=True)
                        
                        return render(request, 'bookings/room_compatibility_warning.html', {
                            'property': property_obj,
                            'current_room': room,
                            'current_score': int(avg_score),
                            'alternatives': alternatives,
                        })

    just_acknowledged = request.session.pop('just_acknowledged_rules', False)
    if not just_acknowledged:
        return render(request, 'bookings/house_rules_acknowledgment.html', {
            'property': property_obj,
            'room_id': room_id,
            'unit_type_id': unit_type_id,
            'room_type_id': room_type_id,
            'room': room,
        })
    
    # Step 3: Execute atomic soft lock
    session_key = request.session.session_key
    house_rules_ack = HouseRulesAcknowledgment.objects.filter(
        user=user,
        property=property_obj,
        session_key=session_key
    ).order_by('-acknowledged_at').first()
    
    soft_lock_result = SoftLockService.execute_atomic_soft_lock(
        user=user,
        property_id=property_id,
        room_id=int(room_id) if room_id else None,
        unit_type_id=int(unit_type_id) if unit_type_id else None,
        house_rules_acknowledged_at=house_rules_ack.acknowledged_at if house_rules_ack else None
    )
    
    if not soft_lock_result.success:
        messages.error(request, soft_lock_result.message)
        return redirect('landing:property_detail', pk=property_id)
    
    booking = soft_lock_result.booking
    
    if booking.status in ['WAITING_CONSENT', 'TEMPORARILY_CANCELLED', 'COMPATIBILITY_REVIEW']:
        return redirect('bookings:user-consent', booking_id=booking.id)
    elif booking.status == 'LIFESTYLE_PENDING':
        return redirect('bookings:lifestyle_questionnaire', booking_id=booking.id, screen=1)
    elif booking.status == 'PAYMENT_REQUIRED':
        return redirect('bookings:booking_confirmation', booking_id=booking.id)
    
    # Step 4: Schedule Celery tasks (4h reminder and 6h expiry) safely
    try:
        from bookings.tasks import schedule_soft_lock_tasks
        schedule_soft_lock_tasks.delay(booking.id)
    except Exception as e:
        import logging
        logging.warning(f"Celery task scheduling bypassed for booking {booking.id}: {e}")
    
    # Step 5: Send notification
    Notification.objects.create(
        user=user,
        title='SLOT RESERVED',
        message=f"Your slot at {property_obj.title} is reserved.\nReference: {booking.reference_number}\nComplete your booking within 2 hours.",
    )
    
    # Step 6: Show booking initiated screen
    return render(request, 'bookings/booking_initiated.html', {
        'booking': booking,
        'property': property_obj,
        'time_remaining': SoftLockService.get_time_remaining(booking),
    })


@require_POST
@login_required
def acknowledge_house_rules(request):
    """
    Handle house rules acknowledgment submission.
    Creates acknowledgment record and redirects to booking initiation.
    """
    property_id = request.POST.get('property_id')
    room_id = request.POST.get('room_id')
    unit_type_id = request.POST.get('unit_type_id')
    room_type_id = request.POST.get('room_type_id')
    
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Create acknowledgment record
    HouseRulesAcknowledgment.objects.create(
        user=request.user,
        property=property_obj,
        session_key=request.session.session_key,
        ip_address=request.META.get('REMOTE_ADDR'),
    )
    
    # Set session flag so initiate_booking knows we just accepted
    request.session['just_acknowledged_rules'] = True
    
    # Redirect to booking initiation
    url = f"/api/bookings/initiate/{property_id}/"
    params = []
    if room_id: params.append(f"room_id={room_id}")
    if unit_type_id: params.append(f"unit_type_id={unit_type_id}")
    if room_type_id: params.append(f"room_type_id={room_type_id}")
    if params: url += "?" + "&".join(params)
        
    return redirect(url)


@login_required
def booking_initiated(request, booking_id):
    """
    Display the booking initiated screen.
    Shows:
    - Property and room type info
    - Reference number
    - Time remaining (48-hour countdown)
    - Steps to complete
    - Save and continue later option
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Check if booking is still in INITIATED status
    if booking.status != 'INITIATED':
        if booking.status == 'EXPIRED':
            messages.error(request, 'Your booking has expired. The slot has been released.')
            return redirect('landing:properties')
        else:
            # Booking has progressed, redirect to appropriate page
            return redirect('bookings:booking-detail', booking_id=booking_id)
    
    time_remaining = SoftLockService.get_time_remaining(booking)
    
    return render(request, 'bookings/booking_initiated.html', {
        'booking': booking,
        'property': booking.accommodation_property,
        'time_remaining': time_remaining,
    })


@login_required
def save_and_continue_later(request, booking_id):
    """
    Allow user to save their progress and continue later.
    Booking remains in INITIATED status.
    User can return from My Bookings to resume.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    if booking.status != 'INITIATED':
        messages.error(request, 'This booking cannot be saved at this stage.')
        return redirect('bookings:booking-detail', booking_id=booking_id)
    
    # Just redirect to my bookings - the booking is already saved
    messages.info(request, f'Booking {booking.reference_number} saved. You can continue later.')
    return redirect('bookings:my-bookings')


@login_required
def resume_booking(request, booking_id):
    """
    Resume a saved booking from My Bookings.
    Redirects to the appropriate step based on booking state.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Check if soft lock is still active
    if booking.is_soft_lock_expired():
        messages.error(request, 'Your booking has expired. Please book again.')
        return redirect('landing:properties')
    
    # Based on what information is filled, redirect to appropriate step
    # For now, redirect to booking initiated screen
    return redirect('bookings:booking_initiated', booking_id=booking_id)


# PART 3: DURATION SELECTION VIEWS

@login_required
def duration_selection(request, booking_id):
    """
    Step 1 of 3: Duration Selection
    Adapts to billing model (semester, monthly, annual, academic year)
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    # Auto-resolve room_type / unit_type if missing on booking object but present on room
    if not booking.room_type and booking.room and booking.room.room_type:
        booking.room_type = booking.room.room_type
        booking.save(update_fields=['room_type'])
    if not booking.unit_type and booking.room and hasattr(booking.room, 'unit_type') and booking.room.unit_type:
        booking.unit_type = booking.room.unit_type
        booking.save(update_fields=['unit_type'])

    # Get billing model
    billing_model = DurationService.get_billing_model(
        room_type_id=booking.room_type.id if booking.room_type else None,
        unit_type_id=booking.unit_type.id if booking.unit_type else None
    )
    
    if not billing_model:
        messages.error(request, 'Could not determine billing model.')
        return redirect('bookings:booking_initiated', booking_id=booking_id)
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'billing_model': billing_model,
        'room_type': booking.room_type,
        'unit_type': booking.unit_type,
    }
    
    template_map = {
        'SEMESTER': 'bookings/duration/semester_selection.html',
        'MONTHLY': 'bookings/duration/monthly_selection.html',
        'ANNUAL': 'bookings/duration/annual_selection.html',
        'ACADEMIC_YEAR': 'bookings/duration/academic_year_selection.html',
    }
    
    template = template_map.get(billing_model['type'], 'bookings/duration/semester_selection.html')
    
    return render(request, template, context)


@require_POST
@login_required
def submit_duration(request, booking_id):
    """
    Process duration selection submission
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    if not booking.room_type and booking.room and booking.room.room_type:
        booking.room_type = booking.room.room_type
        booking.save(update_fields=['room_type'])
    if not booking.unit_type and booking.room and hasattr(booking.room, 'unit_type') and booking.room.unit_type:
        booking.unit_type = booking.room.unit_type
        booking.save(update_fields=['unit_type'])

    billing_model = DurationService.get_billing_model(
        room_type_id=booking.room_type.id if booking.room_type else None,
        unit_type_id=booking.unit_type.id if booking.unit_type else None
    )
    
    # Get form data
    move_in_date_str = request.POST.get('move_in_date')
    duration_value = int(request.POST.get('duration_value', 1))
    structure = request.POST.get('structure', 'CONTINUOUS')
    semester2_start_str = request.POST.get('semester2_start_date')
    
    try:
        move_in_date = datetime.strptime(move_in_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, 'Invalid move-in date.')
        return redirect('bookings:duration_selection', booking_id=booking_id)
    
    semester2_start_date = None
    if semester2_start_str:
        try:
            semester2_start_date = datetime.strptime(semester2_start_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    
    # Calculate duration
    result = DurationService.calculate_duration(
        billing_model=billing_model['type'],
        move_in_date=move_in_date,
        duration_value=duration_value,
        pricing_data=billing_model,
        structure=structure,
        semester2_start_date=semester2_start_date
    )
    
    if not result.success:
        messages.error(request, result.message)
        return redirect('bookings:duration_selection', booking_id=booking_id)
    
    # Update booking with calculated data
    booking.move_in_date = result.data['move_in_date']
    # move_out_date is now always set by the service; fallbacks kept for safety
    booking.move_out_date = (
        result.data.get('move_out_date')
        or result.data.get('semester2_end_date')
        or result.data.get('semester_end_date')
    )
    booking.monthly_rent = (
        result.data.get('price_per_month')
        or result.data.get('price_per_semester')
        or result.data.get('price_per_year')
    )
    booking.price_per_unit = booking.monthly_rent
    booking.total_amount = result.data['total_price']
    booking.total_price = result.data['total_price']
    booking.duration_days = result.data.get('total_days')
    booking.months_selected = result.data.get('num_months')
    booking.years_selected = result.data.get('num_years')
    booking.semesters_selected = result.data.get('num_semesters')
    booking.rental_period = billing_model['type'].lower() if billing_model else None
    # Derive duration_months for legacy display consistency
    num_months = result.data.get('num_months')
    total_days = result.data.get('total_days')
    if num_months:
        booking.duration_months = num_months
    elif total_days:
        booking.duration_months = max(1, round(total_days / 30))
    # Save semester 2 dates if available (split or academic year)
    s2_start = result.data.get('semester2_start_date')
    s2_end = result.data.get('semester2_end_date')
    if s2_start:
        booking.semester_2_start_date = s2_start if not isinstance(s2_start, str) else __import__('datetime').date.fromisoformat(s2_start)
    if s2_end:
        booking.semester_2_end_date = s2_end if not isinstance(s2_end, str) else __import__('datetime').date.fromisoformat(s2_end)
    
    # Convert dates to strings and decimals to floats for JSON serialization in session
    serializable_data = {}
    for k, v in result.data.items():
        if isinstance(v, (datetime, date)):
            serializable_data[k] = v.isoformat()
        elif isinstance(v, Decimal):
            serializable_data[k] = float(v)
        else:
            serializable_data[k] = v
            
    request.session['duration_data'] = serializable_data
    
    booking.save(update_fields=[
        'move_in_date', 'move_out_date', 'monthly_rent', 'price_per_unit', 'total_amount',
        'total_price', 'duration_days', 'months_selected', 'years_selected', 'semesters_selected',
        'duration_months', 'rental_period', 'semester_2_start_date', 'semester_2_end_date',
    ])
    
    # If semester billing or academic year → show structure selection (Continuous vs Split/Vacation)
    if billing_model and billing_model.get('type') in ['SEMESTER', 'ACADEMIC_YEAR']:
        return redirect('bookings:semester_structure_selection', booking_id=booking_id)

    # Otherwise, show duration summary
    return redirect('bookings:duration_summary', booking_id=booking_id)


@login_required
def semester_structure_selection(request, booking_id):
    """
    Semester structure selection for 2+ semesters
    Continuous vs Split with vacation gap
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    duration_data = request.session.get('duration_data', {})
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'duration_data': duration_data,
    }
    
    return render(request, 'bookings/duration/semester_structure_selection.html', context)


@require_POST
@login_required
def submit_semester_structure(request, booking_id):
    """
    Process semester structure selection
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    structure = request.POST.get('structure', 'CONTINUOUS')
    
    if structure == 'SPLIT':
        # Redirect to vacation date declaration
        return redirect('bookings:vacation_date_declaration', booking_id=booking_id)
    else:
        # Continuous stay - proceed to summary
        duration_data = request.session.get('duration_data', {})
        duration_data['structure'] = 'CONTINUOUS'
        request.session['duration_data'] = duration_data
        return redirect('bookings:duration_summary', booking_id=booking_id)


@login_required
def vacation_date_declaration(request, booking_id):
    """
    Vacation date declaration for split stays
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    duration_data = request.session.get('duration_data', {})
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'duration_data': duration_data,
    }
    
    return render(request, 'bookings/duration/vacation_date_declaration.html', context)


@require_POST
@login_required
def submit_vacation_date(request, booking_id):
    """
    Process vacation date declaration
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    semester2_start_str = request.POST.get('semester2_start_date')
    
    try:
        semester2_start_date = datetime.strptime(semester2_start_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, 'Invalid Semester 2 start date.')
        return redirect('bookings:vacation_date_declaration', booking_id=booking_id)
    
    # Recalculate with split structure
    billing_model = DurationService.get_billing_model(
        room_type_id=booking.room_type.id if booking.room_type else None,
        unit_type_id=booking.unit_type.id if booking.unit_type else None
    )
    
    result = DurationService.calculate_duration(
        billing_model=billing_model['type'],
        move_in_date=booking.move_in_date,
        duration_value=2,
        pricing_data=billing_model,
        structure='SPLIT',
        semester2_start_date=semester2_start_date
    )
    
    if result.success:
        serializable_data = {}
        for k, v in result.data.items():
            if isinstance(v, (datetime, date)):
                serializable_data[k] = v.isoformat()
            elif isinstance(v, Decimal):
                serializable_data[k] = float(v)
            else:
                serializable_data[k] = v
        request.session['duration_data'] = serializable_data
    
    return redirect('bookings:duration_summary', booking_id=booking_id)


@login_required
def duration_summary(request, booking_id):
    """
    Duration summary screen showing all calculated dates and pricing
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    duration_data = request.session.get('duration_data', {})
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'duration_data': duration_data,
    }
    
    return render(request, 'bookings/duration/duration_summary.html', context)


@require_POST
@login_required
def confirm_duration(request, booking_id):
    """
    Confirm duration and proceed to lifestyle preferences or booking confirmation
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    # Save duration data from session to booking model
    duration_data = request.session.get('duration_data', {})
    if duration_data:
        from datetime import datetime
        
        def parse_date(d):
            if not d: return None
            if isinstance(d, str):
                return datetime.strptime(d, '%Y-%m-%d').date()
            return d

        booking.move_in_date = parse_date(duration_data.get('move_in_date')) or booking.move_in_date
        booking.move_out_date = parse_date(duration_data.get('move_out_date')) or booking.move_out_date
        booking.grace_period_start = parse_date(duration_data.get('grace_period_start')) or booking.grace_period_start
        booking.grace_period_end = parse_date(duration_data.get('grace_period_end')) or booking.grace_period_end
        
        booking.duration_days = duration_data.get('total_days') or booking.duration_days
        booking.semesters_selected = duration_data.get('num_semesters') or booking.semesters_selected
        booking.months_selected = duration_data.get('num_months') or booking.months_selected
        booking.years_selected = duration_data.get('num_years') or booking.years_selected
        # Also update duration_months for legacy display
        num_months = duration_data.get('num_months')
        total_days = duration_data.get('total_days')
        if num_months:
            booking.duration_months = num_months
        elif total_days:
            booking.duration_months = max(1, round(total_days / 30))
        
        billing_model = duration_data.get('billing_model', '')
        booking.rental_period = billing_model.lower() if billing_model else None
        
        if billing_model == 'SEMESTER':
            booking.price_per_unit = duration_data.get('price_per_semester') or booking.price_per_unit
        elif billing_model == 'MONTHLY':
            booking.price_per_unit = duration_data.get('price_per_month') or booking.price_per_unit
        elif billing_model == 'ANNUAL':
            booking.price_per_unit = duration_data.get('price_per_year') or booking.price_per_unit
        elif billing_model == 'ACADEMIC_YEAR':
            booking.price_per_unit = duration_data.get('total_price') or booking.price_per_unit
            
        booking.total_price = duration_data.get('total_price') or booking.total_price
        booking.total_amount = duration_data.get('total_price') or booking.total_amount
        booking.monthly_rent = booking.price_per_unit or booking.monthly_rent
        
        booking.stay_structure = duration_data.get('structure') or booking.stay_structure
        # Handle both key formats (semester2_start_date from service, semester_2_start_date from older code)
        s2_start = parse_date(duration_data.get('semester2_start_date') or duration_data.get('semester_2_start_date'))
        s2_end = parse_date(duration_data.get('semester2_end_date') or duration_data.get('semester_2_end_date'))
        booking.semester_2_start_date = s2_start or booking.semester_2_start_date
        booking.semester_2_end_date = s2_end or booking.semester_2_end_date
        
        booking.vacation_reserve_start = parse_date(duration_data.get('vacation_start_date') or duration_data.get('vacation_reserve_start')) or booking.vacation_reserve_start
        booking.vacation_reserve_end = parse_date(duration_data.get('vacation_end_date') or duration_data.get('vacation_reserve_end')) or booking.vacation_reserve_end
        
        booking.save(update_fields=[
            'move_in_date', 'move_out_date', 'grace_period_start', 'grace_period_end',
            'duration_days', 'semesters_selected', 'months_selected', 'years_selected',
            'duration_months', 'rental_period', 'price_per_unit', 'total_price', 'total_amount',
            'monthly_rent', 'stay_structure', 'semester_2_start_date', 'semester_2_end_date',
            'vacation_reserve_start', 'vacation_reserve_end'
        ])
    
    # Always proceed to Step 3: Lifestyle Preferences
    return redirect('bookings:lifestyle_check', booking_id=booking_id)


# PART 4: LIFESTYLE PREFERENCES VIEWS

@login_required
def lifestyle_check(request, booking_id):
    """
    Check if user has existing lifestyle profile
    Show options to use existing or update
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    # Check for existing lifestyle profile
    existing_profile = LifestyleProfile.objects.filter(user=request.user, is_complete=True).first()
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'existing_profile': existing_profile,
    }
    return render(request, 'bookings/lifestyle/lifestyle_check.html', context)


@login_required
def use_existing_lifestyle(request, booking_id):
    """
    Use existing lifestyle profile for this booking
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    existing_profile = LifestyleProfile.objects.filter(user=request.user, is_complete=True).first()
    if not existing_profile:
        messages.error(request, 'No completed profile found. Please fill out your preferences.')
        return redirect('bookings:lifestyle_check', booking_id=booking_id)
    
    # Proceed to routing engine (which will check if they are the first occupant or need matching)
    return redirect('bookings:booking_route', booking_id=booking_id)


@login_required
def lifestyle_questionnaire(request, booking_id=None, screen=1):
    """
    Lifestyle questionnaire - 4 screens
    Screen 1: Sleep and Daily Routine
    Screen 2: Cleanliness, Noise and Visitors
    Screen 3: Study Habits, Food and Environment
    Screen 4: Boundaries, Conflict and Final Review
    """
    booking = None
    if booking_id:
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    if screen < 1 or screen > 4:
        if booking_id:
            return redirect('bookings:lifestyle_questionnaire', booking_id=booking_id, screen=1)
        return redirect('accounts:lifestyle_questionnaire_standalone', screen=1)
    
    template_map = {
        1: 'bookings/lifestyle/screen1_sleep.html',
        2: 'bookings/lifestyle/screen2_cleanliness.html',
        3: 'bookings/lifestyle/screen3_study.html',
        4: 'bookings/lifestyle/screen4_boundaries.html',
    }
    
    profile = LifestyleProfile.objects.filter(user=request.user).first()
    
    # Merge session answers so the user sees their current draft when clicking Back
    class MockProfile:
        def __getattr__(self, name):
            return None
        
    merged_profile = MockProfile()
    
    # First, load existing db profile attributes if any
    if profile:
        for field in profile._meta.fields:
            setattr(merged_profile, field.name, getattr(profile, field.name))
    
    # Then overwrite with any session answers
    session_answers = request.session.get('lifestyle_answers', {})
    for key, value in session_answers.items():
        setattr(merged_profile, key, value)
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property if booking else None,
        'profile': merged_profile,
        'screen': screen,
        'total_screens': 4,
        'sleep_time_choices': LifestyleProfile.SLEEP_TIME_CHOICES,
        'wake_time_choices': LifestyleProfile.WAKE_TIME_CHOICES,
        'alarm_choices': LifestyleProfile.ALARM_CHOICES,
        'night_activity_choices': LifestyleProfile.NIGHT_ACTIVITY_CHOICES,
        'cleaning_frequency_choices': LifestyleProfile.CLEANING_FREQUENCY_CHOICES,
        'noise_tolerance_choices': LifestyleProfile.NOISE_TOLERANCE_CHOICES,
        'preferred_noise_level_choices': LifestyleProfile.PREFERRED_NOISE_CHOICES,
        'visitor_frequency_choices': LifestyleProfile.VISITOR_FREQUENCY_CHOICES,
        'overnight_guest_choices': LifestyleProfile.OVERNIGHT_GUEST_CHOICES,
        'visitor_notice_choices': LifestyleProfile.VISITOR_NOTICE_CHOICES,
        'study_location_choices': LifestyleProfile.STUDY_LOCATION_CHOICES,
        'study_time_choices': LifestyleProfile.STUDY_TIME_CHOICES,
        'quiet_hours_still_needed_choices': LIFESTYLE_QUIET_HOURS_STILL_NEEDED_CHOICES,
        'quiet_times_choices': LIFESTYLE_QUIET_TIMES_CHOICES,
        'cooking_frequency_choices': LifestyleProfile.COOKING_FREQUENCY_CHOICES,
        'shared_kitchen_comfort_choices': LifestyleProfile.SHARED_KITCHEN_COMFORT_CHOICES,
        'food_sharing_choices': LifestyleProfile.FOOD_SHARING_CHOICES,
        'temperature_range_choices': LIFESTYLE_TEMPERATURE_RANGE_CHOICES,
        'air_con_choices': LifestyleProfile.AIR_CON_CHOICES,
        'shared_items_comfort_choices': LifestyleProfile.SHARED_ITEMS_CHOICES,
        'personal_space_importance_choices': LifestyleProfile.PERSONAL_SPACE_CHOICES,
        'privacy_meaning_choices': LIFESTYLE_PRIVACY_MEANING_CHOICES,
        'conflict_resolution_choices': LifestyleProfile.CONFLICT_RESOLUTION_CHOICES,
        'smoking_tolerance_choices': LifestyleProfile.SMOKING_TOLERANCE_CHOICES,
        'alcohol_tolerance_choices': LifestyleProfile.ALCOHOL_TOLERANCE_CHOICES,
    }
    
    return render(request, template_map[screen], context)


@require_POST
@login_required
def submit_lifestyle_screen(request, booking_id=None, screen=1):
    """
    Submit a lifestyle questionnaire screen.
    Saves answers to session and advances to next screen.
    Multi-select checkbox fields are stored as comma-joined strings.
    """
    booking = None
    if booking_id:
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)

    if 'lifestyle_answers' not in request.session:
        request.session['lifestyle_answers'] = {}

    # Multi-select checkbox field names (use getlist to get all checked values)
    MULTI_SELECT_FIELDS = {'quiet_times', 'privacy_meaning', 'dietary_restrictions'}

    answers = dict(request.session['lifestyle_answers'])  # copy to avoid mutating directly

    for key, value in request.POST.items():
        if key != 'csrfmiddlewaretoken' and key not in MULTI_SELECT_FIELDS:
            answers[key] = value

    # Handle multi-select checkboxes
    for field in MULTI_SELECT_FIELDS:
        values = request.POST.getlist(field)
        if values:
            answers[field] = values

    request.session['lifestyle_answers'] = answers
    request.session.modified = True

    if screen < 4:
        if booking_id:
            return redirect('bookings:lifestyle_questionnaire', booking_id=booking_id, screen=screen + 1)
        return redirect('accounts:lifestyle_questionnaire_standalone', screen=screen + 1)
    else:
        if booking_id:
            return redirect('bookings:lifestyle_submit', booking_id=booking_id)
        return redirect('accounts:lifestyle_submit_final_standalone')


@login_required
def lifestyle_submit(request, booking_id=None):
    """
    Process final lifestyle submission.
    Maps all questionnaire answers (q1–q17+) from session into LifestyleProfile fields.
    Creates profile if none exists, otherwise updates the existing one in-place.
    No duplicate profile is created (spec §4.2).
    """
    booking = None
    if booking_id:
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)

    answers = request.session.get('lifestyle_answers', {})

    # ── Build field update dict from questionnaire answers ───────────────────
    profile_data = {}
    from accounts.models import LifestyleProfile
    valid_fields = [f.name for f in LifestyleProfile._meta.get_fields()]
    
    for key, value in answers.items():
        if key in valid_fields:
            if key in ['personal_cleanliness_level', 'preferred_temperature']:
                try:
                    profile_data[key] = int(value)
                except (ValueError, TypeError):
                    pass
            else:
                profile_data[key] = value

    # Mark as complete
    profile_data['is_complete'] = True

    # ── Create or update profile (no duplicate created) ──────────────────────
    existing_profile = LifestyleProfile.objects.filter(user=request.user).first()
    if existing_profile:
        for field, value in profile_data.items():
            setattr(existing_profile, field, value)
        existing_profile.save()
    else:
        LifestyleProfile.objects.create(user=request.user, **profile_data)

    # Clear session answers
    request.session.pop('lifestyle_answers', None)
    request.session.pop('lifestyle_answers_multi', None)

    # Proceed to routing engine or dashboard
    if booking_id:
        return redirect('bookings:booking_route', booking_id=booking_id)
    else:
        from django.contrib import messages
        messages.success(request, 'Your lifestyle profile has been saved successfully!')
        return redirect('accounts:profile')


# PART 5: ROUTING ENGINE

@login_required
def booking_route(request, booking_id):
    """
    Routing Engine - Determines path based on occupancy and booking context
    Route A: Single occupancy → Admin review
    Route B: First occupant of shared room → Admin review
    Route C: Shared occupancy → Compatibility engine
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Determine occupancy type
    occupancy_type = 'SINGLE'
    if booking.room_type:
        occupancy_type = booking.room_type.occupancy_type
    elif booking.unit_type:
        if booking.unit_type.shared_apartment_allowed or booking.unit_type.roommate_matching_enabled:
            occupancy_type = 'SHARED'
    
    # Route A: Single occupancy
    if occupancy_type == 'SINGLE':
        # Single occupancy - skip all matching, go to payment first
        booking.status = 'PAYMENT_REQUIRED'
        booking.soft_lock_expires_at = None
        booking.save()
        
        # Create booking history
        from bookings.models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            action='ROUTED_TO_PAYMENT',
            description='Single occupancy booking routed to payment before admin review.',
            performed_by=request.user
        )
        
        # Send notification
        Notification.objects.create(
            user=request.user,
            title='Booking Ready for Payment',
            message=f'Your booking {booking.reference_number} is ready. Please complete payment to proceed.',
            notification_type='BOOKING_UPDATE'
        )
        
        return redirect('bookings:booking_confirmation', booking_id=booking_id)
    
    # Route B/C: Shared room - check if first occupant
    # Count ALL existing bookings that hold a slot: anything beyond INITIATED with an active soft lock
    # This MUST include PAYMENT_REQUIRED and PAYMENT_COMPLETE — these are genuine occupants who
    # simply haven't physically moved in yet. Missing them causes the 2nd booker to be treated
    # as the first occupant, bypassing roommate matching entirely.
    existing_statuses = [
        'PAYMENT_REQUIRED', 'PAYMENT_PROCESSING', 'PAYMENT_PENDING_VERIFICATION',
        'PAYMENT_COMPLETE', 'UNDER_REVIEW', 'ASSIGNED_AWAITING', 'LIFESTYLE_PENDING',
        'LIFESTYLE_COMPLETE', 'AWAITING_COMPATIBILITY', 'AUTO_ASSIGNED',
        'CONSENT_PENDING', 'CONSENT_ACCEPTED', 'ADMIN_PENDING',
        'CONFIRMED', 'CONFIRMED_ASSIGNED', 'ACTIVE', 'REINSTATED'
    ]
    existing_active = Booking.objects.filter(
        room_type=booking.room_type,
        accommodation_property=booking.accommodation_property,
        status__in=existing_statuses
    ).exclude(id=booking.id)

    # Also count INITIATED bookings that still have an active soft lock (slot held)
    soft_locked_count = 0
    for eb in Booking.objects.filter(
        room_type=booking.room_type,
        accommodation_property=booking.accommodation_property,
        status='INITIATED'
    ).exclude(id=booking.id):
        if eb.is_soft_lock_active():
            soft_locked_count += 1

    existing_bookings_count = existing_active.count() + soft_locked_count

    if existing_bookings_count == 0:
        # Route B: First occupant - no matching needed, go to payment first
        booking.status = 'PAYMENT_REQUIRED'
        booking.is_first_occupant = True
        booking.occupancy_position = 1
        booking.soft_lock_expires_at = None
        booking.save()
        
        # Create booking history
        from bookings.models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            action='ROUTED_TO_PAYMENT',
            description='First occupant of shared room. No matching needed. Routed to payment before admin review.',
            performed_by=request.user
        )
        
        # Send notification
        Notification.objects.create(
            user=request.user,
            title='Booking Ready for Payment',
            message=f'Your booking {booking.reference_number} is ready. You are the first occupant. Please complete payment.',
            notification_type='BOOKING_UPDATE'
        )
        
        return redirect('bookings:booking_confirmation', booking_id=booking_id)
    else:
        # Route C: Shared occupancy - activate compatibility engine
        return redirect('bookings:compatibility_engine', booking_id=booking_id)


@login_required
def compatibility_engine(request, booking_id):
    """
    Compatibility Engine - Activates for shared occupancy when not first occupant
    Calculates room-level compatibility scores and finds best match
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Get user's lifestyle profile
    from accounts.models import LifestyleProfile
    user_profile = LifestyleProfile.objects.filter(user=request.user).first()
    
    if not user_profile:
        messages.error(request, 'Lifestyle profile not found. Please complete the questionnaire.')
        return redirect('bookings:lifestyle_check', booking_id=booking_id)
    
    # Find existing occupants in the same room type/property — include ALL statuses that hold a slot
    _active_statuses = [
        'PAYMENT_REQUIRED', 'PAYMENT_PROCESSING', 'PAYMENT_PENDING_VERIFICATION',
        'PAYMENT_COMPLETE', 'UNDER_REVIEW', 'ASSIGNED_AWAITING', 'LIFESTYLE_PENDING',
        'LIFESTYLE_COMPLETE', 'AWAITING_COMPATIBILITY', 'AUTO_ASSIGNED',
        'CONSENT_PENDING', 'CONSENT_ACCEPTED', 'ADMIN_PENDING',
        'CONFIRMED', 'CONFIRMED_ASSIGNED', 'ACTIVE', 'REINSTATED'
    ]
    existing_bookings = Booking.objects.filter(
        room_type=booking.room_type,
        accommodation_property=booking.accommodation_property,
        status__in=_active_statuses
    ).exclude(id=booking.id)
    
    # Group bookings by assigned_room (using None for those not yet assigned a physical room)
    room_groups = {}
    for eb in existing_bookings:
        room_id = eb.assigned_room_id
        if room_id not in room_groups:
            room_groups[room_id] = []
        room_groups[room_id].append(eb)
    
    from bookings.services.booking.compatibility_service import CompatibilityService
    
    occupancy_limit = booking.room_type.beds_per_room if booking.room_type else 2
    
    best_room_score = -1
    best_room_result = None
    best_room_id = None
    best_room_bookings = []
    
    for room_id, bookings_in_room in room_groups.items():
        if len(bookings_in_room) >= occupancy_limit:
            continue
            
        existing_profiles = []
        for b in bookings_in_room:
            p = LifestyleProfile.objects.filter(user=b.tenant).first()
            if p:
                existing_profiles.append(p)
                
        if existing_profiles:
            result = CompatibilityService.calculate_room_compatibility(user_profile, existing_profiles)
            if result['score'] > best_room_score:
                best_room_score = result['score']
                best_room_result = result
                best_room_id = room_id
                best_room_bookings = bookings_in_room
    
    if best_room_result:
        # Save the result
        booking.compatibility_result = best_room_result
        booking.compatibility_score = best_room_score
        if best_room_id:
            booking.assigned_room_id = best_room_id
            
        # Determine position
        max_pos = max([b.occupancy_position for b in best_room_bookings if b.occupancy_position] + [0])
        booking.occupancy_position = max_pos + 1
        booking.is_first_occupant = False
        booking.soft_lock_expires_at = None
        
        if best_room_score >= CompatibilityService.ROUTING_THRESHOLD:
            # AUTO-ASSIGN
            booking.status = 'UNDER_REVIEW'
            booking.save()
            
            # Lock the profile
            user_profile.is_locked = True
            user_profile.locked_until = timezone.now() + timezone.timedelta(days=180) # rough estimate for stay
            user_profile.save()
            
            # Send Notification to user
            from accounts.models import Notification
            Notification.objects.create(
                user=request.user,
                title='Roommate Matched!',
                message=f'Great news! You have been auto-assigned to a room with highly compatible roommates ({best_room_score}% match).',
                notification_type='SUCCESS'
            )
            
            messages.success(request, f'Great news! You have been auto-assigned with a {best_room_score}% compatibility match!')
            # Set status to payment required before confirmation
            booking.status = 'PAYMENT_REQUIRED'
            booking.save()
            return redirect('bookings:booking_confirmation', booking_id=booking.id)
        else:
            # CONSENT REQUIRED
            booking.status = 'ASSIGNED_AWAITING'
            booking.consent_deadline = timezone.now() + timezone.timedelta(hours=2)
            booking.consent_status = 'pending'
            booking.save()
            
            # Send Notification
            from accounts.models import Notification
            Notification.objects.create(
                user=request.user,
                title='Roommate Match Found',
                message='A potential roommate has been found. Please review the compatibility and accept within 2 hours.',
                notification_type='WARNING'
            )
            
            return redirect('bookings:user-consent', booking_id=booking.id)
    else:
        # No available rooms found with profiles to match against, fallback to under review
        booking.status = 'UNDER_REVIEW'
        booking.is_first_occupant = True
        booking.occupancy_position = 1
        booking.status = 'PAYMENT_REQUIRED'
        booking.save()
        return redirect('bookings:booking_confirmation', booking_id=booking.id)


@require_POST
@login_required
def accept_match(request, booking_id, match_booking_id):
    """
    User accepts a roommate match
    Proceeds to consent process
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    from django.http import HttpResponseForbidden
    
    if booking.status not in ['INITIATED', 'ASSIGNED_AWAITING']:
        return HttpResponseForbidden("Booking is not in a state to accept a match.")
        
    if booking.status == 'INITIATED':
        match_booking = get_object_or_404(Booking, id=match_booking_id)
        
        # Update booking status
        booking.status = 'ASSIGNED_AWAITING'
        booking.occupancy_position = match_booking.occupancy_position + 1
        booking.is_first_occupant = False
        booking.soft_lock_expires_at = None
        booking.assigned_room = match_booking.assigned_room
        
        # Calculate compatibility and save
        from accounts.models import LifestyleProfile
        from bookings.services.booking.compatibility_service import CompatibilityService
        
        user_profile = LifestyleProfile.objects.filter(user=request.user).first()
        match_profile = LifestyleProfile.objects.filter(user=match_booking.tenant).first()
        
        if user_profile and match_profile:
            comp_result = CompatibilityService.calculate_compatibility(user_profile, match_profile)
            booking.compatibility_result = comp_result
            if isinstance(comp_result, dict):
                booking.compatibility_score = comp_result.get('score', 0)
            else:
                booking.compatibility_score = comp_result
        
        from django.utils import timezone
        booking.consent_deadline = timezone.now() + timezone.timedelta(hours=24)
        booking.save()
        
        # Create booking history
        from bookings.models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            action='MATCH_ACCEPTED',
            description=f'User accepted match with {match_booking.tenant.email}. Awaiting consent.',
            performed_by=request.user
        )
    
    # Redirect to consent process
    return redirect('bookings:user-consent', booking_id=booking_id)


@login_required
def booking_confirmation(request, booking_id):
    """
    Booking confirmation screen
    Shows final booking details and next steps
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
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
    
    from payments.models import PaymentRecord
    has_paid = PaymentRecord.objects.filter(
        booking=booking, 
        payment_status__in=['completed', 'verified', 'SUCCESS', 'PAID', 'COMPLETED']
    ).exists()
    
    context = {
        'booking': booking,
        'property': accommodation_property,
        'room': room,
        'room_type': room_type,
        'unit_type': unit_type,
        'amenities': accommodation_property.amenities.all() if accommodation_property else [],
        'property_images': accommodation_property.images.all()[:6] if accommodation_property else [],
        'gallery_images': gallery_images,
        'lifestyle_profile': lifestyle_profile,
        'has_paid': has_paid,
        'time_remaining': SoftLockService.get_time_remaining(booking),
        'soft_lock_expires_at': booking.soft_lock_expires_at.isoformat() if booking.soft_lock_expires_at else None,
    }
    
    return render(request, 'bookings/booking_confirmation.html', context)


@require_POST
@login_required
def submit_booking(request, booking_id):
    """
    Final submission of the booking.
    Creates payment record and redirects to payment screen.
    User must complete payment before seeing booking confirmation.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Create payment record
    from payments.services import PaymentService
    from payments.models import PaymentRecord
    from decimal import Decimal
    
    payment_service = PaymentService()
    
    # Calculate amounts
    accommodation_amount = booking.total_amount or booking.total_price or Decimal('0.00')
    platform_fee = accommodation_amount * Decimal(str(payment_service.platform_fee_percentage))
    total_charged = accommodation_amount + platform_fee
    
    # Create payment record
    payment = PaymentRecord.objects.create(
        booking=booking,
        user=request.user,
        amount_accommodation=accommodation_amount,
        amount_platform_fee=platform_fee,
        amount_total=total_charged,
        payment_status='initiated',
        payment_window_opens_at=timezone.now(),
        payment_window_closes_at=timezone.now() + timezone.timedelta(hours=payment_service.payment_window_hours)
    )
    
    # Update booking status to require payment
    booking.status = 'PAYMENT_REQUIRED'
    booking.save()
    
    # Create booking history
    BookingHistory.objects.create(
        booking=booking,
        action='PAYMENT_REQUIRED',
        description='Payment record created. User must complete payment before admin review.',
        performed_by=request.user
    )
    
    # Redirect to payment screen
    return redirect('payments:payment_screen', payment_id=payment.id)


@login_required
def download_receipt(request, booking_id):
    """Return a downloadable receipt for the booking as an attachment (HTML)."""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from io import BytesIO

    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)

    context = {
        'booking': booking,
        'property': booking.accommodation_property,
    }

    # If PDF requested, try to generate using xhtml2pdf (fallback to HTML)
    fmt = request.GET.get('format', '').lower()
    html_string = render_to_string('bookings/receipt.html', context)
    filename = f"receipt-{booking.reference_number or booking.id}"

    if fmt == 'pdf':
        try:
            from xhtml2pdf import pisa
            result = BytesIO()
            pisa_status = pisa.CreatePDF(html_string, dest=result)
            if pisa_status.err:
                raise Exception('PDF generation failed')
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response
        except Exception:
            # Fall back to HTML if PDF libs not available or generation failed
            pass

    response = HttpResponse(html_string, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.html"'
    return response


@require_POST
@login_required
def save_lifestyle_progress(request, booking_id):
    """
    AJAX endpoint to save lifestyle questionnaire progress
    Stores partial answers in session and optionally in database
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    # Get answers from POST data
    answers = {}
    for key, value in request.POST.items():
        if key.startswith('q') and value:
            answers[key] = value
    
    # Store in session
    if 'lifestyle_answers' not in request.session:
        request.session['lifestyle_answers'] = {}
    request.session['lifestyle_answers'].update(answers)
    request.session.modified = True
    
    # Optional: Store in database as JSON for persistence
    # This allows resuming even if session expires
    booking.lifestyle_progress = answers
    booking.save()
    
    return JsonResponse({'success': True, 'message': 'Progress saved'})


@login_required
def load_lifestyle_progress(request, booking_id):
    """
    AJAX endpoint to load saved lifestyle questionnaire progress
    Returns previously saved answers
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='INITIATED')
    
    # Try session first, then database
    answers = request.session.get('lifestyle_answers', {})
    if not answers and booking.lifestyle_progress:
        answers = booking.lifestyle_progress
    
    return JsonResponse({'success': True, 'answers': answers})


# Part 7: Consent Workflow Views

@login_required
def compatibility_result(request, booking_id):
    """
    Display compatibility result after lifestyle questionnaire submission.
    Shows either auto-assign confirmation or consent-required screen based on score.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Get compatibility result from booking or calculate it
    if booking.compatibility_result:
        result = booking.compatibility_result
    else:
        # Calculate compatibility if not stored
        from bookings.services.booking.compatibility_service import CompatibilityService
        from accounts.models import LifestyleProfile
        
        try:
            profile = LifestyleProfile.objects.get(user=request.user)
            result = CompatibilityService.calculate_compatibility(profile, booking)
            booking.compatibility_result = result
            booking.save()
        except LifestyleProfile.DoesNotExist:
            messages.error(request, 'Lifestyle profile not found. Please complete the questionnaire.')
            return redirect('bookings:lifestyle_questionnaire', booking_id=booking.id, screen=1)
    
    # Set consent deadline if consent is required
    if not result.get('auto_assign', False) and not booking.consent_deadline:
        booking.consent_deadline = timezone.now() + timezone.timedelta(hours=24)
        booking.status = 'PENDING_CONSENT'
        booking.save()
        
        # Schedule consent tasks
        from bookings.tasks import schedule_consent_tasks
        schedule_consent_tasks(booking.id, deadline_hours=24)
    
    # Determine template based on auto_assign flag
    if result.get('auto_assign', False):
        template = 'bookings/compatibility_auto_assign.html'
    else:
        template = 'bookings/compatibility_consent_required.html'
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'result': result,
    }
    
    return render(request, template, context)


@require_POST
@login_required
def accept_consent(request, booking_id):
    """
    Handle user accepting the compatibility result.
    Sets consent_given_at and proceeds to checkout.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Set consent timestamp
    booking.consent_given_at = timezone.now()
    booking.status = 'CONFIRMED'
    booking.soft_lock_expires_at = None
    booking.save()
    
    # Send notification to existing occupants if applicable
    if not booking.is_first_occupant:
        from accounts.models import Notification
        existing_occupants = Booking.objects.filter(
            accommodation_property=booking.accommodation_property,
            room=booking.room,
            status__in=['CONFIRMED', 'CHECKED_IN'],
            tenant__isnull=False
        ).exclude(tenant=request.user)
        
        from bookings.utils import send_new_roommate_email
        for occupant_booking in existing_occupants:
            Notification.objects.create(
                user=occupant_booking.tenant,
                title='New Roommate Confirmed',
                message=f'{request.user.get_full_name()} has been confirmed as your roommate.',
                notification_type='INFO'
            )
            try:
                send_new_roommate_email(
                    existing_user=occupant_booking.tenant,
                    new_user=request.user,
                    new_booking=booking,
                    booking=occupant_booking,
                    room=booking.assigned_room,
                    compatibility_score=booking.compatibility_score
                )
            except Exception as e:
                print(f"Failed to send new roommate email: {e}")
                
        from bookings.utils import send_booking_confirmed_email
        try:
            roommates_list = list(existing_occupants.values_list('tenant', flat=True)) if not booking.is_first_occupant else []
            send_booking_confirmed_email(
                booking=booking,
                user=request.user,
                room=booking.assigned_room,
                roommates=roommates_list,
                compatibility_score=booking.compatibility_score
            )
        except Exception as e:
            print(f"Failed to send booking confirmed email: {e}")
    
    messages.success(request, 'Your booking has been confirmed!')
    return redirect('bookings:booking_confirmation', booking_id=booking.id)


@require_POST
@login_required
def reject_consent(request, booking_id):
    """
    Handle user rejecting the compatibility result.
    Performs temporary cancellation with 24-hour reinstatement window.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Set temporary cancellation timestamp
    booking.temp_cancelled_at = timezone.now()
    booking.temp_cancel_expires_at = timezone.now() + timezone.timedelta(hours=24)
    booking.status = 'TEMP_CANCELLED'
    booking.save()
    
    # Send notification
    from accounts.models import Notification
    Notification.objects.create(
        user=request.user,
        title='Booking Temporarily Cancelled',
        message='You have 24 hours to reinstate your booking. After that, it will be permanently cancelled.',
        notification_type='WARNING'
    )
    
    messages.warning(request, 'Your booking has been temporarily cancelled. You have 24 hours to reinstate it.')
    return redirect('bookings:booking_reinstatement', booking_id=booking.id)


@login_required
def booking_reinstatement(request, booking_id):
    """
    Display reinstatement screen with countdown timer.
    Allows user to reinstate booking within 24-hour window.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='TEMP_CANCELLED')
    
    # Check if reinstatement window has expired
    if booking.temp_cancel_expires_at and booking.temp_cancel_expires_at < timezone.now():
        booking.status = 'CANCELLED'
        booking.save()
        messages.error(request, 'The reinstatement window has expired. Your booking has been permanently cancelled.')
        return redirect('landing:property_detail', pk=booking.accommodation_property.id)
    
    # Calculate remaining time
    if booking.temp_cancel_expires_at:
        remaining = booking.temp_cancel_expires_at - timezone.now()
        hours_remaining = int(remaining.total_seconds() // 3600)
        minutes_remaining = int((remaining.total_seconds() % 3600) // 60)
    else:
        hours_remaining = 0
        minutes_remaining = 0
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'hours_remaining': hours_remaining,
        'minutes_remaining': minutes_remaining,
    }
    
    return render(request, 'bookings/booking_reinstatement.html', context)


@require_POST
@login_required
def reinstate_booking(request, booking_id):
    """
    Handle user reinstating a temporarily cancelled booking.
    Increments reinstatement_count and returns booking to CONFIRMED status.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user, status='TEMP_CANCELLED')
    
    # Check if reinstatement window has expired
    if booking.temp_cancel_expires_at and booking.temp_cancel_expires_at < timezone.now():
        booking.status = 'CANCELLED'
        booking.save()
        messages.error(request, 'The reinstatement window has expired. Your booking has been permanently cancelled.')
        return JsonResponse({'success': False, 'message': 'Reinstatement window expired'})
    
    # Reinstate booking
    booking.reinstatement_count += 1
    booking.temp_cancelled_at = None
    booking.temp_cancel_expires_at = None
    booking.status = 'CONFIRMED'
    booking.consent_given_at = timezone.now()
    booking.save()
    
    # Send notification
    from accounts.models import Notification
    Notification.objects.create(
        user=request.user,
        title='Booking Reinstated',
        message='Your booking has been successfully reinstated.',
        notification_type='SUCCESS'
    )
    
    return JsonResponse({'success': True, 'message': 'Booking reinstated successfully'})


@require_POST
@login_required
def permanent_cancel(request, booking_id):
    """
    Handle user permanently cancelling a booking (either from reinstatement screen or directly).
    Sets status to CANCELLED permanently.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    booking.status = 'CANCELLED'
    booking.temp_cancelled_at = None
    booking.temp_cancel_expires_at = None
    booking.save()
    
    # Send notification
    from accounts.models import Notification
    Notification.objects.create(
        user=request.user,
        title='Booking Cancelled',
        message='Your booking has been permanently cancelled.',
        notification_type='INFO'
    )
    
    messages.info(request, 'Your booking has been permanently cancelled.')
    return redirect('landing:property_detail', pk=booking.accommodation_property.id)


@login_required
def no_match_found(request, booking_id):
    """
    Display no-match found alternatives when compatibility score is below threshold.
    Shows alternative rooms or properties.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    
    # Get alternative properties
    from properties.models import Property
    alternatives = Property.objects.filter(
        is_active=True,
        available_from__lte=booking.move_in_date
    ).exclude(id=booking.accommodation_property.id)[:5]
    
    context = {
        'booking': booking,
        'property': booking.accommodation_property,
        'alternatives': alternatives,
    }
    
    return render(request, 'bookings/no_match_found.html', context)
