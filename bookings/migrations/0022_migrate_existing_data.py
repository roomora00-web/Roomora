"""
Data migration to populate new models from existing booking data.
This migration creates BillingAllocation, RoomAllocation, and ConsentRecord records
for existing bookings that don't have them yet.
"""

from django.db import migrations


def migrate_existing_bookings(apps, schema_editor):
    """Migrate existing booking data to new models."""
    Booking = apps.get_model('bookings', 'Booking')
    BillingAllocation = apps.get_model('bookings', 'BillingAllocation')
    RoomAllocation = apps.get_model('bookings', 'RoomAllocation')
    ConsentRecord = apps.get_model('bookings', 'ConsentRecord')
    
    # Migrate bookings to BillingAllocation
    for booking in Booking.objects.all():
        if not hasattr(booking, 'billing_allocation'):
            duration_params = {}
            if booking.num_semesters:
                duration_params['num_semesters'] = booking.num_semesters
            if booking.billing_model == 'MONTHLY_BASED':
                # Calculate months from dates if available
                if booking.move_in_date and booking.move_out_date:
                    from datetime import datetime, timedelta
                    days = (booking.move_out_date - booking.move_in_date).days
                    duration_params['num_months'] = max(1, round(days / 30))
            
            BillingAllocation.objects.create(
                booking=booking,
                billing_model=booking.billing_model or 'MONTHLY_BASED',
                num_semesters=booking.num_semesters,
                semester_structure=booking.semester_structure,
                vacation_gap_start=booking.vacation_gap_start,
                vacation_gap_end=booking.vacation_gap_end,
                semester1_end=booking.semester1_end,
                semester2_start=booking.semester2_start,
                semester2_end=booking.semester2_end,
                monthly_rent=booking.monthly_rent or 0,
                total_amount=booking.total_amount or 0,
                security_deposit=booking.security_deposit or 0,
            )
    
    # Migrate bookings to RoomAllocation
    for booking in Booking.objects.all():
        if not hasattr(booking, 'room_allocation'):
            occupancy_type = None
            if booking.room_type:
                occupancy_type = booking.room_type.occupancy_type
            
            RoomAllocation.objects.create(
                booking=booking,
                room_type=booking.room_type,
                unit_type=booking.unit_type,
                assigned_room=booking.assigned_room,
                occupancy_type=occupancy_type,
                allocation_status='CONFIRMED' if booking.assigned_room else 'RESERVED',
                confirmed_at=booking.created_at if booking.assigned_room else None,
            )
    
    # Migrate bookings to ConsentRecord for roommate matching bookings
    for booking in Booking.objects.filter(booking_type='ROOMMATE_MATCH'):
        if not hasattr(booking, 'new_consent_record'):
            consent_status = 'PENDING'
            if booking.user_consent and booking.roommate_consent:
                consent_status = 'BOTH_CONSENTED'
            elif booking.user_consent:
                consent_status = 'USER_CONSENTED'
            elif booking.roommate_consent:
                consent_status = 'ROOMMATE_CONSENTED'
            
            ConsentRecord.objects.create(
                booking=booking,
                user_consent=booking.user_consent or False,
                user_consent_date=booking.user_consent_date,
                user_consent_ip=booking.user_consent_ip,
                roommate=booking.roommate,
                roommate_consent=booking.roommate_consent or False,
                roommate_consent_date=booking.roommate_consent_date,
                roommate_consent_ip=booking.roommate_consent_ip,
                consent_deadline=booking.consent_timeout_date,
                consent_status=consent_status,
            )


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0021_billingallocation_bookingdraft_consentrecord_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_bookings),
    ]
