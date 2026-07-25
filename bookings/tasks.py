from celery import shared_task
from django.utils import timezone
from .models import Booking, BookingConsent
import datetime

@shared_task
def send_soft_lock_reminder(booking_id):
    """
    Task A: Soft lock expiry reminder
    Fires at 1 hour (1 hour before expiry)
    Sends notification to user to complete booking
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id, status='INITIATED')
        
        # Check if reminder already sent
        if booking.reminder_sent:
            return f"Reminder already sent for booking {booking_id}"
        
        # Check if booking is still within reminder window
        if booking.is_soft_lock_expired():
            return f"Booking {booking_id} already expired, skipping reminder"
        
        # Send in-app notification
        Notification.objects.create(
            user=booking.tenant,
            title='BOOKING EXPIRING SOON',
            message=f"Your booking expires in 1 hour. Complete your booking now to keep your slot.\n\nProperty: {booking.accommodation_property.title}\nReference: {booking.reference_number}\n\n[Resume Booking]",
        )
        
        # Mark reminder as sent
        booking.reminder_sent = True
        booking.save()
        
        return f"Sent 1-hour reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found or not in INITIATED status"


@shared_task
def schedule_soft_lock_tasks(booking_id):
    """
    Schedule both Celery tasks immediately after soft lock transaction commits:
    - Task A: Soft lock expiry reminder at 1 hour
    - Task B: Soft lock expiry at 2 hours
    """
    from celery import current_app
    
    # Schedule reminder at 1 hour (3600 seconds)
    current_app.send_task(
        'bookings.tasks.send_soft_lock_reminder',
        args=[booking_id],
        countdown=1 * 60 * 60  # 1 hour in seconds
    )
    
    # Schedule expiry at 2 hours (7200 seconds)
    current_app.send_task(
        'bookings.tasks.expire_soft_lock',
        args=[booking_id],
        countdown=2 * 60 * 60  # 2 hours in seconds
    )
    
    return f"Scheduled soft lock tasks for booking {booking_id}"

@shared_task
def expire_soft_lock(booking_id):
    """
    Task B: Soft lock expiry
    Fires at 2 hours
    Sets booking status to EXPIRED, releases slot, notifies user
    """
    from accounts.models import Notification
    from bookings.services.booking.soft_lock_service import SoftLockService
    
    try:
        booking = Booking.objects.get(id=booking_id, status='INITIATED')
        
        # Release the soft lock
        SoftLockService.release_soft_lock(booking)
        
        # Send notification to user
        Notification.objects.create(
            user=booking.tenant,
            title='BOOKING EXPIRED',
            message=f"Your 2-hour booking window has expired. The slot has been released.\n\nProperty: {booking.accommodation_property.title}\nReference: {booking.reference_number}\n\n[Search Again]",
        )
        
        return f"Expired soft lock for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found or not in INITIATED status"


@shared_task
def check_soft_lock_expiries():
    """
    Periodic task to check for expired soft locks and release them if
    the booking hasn't moved forward.
    """
    now = timezone.now()
    expired_bookings = Booking.objects.filter(
        status='INITIATED',
        soft_lock_expires_at__lte=now
    )
    
    for booking in expired_bookings:
        # Check if they completed payment or moved forward
        # For our logic, if it's still INITIATED and expired, we cancel
        booking.release_soft_lock()
        booking.set_status('PERMANENTLY_CANCELLED', note='Soft lock expired without completion')
        
    return f"Processed {expired_bookings.count()} soft lock expirations."

@shared_task
def check_consent_deadlines():
    """
    Periodic task to check for expired roommate consent requests.
    """
    now = timezone.now()
    # Find consents that are pending but have expired
    expired_consents = BookingConsent.objects.filter(
        expires_at__lte=now
    ).exclude(
        user_status__in=['ACCEPTED', 'REJECTED'],
        roommate_status__in=['ACCEPTED', 'REJECTED']
    )
    
    count = 0
    for consent in expired_consents:
        if consent.user_status == 'PENDING':
            consent.user_status = 'EXPIRED'
        if consent.roommate_status == 'PENDING':
            consent.roommate_status = 'EXPIRED'
        consent.save()
        
        # We need to trigger the rejection/cancellation workflow on the booking
        booking = consent.booking
        booking.set_status('TEMPORARILY_CANCELLED', note='Consent deadline expired')
        
        # Hold slot for 6 hours
        booking.slot_hold_expires_at = now + timezone.timedelta(hours=6)
        booking.temp_cancel_expires_at = now + timezone.timedelta(hours=24)
        booking.save()
        
        count += 1
        
    return f"Processed {count} consent expirations."

@shared_task
def check_slot_hold_expiries():
    """
    Periodic task to release slots that were held for 6 hours after rejection.
    """
    now = timezone.now()
    expired_holds = Booking.objects.filter(
        status='TEMPORARILY_CANCELLED',
        slot_hold_expires_at__lte=now
    ).exclude(slot_hold_expires_at__isnull=True)
    
    for booking in expired_holds:
        # Release the slot back to the physical room
        if booking.assigned_room and booking.assigned_room.pending_slots > 0:
            booking.assigned_room.pending_slots -= 1
            booking.assigned_room.save()
        
        # Clear the hold expiry so we don't process it again
        booking.slot_hold_expires_at = None
        booking.save()

    return f"Processed {expired_holds.count()} slot hold releases."

@shared_task
def check_temp_cancel_expiries():
    """
    Chapter 15: Periodic task to permanently cancel bookings after 24-hour reinstatement window expires.
    """
    now = timezone.now()
    expired_cancels = Booking.objects.filter(
        status='TEMPORARILY_CANCELLED',
        temp_cancel_expires_at__lte=now
    ).exclude(temp_cancel_expires_at__isnull=True)
    
    from accounts.models import Notification
    
    for booking in expired_cancels:
        # Permanent cancellation
        booking.status = 'PERMANENTLY_CANCELLED'
        booking.permanently_cancelled_at = now
        booking.cancellation_initiated_by = 'system'
        booking.refund_status = 'pending'
        
        # Release slot if still held
        if booking.assigned_room and booking.assigned_room.pending_slots > 0:
            booking.assigned_room.pending_slots -= 1
            booking.assigned_room.save()
        
        booking.save()
        
        # Notify user
        Notification.objects.create(
            user=booking.tenant,
            title='BOOKING PERMANENTLY CLOSED',
            message=f"{booking.accommodation_property.title} — {booking.get_room_type_display() if booking.room_type else 'Unit'}\nReference: {booking.reference_number}\n\nYour 24-hour reinstatement window has passed.\nYour booking has been permanently cancelled.\n\nRefund Status: Processing\nAmount: GH₵ {booking.total_amount}\nExpected: 3-5 business days",
        )
        
        # Notify existing occupant
        existing_bookings = Booking.objects.filter(
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type,
            assigned_room=booking.assigned_room,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
        ).exclude(tenant=booking.tenant)
        
        for existing_booking in existing_bookings:
            Notification.objects.create(
                user=existing_booking.tenant,
                title='ROOM UPDATE',
                message=f"The user who was proposed as your roommate for Room {booking.assigned_room.room_number if booking.assigned_room else 'Assigned'} did not confirm their booking.\n\nYour room is now open for a new roommate match.\nYou will be notified when a compatible user books this room.\n\nNo action required from you.",
            )
    
    return f"Processed {expired_cancels.count()} permanent cancellations."


# Part 7: Consent Workflow Tasks

@shared_task
def send_consent_deadline_reminder(booking_id):
    """
    Send reminder 12 hours before consent deadline expires.
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if booking is still pending consent
        if booking.consent_given_at or booking.status not in ['INITIATED', 'PENDING_CONSENT']:
            return f"Booking {booking_id} already processed, skipping reminder"
        
        # Send notification
        Notification.objects.create(
            user=booking.tenant,
            title='Consent Deadline Approaching',
            message=f"You have 12 hours remaining to accept or decline your booking.\n\nProperty: {booking.accommodation_property.name}\nReference: {booking.reference_number}\n\nPlease review your compatibility result and make your decision.",
            notification_type='WARNING'
        )
        
        return f"Sent consent deadline reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def expire_consent_deadline(booking_id):
    """
    Expire consent deadline and permanently cancel booking if no action taken.
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if user already responded
        if booking.consent_given_at:
            return f"Booking {booking_id} already has consent, skipping expiry"
        
        # Check if booking is still pending consent
        if booking.status not in ['INITIATED', 'PENDING_CONSENT']:
            return f"Booking {booking_id} not in pending consent status"
        
        # Permanently cancel booking
        booking.status = 'CANCELLED'
        booking.save()
        
        # Send notification
        Notification.objects.create(
            user=booking.tenant,
            title='Consent Deadline Expired',
            message=f"Your consent deadline has expired. Your booking has been permanently cancelled.\n\nProperty: {booking.accommodation_property.name}\nReference: {booking.reference_number}\n\nYou can start a new booking anytime.",
            notification_type='INFO'
        )
        
        return f"Expired consent deadline for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def schedule_consent_tasks(booking_id, deadline_hours=24):
    """
    Schedule consent deadline and reminder tasks when consent is required.
    """
    from celery import current_app
    
    # Schedule reminder at deadline - 12 hours
    reminder_seconds = (deadline_hours - 12) * 60 * 60
    if reminder_seconds > 0:
        current_app.send_task(
            'bookings.tasks.send_consent_deadline_reminder',
            args=[booking_id],
            countdown=reminder_seconds
        )
    
    # Schedule expiry at deadline
    expiry_seconds = deadline_hours * 60 * 60
    current_app.send_task(
        'bookings.tasks.expire_consent_deadline',
        args=[booking_id],
        countdown=expiry_seconds
    )
    
    return f"Scheduled consent tasks for booking {booking_id}"


# Part 12: Additional Celery Background Tasks

@shared_task
def send_lifestyle_reminder(booking_id):
    """
    Send reminder to complete lifestyle questionnaire.
    Fires at 12 hours after booking initiation if not completed.
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if lifestyle already completed
        if booking.lifestyle_assessment_completed:
            return f"Booking {booking_id} already completed lifestyle, skipping reminder"
        
        # Check if booking is still in appropriate status
        if booking.status not in ['INITIATED', 'LIFESTYLE_PENDING']:
            return f"Booking {booking_id} not in lifestyle pending status"
        
        # Send notification
        Notification.objects.create(
            user=booking.tenant,
            title='Complete Your Lifestyle Questionnaire',
            message=f"To help us find you the best roommate match, please complete your lifestyle questionnaire.\n\nProperty: {booking.accommodation_property.title}\nReference: {booking.reference_number}\n\nThis takes about 5 minutes and helps ensure compatibility with your roommate.",
            notification_type='INFO'
        )
        
        return f"Sent lifestyle reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def schedule_lifestyle_reminder(booking_id, hours=12):
    """
    Schedule lifestyle questionnaire reminder.
    """
    from celery import current_app
    
    reminder_seconds = hours * 60 * 60
    current_app.send_task(
        'bookings.tasks.send_lifestyle_reminder',
        args=[booking_id],
        countdown=reminder_seconds
    )
    
    return f"Scheduled lifestyle reminder for booking {booking_id}"


@shared_task
def send_vacation_reserve_reminder(booking_id):
    """
    Send reminder for Semester 2 return date confirmation.
    Fires 7 days before vacation reserve ends.
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if booking has vacation reserve
        if not booking.vacation_reserve_active or not booking.vacation_reserve_end:
            return f"Booking {booking_id} does not have vacation reserve"
        
        # Check if already active (returned)
        if booking.status == 'ACTIVE':
            return f"Booking {booking_id} already active, skipping reminder"
        
        # Send notification
        Notification.objects.create(
            user=booking.tenant,
            title='Semester 2 Return Date Approaching',
            message=f"Your Semester 2 return date is coming up on {booking.vacation_reserve_end.strftime('%B %d, %Y')}.\n\nPlease confirm your return date or update if needed.\n\nProperty: {booking.accommodation_property.title}\nReference: {booking.reference_number}",
            notification_type='INFO'
        )
        
        return f"Sent vacation reserve reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def schedule_vacation_reserve_reminders(booking_id):
    """
    Schedule vacation reserve reminders at 7 days and 1 day before return.
    """
    from celery import current_app
    from datetime import timedelta
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        if not booking.vacation_reserve_end:
            return f"Booking {booking_id} has no vacation reserve end date"
        
        now = timezone.now()
        return_date = booking.vacation_reserve_end
        
        # 7 days before
        days_7 = (return_date - now - timedelta(days=7)).total_seconds()
        if days_7 > 0:
            current_app.send_task(
                'bookings.tasks.send_vacation_reserve_reminder',
                args=[booking_id],
                countdown=days_7
            )
        
        # 1 day before
        days_1 = (return_date - now - timedelta(days=1)).total_seconds()
        if days_1 > 0:
            current_app.send_task(
                'bookings.tasks.send_vacation_reserve_reminder',
                args=[booking_id],
                countdown=days_1
            )
        
        return f"Scheduled vacation reserve reminders for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def check_overstay_escalation():
    """
    Periodic task to check for overstays and send escalation notifications.
    Runs daily.
    """
    from accounts.models import Notification
    from .overstay_service import OverstayService
    
    now = timezone.now()
    
    # Find bookings in overstay status
    overstayed_bookings = Booking.objects.filter(
        status='OVERSTAY'
    ).select_related('tenant', 'accommodation_property', 'assigned_room')
    
    escalation_count = 0
    
    for booking in overstayed_bookings:
        escalation_status = OverstayService.check_escalation_required(booking)
        
        if escalation_status['escalation_required']:
            # Send notification to admin
            admin_emails = ['admin@staymatch.com']  # Configure as needed
            
            # Send in-app notification to admins
            Notification.objects.create(
                user=None,  # System notification
                title='OVERSTAY ESCALATION REQUIRED',
                message=f"Student {booking.tenant.full_name} has overstayed Room {booking.assigned_room.room_number if booking.assigned_room else 'N/A'}.\n\nProperty: {booking.accommodation_property.title}\nOverstay Duration: {escalation_status['days_overstayed']} days\nTotal Charges: GH₵ {escalation_status['total_charge']}\n\nAction Required: Contact student or initiate eviction process.",
                notification_type='URGENT'
            )
            
            # Notify student
            Notification.objects.create(
                user=booking.tenant,
                title='OVERSTAY NOTICE',
                message=f"You have overstayed your booking by {escalation_status['days_overstayed']} days.\n\nCurrent Charges: GH₵ {escalation_status['total_charge']}\nDaily Rate: GH₵ {escalation_status['daily_rate']}\n\nPlease contact administration immediately to resolve this matter.",
                notification_type='URGENT'
            )
            
            escalation_count += 1
    
    return f"Processed {overstayed_bookings.count()} overstays, {escalation_count} escalations required."


@shared_task
def send_grace_period_reminder(booking_id):
    """
    Send reminder during grace period before move-out.
    Fires at 50% of grace period elapsed.
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if in grace period
        if booking.status != 'GRACE_PERIOD':
            return f"Booking {booking_id} not in grace period"
        
        # Send notification
        Notification.objects.create(
            user=booking.tenant,
            title='Grace Period Reminder',
            message=f"You are currently in your grace period which ends on {booking.grace_period_end.strftime('%B %d, %Y')}.\n\nPlease ensure you have arranged for your move-out and vacated the room by this date.\n\nProperty: {booking.accommodation_property.title}\nReference: {booking.reference_number}",
            notification_type='WARNING'
        )
        
        return f"Sent grace period reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def schedule_grace_period_reminder(booking_id):
    """
    Schedule grace period reminder at 50% of grace period duration.
    """
    from celery import current_app
    from datetime import timedelta
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        if not booking.grace_period_start or not booking.grace_period_end:
            return f"Booking {booking_id} has no grace period dates"
        
        now = timezone.now()
        grace_duration = (booking.grace_period_end - booking.grace_period_start).days
        reminder_at_50_percent = grace_duration // 2
        
        reminder_seconds = reminder_at_50_percent * 24 * 60 * 60
        
        if reminder_seconds > 0:
            current_app.send_task(
                'bookings.tasks.send_grace_period_reminder',
                args=[booking_id],
                countdown=reminder_seconds
            )
        
        return f"Scheduled grace period reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def check_grace_period_expiries():
    """
    Periodic task to check for grace period expirations and transition to overstay.
    Runs daily.
    """
    from accounts.models import Notification
    from .grace_period_service import GracePeriodService
    
    now = timezone.now()
    
    # Find bookings in grace period that have ended
    expired_grace_bookings = Booking.objects.filter(
        status='GRACE_PERIOD',
        grace_period_end__lte=now
    ).select_related('tenant', 'accommodation_property', 'assigned_room')
    
    count = 0
    
    for booking in expired_grace_bookings:
        # Transition to overstay
        grace_status = GracePeriodService.get_grace_period_status(booking)
        
        if grace_status['status'] == 'GRACE_PERIOD_ENDED':
            # Update booking status
            booking.status = 'OVERSTAY'
            booking.overstay_start = now
            booking.save()
            
            # Notify student
            Notification.objects.create(
                user=booking.tenant,
                title='GRACE PERIOD ENDED - OVERSTAY',
                message=f"Your grace period has ended. You are now in overstay status.\n\nProperty: {booking.accommodation_property.title}\nRoom: {booking.assigned_room.room_number if booking.assigned_room else 'N/A'}\n\nOverstay charges will begin accruing immediately.\nPlease contact administration to resolve this matter.",
                notification_type='URGENT'
            )
            
            count += 1
    
    return f"Processed {count} grace period expirations to overstay."


@shared_task
def send_semester2_return_reminder(booking_id):
    """
    Send reminder for Semester 2 return date.
    Fires 3 days before return date.
    """
    from accounts.models import Notification
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if booking has split stay
        if booking.stay_structure != 'split_stay' or not booking.semester_2_start_date:
            return f"Booking {booking_id} does not have split stay"
        
        # Send notification
        Notification.objects.create(
            user=booking.tenant,
            title='Semester 2 Return in 3 Days',
            message=f"Your Semester 2 return date is {booking.semester_2_start_date.strftime('%B %d, %Y')}.\n\nPlease ensure you are prepared to return to your accommodation.\n\nProperty: {booking.accommodation_property.title}\nReference: {booking.reference_number}",
            notification_type='INFO'
        )
        
        return f"Sent Semester 2 return reminder for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"


@shared_task
def schedule_semester2_reminders(booking_id):
    """
    Schedule Semester 2 return reminders at 7 days and 3 days before return.
    """
    from celery import current_app
    from datetime import timedelta
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        if not booking.semester_2_start_date:
            return f"Booking {booking_id} has no Semester 2 start date"
        
        now = timezone.now()
        return_date = booking.semester_2_start_date
        
        # 7 days before
        days_7 = (return_date - now - timedelta(days=7)).total_seconds()
        if days_7 > 0:
            current_app.send_task(
                'bookings.tasks.send_vacation_reserve_reminder',
                args=[booking_id],
                countdown=days_7
            )
        
        # 3 days before
        days_3 = (return_date - now - timedelta(days=3)).total_seconds()
        if days_3 > 0:
            current_app.send_task(
                'bookings.tasks.send_semester2_return_reminder',
                args=[booking_id],
                countdown=days_3
            )
        
        return f"Scheduled Semester 2 reminders for booking {booking_id}"
    
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"
