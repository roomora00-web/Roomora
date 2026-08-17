"""
Student Dashboard Views for Booking Status Cards

Views for displaying booking status cards on student dashboard as per Part 13.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, timedelta

from .models import Booking
from .constants import BillingModel, SemesterStructure
from .grace_period_service import GracePeriodService
from .overstay_service import OverstayService
from .vacation_reserve_service import VacationReserveService
from .rebooking_service import RebookingService


@login_required
def student_booking_status_cards(request):
    """
    Student Dashboard - Booking Status Cards (Part 10 & Part 13)
    
    Returns booking status cards for all bookings based on their current state.
    Handles all 17 booking statuses with dynamic card types.
    """
    from django.utils import timezone
    
    # Get all bookings for the user (not just active ones)
    bookings = Booking.objects.filter(
        tenant=request.user
    ).select_related('accommodation_property', 'room_type', 'unit_type', 'assigned_room').order_by('-created_at')
    
    cards = []
    
    for booking in bookings:
        card_data = {
            'booking_id': booking.id,
            'property_title': booking.accommodation_property.title,
            'room_type': booking.room_type.room_type_name if booking.room_type else 'N/A',
            'unit_type': booking.unit_type.unit_type_name if booking.unit_type else 'N/A',
            'status': booking.status,
            'created_at': booking.created_at,
            'reference': f"SM-{booking.created_at.strftime('%Y%m%d')}-{str(booking.id).zfill(4)}",
        }
        
        # Determine card type based on booking status (Part 10)
        if booking.status == 'INITIATED':
            card = _get_initiated_card(booking)
        elif booking.status == 'LIFESTYLE_PENDING':
            card = _get_lifestyle_pending_card(booking)
        elif booking.status == 'AWAITING_COMPATIBILITY':
            card = _get_awaiting_compatibility_card(booking)
        elif booking.status == 'AUTO_ASSIGNED':
            card = _get_auto_assigned_card(booking)
        elif booking.status == 'CONSENT_PENDING':
            card = _get_consent_pending_card(booking)
        elif booking.status == 'CONSENT_ACCEPTED':
            card = _get_consent_accepted_card(booking)
        elif booking.status == 'TEMPORARILY_CANCELLED':
            card = _get_temporarily_cancelled_card(booking)
        elif booking.status == 'REINSTATED':
            card = _get_reinstated_card(booking)
        elif booking.status == 'ADMIN_PENDING':
            card = _get_admin_pending_card(booking)
        elif booking.status == 'CONFIRMED':
            card = _get_confirmed_card(booking)
        elif booking.status == 'ACTIVE':
            card = _get_active_card(booking)
        elif booking.status == 'GRACE_PERIOD':
            card = _get_grace_period_dashboard_card(booking)
        elif booking.status == 'VACATION_RESERVE':
            card = _get_vacation_reserve_dashboard_card(booking)
        elif booking.status == 'OVERSTAY':
            card = _get_overstay_dashboard_card(booking)
        elif booking.status == 'CANCELLED' or booking.status == 'PERMANENTLY_CANCELLED':
            card = _get_cancelled_card(booking)
        elif booking.status == 'EXPIRED':
            card = _get_expired_card(booking)
        else:
            card = _get_default_card(booking)
        
        card_data.update(card)
        cards.append(card_data)
    
    context = {
        'cards': cards,
    }
    
    return render(request, 'bookings/dashboard/booking_status_cards.html', context)


# Part 10: Dynamic Status Card Functions for All Booking States

def _get_initiated_card(booking):
    """Card for INITIATED status - Soft lock active"""
    from django.utils import timezone
    
    time_remaining = None
    if booking.soft_lock_expires_at:
        time_remaining = booking.soft_lock_expires_at - timezone.now()
        hours_remaining = max(0, time_remaining.total_seconds() / 3600)
    
    return {
        'card_type': 'initiated',
        'title': 'Complete Your Booking',
        'subtitle': 'Slot reserved — complete within 2 hours',
        'hours_remaining': hours_remaining if time_remaining else 2,
        'progress_percentage': 10,
        'next_step': 'acknowledge_house_rules',
        'action_text': 'Continue Booking',
        'action_url': f"/api/bookings/booking/{booking.id}/resume/",
        'warning': time_remaining and time_remaining.total_seconds() < 0.5 * 3600,  # warn at 30 mins
    }


def _get_lifestyle_pending_card(booking):
    """Card for LIFESTYLE_PENDING status"""
    return {
        'card_type': 'lifestyle_pending',
        'title': 'Complete Lifestyle Questionnaire',
        'subtitle': 'Help us find your ideal roommate',
        'progress_percentage': 30,
        'next_step': 'lifestyle_questionnaire',
        'action_text': 'Complete Questionnaire',
        'action_url': f"/api/bookings/booking/{booking.id}/lifestyle-check/",
    }


def _get_awaiting_compatibility_card(booking):
    """Card for AWAITING_COMPATIBILITY status"""
    return {
        'card_type': 'awaiting_compatibility',
        'title': 'Finding Your Match',
        'subtitle': 'We are analyzing compatibility with potential roommates',
        'progress_percentage': 50,
        'action_text': 'Processing',
        'action_url': None,
        'info': 'This usually takes less than a minute.',
    }


def _get_auto_assigned_card(booking):
    """Card for AUTO_ASSIGNED status - High compatibility auto-assignment"""
    score = booking.compatibility_score or 0
    return {
        'card_type': 'auto_assigned',
        'title': 'Great Match Found!',
        'subtitle': f'Compatibility Score: {score}%',
        'progress_percentage': 70,
        'compatibility_score': score,
        'action_text': 'View Match',
        'action_url': f"/api/bookings/booking/{booking.id}/compatibility-result/",
        'success': score >= 85,
    }


def _get_consent_pending_card(booking):
    """Card for CONSENT_PENDING status - User needs to accept/reject"""
    from django.utils import timezone
    
    time_remaining = None
    if booking.consent_deadline:
        time_remaining = booking.consent_deadline - timezone.now()
        hours_remaining = max(0, time_remaining.total_seconds() / 3600)
    
    score = booking.compatibility_score or 0
    return {
        'card_type': 'consent_pending',
        'title': 'Review Your Match',
        'subtitle': f'Compatibility Score: {score}%',
        'progress_percentage': 75,
        'compatibility_score': score,
        'hours_remaining': hours_remaining if time_remaining else 24,
        'action_text': 'Review & Decide',
        'action_url': f"/api/bookings/booking/{booking.id}/compatibility-result/",
        'urgent': time_remaining and time_remaining.total_seconds() < 6 * 3600,
    }


def _get_consent_accepted_card(booking):
    """Card for CONSENT_ACCEPTED status - Pending admin finalization"""
    return {
        'card_type': 'consent_accepted',
        'title': 'Match Accepted',
        'subtitle': 'Awaiting admin confirmation',
        'progress_percentage': 85,
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
        'info': 'Admin will review and confirm your booking shortly.',
    }


def _get_temporarily_cancelled_card(booking):
    """Card for TEMPORARILY_CANCELLED status - Reinstatement window"""
    from django.utils import timezone
    
    time_remaining = None
    if booking.temp_cancelled_at:
        expiry = booking.temp_cancelled_at + timezone.timedelta(hours=24)
        time_remaining = expiry - timezone.now()
        hours_remaining = max(0, time_remaining.total_seconds() / 3600)
    
    return {
        'card_type': 'temporarily_cancelled',
        'title': 'Booking Temporarily Cancelled',
        'subtitle': 'You can reinstate within 24 hours',
        'progress_percentage': 60,
        'hours_remaining': hours_remaining if time_remaining else 24,
        'action_text': 'Reinstate Booking',
        'action_url': f"/api/bookings/booking/{booking.id}/reinstatement/",
        'warning': time_remaining and time_remaining.total_seconds() < 6 * 3600,
    }


def _get_reinstated_card(booking):
    """Card for REINSTATED status - Back in flow"""
    return {
        'card_type': 'reinstated',
        'title': 'Booking Reinstated',
        'subtitle': 'Continue with your booking',
        'progress_percentage': 50,
        'action_text': 'Continue',
        'action_url': f"/api/bookings/booking/{booking.id}/resume/",
        'success': True,
    }


def _get_admin_pending_card(booking):
    """Card for ADMIN_PENDING status - Awaiting admin review"""
    from django.utils import timezone
    
    waiting_hours = 0
    if booking.created_at:
        waiting_hours = (timezone.now() - booking.created_at).total_seconds() / 3600
    
    return {
        'card_type': 'admin_pending',
        'title': 'Pending Admin Review',
        'subtitle': f'Waiting {waiting_hours|floatformat:1} hours',
        'progress_percentage': 90,
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
        'info': 'Admin will review and assign your room shortly.',
    }


def _get_confirmed_card(booking):
    """Card for CONFIRMED status - Booking confirmed, awaiting move-in"""
    from django.utils import timezone
    from datetime import date
    
    move_in = booking.move_in_date
    days_until_movein = (move_in - date.today()).days if move_in else None
    
    return {
        'card_type': 'confirmed',
        'title': 'Booking Confirmed',
        'subtitle': f'Move-in in {days_until_movein} days' if days_until_movein else 'Move-in date TBD',
        'progress_percentage': 95,
        'move_in_date': move_in,
        'days_until_movein': days_until_movein,
        'room_number': booking.assigned_room.room_number if booking.assigned_room else 'To be assigned',
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
        'success': True,
    }


def _get_active_card(booking):
    """Card for ACTIVE status - Currently staying"""
    from datetime import date
    
    move_in = booking.move_in_date
    move_out = booking.move_out_date
    total_days = (move_out - move_in).days if move_in and move_out else 0
    days_elapsed = (date.today() - move_in).days if move_in else 0
    days_remaining = (move_out - date.today()).days if move_out else 0
    progress = (days_elapsed / total_days * 100) if total_days > 0 else 0
    
    return {
        'card_type': 'active',
        'title': 'Active Stay',
        'subtitle': f'{days_remaining} days remaining',
        'progress_percentage': min(100, max(0, progress)),
        'move_in_date': move_in,
        'move_out_date': move_out,
        'days_elapsed': days_elapsed,
        'days_remaining': max(0, days_remaining),
        'room_number': booking.assigned_room.room_number if booking.assigned_room else 'N/A',
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
        'success': True,
    }


def _get_grace_period_dashboard_card(booking):
    """Card for GRACE_PERIOD status - Grace period active"""
    from datetime import date
    
    grace_end = booking.grace_period_end
    days_remaining = (grace_end - date.today()).days if grace_end else 0
    
    return {
        'card_type': 'grace_period',
        'title': 'Grace Period',
        'subtitle': f'{days_remaining} days until move-out',
        'progress_percentage': 100,
        'grace_period_end': grace_end,
        'days_remaining': max(0, days_remaining),
        'room_number': booking.assigned_room.room_number if booking.assigned_room else 'N/A',
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
        'warning': True,
    }


def _get_vacation_reserve_dashboard_card(booking):
    """Card for VACATION_RESERVE status - Between semesters"""
    from datetime import date
    
    return_date = booking.semester_2_start_date or booking.vacation_reserve_end
    days_until_return = (return_date - date.today()).days if return_date else 0
    
    return {
        'card_type': 'vacation_reserve',
        'title': 'Vacation Reserve',
        'subtitle': f'Semester 2 return in {days_until_return} days',
        'progress_percentage': 100,
        'semester2_start_date': return_date,
        'days_until_return': max(0, days_until_return),
        'room_number': booking.assigned_room.room_number if booking.assigned_room else 'N/A',
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
        'info': 'Your room is reserved for your return.',
    }


def _get_overstay_dashboard_card(booking):
    """Card for OVERSTAY status - Overstay charges accruing"""
    from datetime import date
    
    days_overstay = 0
    if booking.overstay_start:
        days_overstay = (date.today() - booking.overstay_start.date()).days
    
    return {
        'card_type': 'overstay',
        'title': 'Overstay',
        'subtitle': f'{days_overstay} days in overstay',
        'progress_percentage': 100,
        'days_overstay': max(0, days_overstay),
        'total_charges': booking.overstay_accrued,
        'daily_rate': booking.overstay_daily_rate,
        'room_number': booking.assigned_room.room_number if booking.assigned_room else 'N/A',
        'action_text': 'Contact Support',
        'action_url': '/contact/',
        'urgent': True,
    }


def _get_cancelled_card(booking):
    """Card for CANCELLED/PERMANENTLY_CANCELLED status"""
    return {
        'card_type': 'cancelled',
        'title': 'Booking Cancelled',
        'subtitle': booking.cancellation_reason or 'No reason provided',
        'progress_percentage': 0,
        'cancelled_at': booking.permanently_cancelled_at,
        'refund_status': booking.refund_status,
        'refund_amount': booking.refund_amount,
        'action_text': 'Book Again',
        'action_url': '/properties/',
    }


def _get_expired_card(booking):
    """Card for EXPIRED status - Soft lock expired"""
    return {
        'card_type': 'expired',
        'title': 'Booking Expired',
        'subtitle': 'Soft lock expired without completion',
        'progress_percentage': 0,
        'expired_at': booking.soft_lock_expires_at,
        'action_text': 'Book Again',
        'action_url': '/properties/',
    }


def _get_default_card(booking):
    """Default card for unknown status"""
    return {
        'card_type': 'default',
        'title': 'Booking',
        'subtitle': f'Status: {booking.status}',
        'progress_percentage': 0,
        'action_text': 'View Details',
        'action_url': f"/api/bookings/booking/{booking.id}/",
    }


def _get_single_semester_card(booking):
    """Single semester booking card (Part 13.1)"""
    move_in = booking.move_in_date
    move_out = booking.move_out_date
    total_days = (move_out - move_in).days
    days_remaining = (move_out - date.today()).days
    
    # Calculate progress percentage
    progress = ((date.today() - move_in).days / total_days) * 100 if total_days > 0 else 0
    progress = max(0, min(100, progress))
    
    return {
        'card_type': 'single_semester',
        'semester_number': 1,
        'move_in_date': move_in,
        'move_out_date': move_out,
        'duration_days': total_days,
        'days_remaining': max(0, days_remaining),
        'progress_percentage': round(progress, 1),
        'total_amount': booking.total_amount,
    }


def _get_continuous_stay_card(booking):
    """Continuous stay card (Part 13.2)"""
    move_in = booking.move_in_date
    move_out = booking.move_out_date
    total_days = (move_out - move_in).days
    days_remaining = (move_out - date.today()).days
    
    # Calculate progress
    progress = ((date.today() - move_in).days / total_days) * 100 if total_days > 0 else 0
    progress = max(0, min(100, progress))
    
    return {
        'card_type': 'continuous_stay',
        'num_semesters': booking.num_semesters,
        'semester_structure': booking.semester_structure,
        'move_in_date': move_in,
        'move_out_date': move_out,
        'duration_days': total_days,
        'days_remaining': max(0, days_remaining),
        'progress_percentage': round(progress, 1),
        'total_amount': booking.total_amount,
    }


def _get_vacation_reserve_card(booking):
    """Vacation reserve card (Part 13.2)"""
    vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
    
    if vacation_status['in_vacation_reserve']:
        card_type = 'vacation_reserve'
        days_until_return = vacation_status['days_remaining']
        semester2_start = vacation_status['semester2_start']
        semester2_end = vacation_status['semester2_end']
    else:
        # Before or after vacation
        card_type = 'split_stay'
        days_until_return = None
        semester2_start = booking.vacation_gap_end
        semester2_end = booking.move_out_date
    
    return {
        'card_type': card_type,
        'semester1_start': booking.move_in_date,
        'semester1_end': booking.vacation_gap_start - timedelta(days=1) if booking.vacation_gap_start else None,
        'vacation_reserve_start': vacation_status.get('vacation_start'),
        'vacation_reserve_end': vacation_status.get('vacation_end'),
        'semester2_start': semester2_start,
        'semester2_end': semester2_end,
        'days_until_return': days_until_return,
        'room_locked': True,
        'no_charge_during_vacation': True,
    }


def _get_standard_booking_card(booking):
    """Standard booking card (monthly or annual)"""
    move_in = booking.move_in_date
    move_out = booking.move_out_date
    total_days = (move_out - move_in).days
    days_remaining = (move_out - date.today()).days
    
    # Calculate progress
    progress = ((date.today() - move_in).days / total_days) * 100 if total_days > 0 else 0
    progress = max(0, min(100, progress))
    
    return {
        'card_type': 'standard',
        'move_in_date': move_in,
        'move_out_date': move_out,
        'duration_days': total_days,
        'days_remaining': max(0, days_remaining),
        'progress_percentage': round(progress, 1),
        'total_amount': booking.total_amount,
    }


@login_required
def grace_period_card(request, booking_id):
    """
    Grace Period Card (Part 13.3)
    
    Shows grace period status and rebooking options
    """
    booking = Booking.objects.get(id=booking_id, tenant=request.user)
    grace_status = GracePeriodService.get_grace_period_status(booking)
    
    card_data = {
        'booking_id': booking.id,
        'property_title': booking.accommodation_property.title,
        'room_number': booking.room_assignment.assigned_room_number if booking.room_assignment else 'N/A',
        'move_out_date': booking.move_out_date,
        'grace_period_start': grace_status['grace_period_start'],
        'grace_period_end': grace_status['grace_period_end'],
        'slot_available_date': grace_status['slot_available_date'],
        'in_grace_period': grace_status['in_grace_period'],
        'days_remaining': grace_status.get('days_remaining', 0),
        'days_in_grace': grace_status.get('days_in_grace', 0),
    }
    
    # Check rebooking eligibility
    if grace_status['in_grace_period']:
        rebooking_eligibility = RebookingService.check_rebooking_eligibility(booking)
        card_data['rebooking_eligible'] = rebooking_eligibility['eligible']
        card_data['rebooking_options'] = rebooking_eligibility.get('options', [])
    else:
        card_data['rebooking_eligible'] = False
        card_data['rebooking_options'] = []
    
    return render(request, 'bookings/dashboard/grace_period_card.html', {'card': card_data})


@login_required
def overstay_card(request, booking_id):
    """
    Overstay Card
    
    Shows overstay status and charges
    """
    booking = Booking.objects.get(id=booking_id, tenant=request.user)
    overstay_status = OverstayService.get_overstay_status(booking)
    
    card_data = {
        'booking_id': booking.id,
        'property_title': booking.accommodation_property.title,
        'room_number': booking.room_assignment.assigned_room_number if booking.room_assignment else 'N/A',
        'in_overstay': overstay_status['in_overstay'],
        'days_in_overstay': overstay_status.get('days_in_overstay', 0),
        'total_charge': overstay_status.get('total_charge', 0),
        'daily_rate': overstay_status.get('overstay_daily_rate', 0),
        'escalated': overstay_status.get('escalated', False),
        'overstay_start_date': overstay_status.get('overstay_start_date'),
    }
    
    return render(request, 'bookings/dashboard/overstay_card.html', {'card': card_data})


@login_required
def booking_actions(request, booking_id):
    """
    Booking Actions API
    
    Handles student actions on their bookings
    """
    booking = Booking.objects.get(id=booking_id, tenant=request.user)
    action = request.POST.get('action')
    
    if action == 'confirm_departure':
        result = RebookingService.confirm_departure(booking, requested_by=request.user)
        return JsonResponse({'success': True, 'result': result})
    
    elif action == 'request_extension':
        additional_months = int(request.POST.get('additional_months', 1))
        try:
            result = RebookingService.request_monthly_extension(
                booking,
                additional_months,
                requested_by=request.user
            )
            return JsonResponse({'success': True, 'result': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    elif action == 'update_semester2_date':
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
    
    return JsonResponse({'success': False, 'error': 'Unknown action'})
