"""
Grace Period Service

Handles grace period calculations and notifications as per Part 8.
The grace period is a 7-day window after the paid period ends.
"""

from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from .constants import (
    RoomStatus,
    DEFAULT_GRACE_PERIOD_DAYS,
    MIN_GRACE_PERIOD_DAYS,
    MAX_GRACE_PERIOD_DAYS,
    GRACE_PERIOD_REMINDER_DAYS,
    PRE_EXPIRY_REMINDER_WEEKS,
    PRE_EXPIRY_REMINDER_DAYS
)


class GracePeriodService:
    """Service for grace period management"""
    
    @staticmethod
    def calculate_grace_period(move_out_date, grace_period_days=None):
        """
        Calculate grace period dates
        
        Args:
            move_out_date: The end of the paid period
            grace_period_days: Number of grace days (default from pricing)
        
        Returns:
            dict with grace_period_start, grace_period_end, slot_available_date
        """
        if grace_period_days is None:
            grace_period_days = DEFAULT_GRACE_PERIOD_DAYS
        
        # Validate grace period days
        if grace_period_days < MIN_GRACE_PERIOD_DAYS or grace_period_days > MAX_GRACE_PERIOD_DAYS:
            raise ValidationError(
                f"Grace period must be between {MIN_GRACE_PERIOD_DAYS} and {MAX_GRACE_PERIOD_DAYS} days"
            )
        
        grace_period_start = move_out_date + timedelta(days=1)
        grace_period_end = grace_period_start + timedelta(days=grace_period_days - 1)
        slot_available_date = grace_period_end + timedelta(days=1)
        
        return {
            'grace_period_start': grace_period_start,
            'grace_period_end': grace_period_end,
            'grace_period_days': grace_period_days,
            'slot_available_date': slot_available_date
        }
    
    @staticmethod
    def get_grace_period_status(booking, current_date=None):
        """
        Get current grace period status for a booking
        
        Returns:
            dict with status, days_remaining, in_grace_period, etc.
        """
        if current_date is None:
            current_date = date.today()
        
        move_out_date = booking.move_out_date
        
        # Get grace period configuration from pricing
        if booking.room_type:
            pricing = booking.room_type.pricing_models.filter(
                payment_type__icontains=booking.billing_model.lower()
            ).first()
            grace_period_days = pricing.grace_period_days if pricing else DEFAULT_GRACE_PERIOD_DAYS
        else:
            grace_period_days = DEFAULT_GRACE_PERIOD_DAYS
        
        grace_info = GracePeriodService.calculate_grace_period(move_out_date, grace_period_days)
        
        # Determine status
        if current_date < move_out_date:
            return {
                'status': 'ACTIVE',
                'in_grace_period': False,
                'days_remaining': (move_out_date - current_date).days,
                'grace_period_start': grace_info['grace_period_start'],
                'grace_period_end': grace_info['grace_period_end'],
                'slot_available_date': grace_info['slot_available_date']
            }
        
        elif current_date <= grace_info['grace_period_end']:
            days_in_grace = (current_date - grace_info['grace_period_start']).days + 1
            days_remaining = (grace_info['grace_period_end'] - current_date).days
            return {
                'status': 'GRACE_PERIOD',
                'in_grace_period': True,
                'days_in_grace': days_in_grace,
                'days_remaining': days_remaining,
                'grace_period_start': grace_info['grace_period_start'],
                'grace_period_end': grace_info['grace_period_end'],
                'slot_available_date': grace_info['slot_available_date']
            }
        
        else:
            days_past_grace = (current_date - grace_info['grace_period_end']).days
            return {
                'status': 'GRACE_PERIOD_ENDED',
                'in_grace_period': False,
                'days_past_grace': days_past_grace,
                'grace_period_end': grace_info['grace_period_end'],
                'slot_available_date': grace_info['slot_available_date']
            }
    
    @staticmethod
    def should_send_reminder(booking, current_date=None):
        """
        Check if a grace period reminder should be sent today
        
        Returns:
            bool or reminder_type if reminder should be sent
        """
        if current_date is None:
            current_date = date.today()
        
        grace_status = GracePeriodService.get_grace_period_status(booking, current_date)
        
        if not grace_status['in_grace_period']:
            return None
        
        days_in_grace = grace_status['days_in_grace']
        
        # Check if today is a reminder day (Day 3 or Day 6)
        if days_in_grace in GRACE_PERIOD_REMINDER_DAYS:
            return f'GRACE_PERIOD_DAY_{days_in_grace}'
        
        return None
    
    @staticmethod
    def get_pre_expiry_reminder_schedule(booking):
        """
        Get the pre-expiry reminder schedule for a booking
        
        Returns:
            list of reminder dates
        """
        move_out_date = booking.move_out_date
        reminders = []
        
        # Weekly reminders (4, 2, 1 weeks before)
        for weeks_before in PRE_EXPIRY_REMINDER_WEEKS:
            reminder_date = move_out_date - timedelta(weeks=weeks_before)
            reminders.append({
                'date': reminder_date,
                'type': f'PRE_EXPIRY_{weeks_before}_WEEKS',
                'weeks_before': weeks_before
            })
        
        # Daily reminders (3 days before, day of expiry)
        for days_before in PRE_EXPIRY_REMINDER_DAYS:
            if days_before == 0:
                reminder_date = move_out_date
            else:
                reminder_date = move_out_date - timedelta(days=days_before)
            reminders.append({
                'date': reminder_date,
                'type': f'PRE_EXPIRY_{days_before}_DAYS' if days_before > 0 else 'PRE_EXPIRY_DAY_OF',
                'days_before': days_before
            })
        
        # Grace period reminders
        grace_period_days = 7  # Default, should get from pricing
        grace_period_start = move_out_date + timedelta(days=1)
        
        for day in GRACE_PERIOD_REMINDER_DAYS:
            reminder_date = grace_period_start + timedelta(days=day - 1)
            reminders.append({
                'date': reminder_date,
                'type': f'GRACE_PERIOD_DAY_{day}',
                'day_of_grace': day
            })
        
        return sorted(reminders, key=lambda x: x['date'])
    
    @staticmethod
    def check_rebooking_eligibility(booking, current_date=None):
        """
        Check if student is eligible for priority rebooking during grace period
        
        Returns:
            dict with eligibility status and information
        """
        if current_date is None:
            current_date = date.today()
        
        grace_status = GracePeriodService.get_grace_period_status(booking, current_date)
        
        if not grace_status['in_grace_period']:
            return {
                'eligible': False,
                'reason': 'Not in grace period',
                'status': grace_status['status']
            }
        
        # Check if room is still available
        room_type = booking.room_type
        if room_type and room_type.available_slots > 0:
            return {
                'eligible': True,
                'reason': 'In grace period and room available',
                'days_remaining': grace_status['days_remaining'],
                'room_available': True,
                'slot_available_date': grace_status['slot_available_date']
            }
        else:
            return {
                'eligible': False,
                'reason': 'Room not available',
                'days_remaining': grace_status['days_remaining'],
                'room_available': False
            }
    
    @staticmethod
    def calculate_practical_checkout_window(semester1_end):
        """
        Calculate the 48-hour practical checkout window for split stay (Part 8.3)
        
        Args:
            semester1_end: End date of Semester 1
        
        Returns:
            dict with practical_checkout_start, practical_checkout_end
        """
        from .constants import PRACTICAL_CHECKOUT_HOURS
        
        practical_checkout_start = semester1_end + timedelta(days=1)
        practical_checkout_end = practical_checkout_start + timedelta(hours=PRACTICAL_CHECKOUT_HOURS)
        
        return {
            'practical_checkout_start': practical_checkout_start,
            'practical_checkout_end': practical_checkout_end,
            'duration_hours': PRACTICAL_CHECKOUT_HOURS
        }
