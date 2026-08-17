"""
Vacation Reserve Service

Handles vacation reserve management as per Part 10.
The Vacation Reserve applies to Option B (Split Stay) bookings.
"""

from datetime import date, timedelta
from django.core.exceptions import ValidationError

from .constants import (
    RoomStatus,
    SemesterStructure,
    SEMESTER_DAYS,
    VACATION_RESERVE_NO_RETURN_ESCALATION_DAYS
)
from .grace_period_service import GracePeriodService


class VacationReserveService:
    """Service for vacation reserve management"""
    
    @staticmethod
    def calculate_vacation_reserve_period(semester1_end, semester2_start):
        """
        Calculate vacation reserve period
        
        Args:
            semester1_end: End date of Semester 1
            semester2_start: Start date of Semester 2
        
        Returns:
            dict with vacation period details
        """
        vacation_start = semester1_end + timedelta(days=1)
        vacation_end = semester2_start - timedelta(days=1)
        vacation_days = (vacation_end - vacation_start).days + 1
        
        return {
            'vacation_start': vacation_start,
            'vacation_end': vacation_end,
            'vacation_days': vacation_days,
            'semester1_end': semester1_end,
            'semester2_start': semester2_start
        }
    
    @staticmethod
    def get_vacation_reserve_status(booking, current_date=None):
        """
        Get current vacation reserve status for a booking
        
        Returns:
            dict with vacation reserve status, days remaining, etc.
        """
        if current_date is None:
            current_date = date.today()
        
        # Only applies to split stay bookings
        if booking.semester_structure != SemesterStructure.SPLIT_STAY.value:
            return {
                'in_vacation_reserve': False,
                'reason': 'Not a split stay booking'
            }
        
        if not booking.vacation_gap_start or not booking.vacation_gap_end:
            return {
                'in_vacation_reserve': False,
                'reason': 'Vacation gap dates not set'
            }
        
        vacation_info = VacationReserveService.calculate_vacation_reserve_period(
            booking.vacation_gap_start,
            booking.vacation_gap_end
        )
        
        # Check if currently in vacation reserve
        if vacation_info['vacation_start'] <= current_date <= vacation_info['vacation_end']:
            days_remaining = (vacation_info['vacation_end'] - current_date).days
            days_elapsed = (current_date - vacation_info['vacation_start']).days
            
            return {
                'in_vacation_reserve': True,
                'status': 'ACTIVE',
                'vacation_start': vacation_info['vacation_start'],
                'vacation_end': vacation_info['vacation_end'],
                'vacation_days': vacation_info['vacation_days'],
                'days_remaining': days_remaining,
                'days_elapsed': days_elapsed,
                'semester2_start': booking.vacation_gap_end,
                'semester2_end': booking.vacation_gap_end + timedelta(days=SEMESTER_DAYS)
            }
        
        elif current_date < vacation_info['vacation_start']:
            days_until_vacation = (vacation_info['vacation_start'] - current_date).days
            return {
                'in_vacation_reserve': False,
                'status': 'UPCOMING',
                'days_until_vacation': days_until_vacation,
                'vacation_start': vacation_info['vacation_start'],
                'vacation_end': vacation_info['vacation_end']
            }
        
        else:
            days_past_vacation = (current_date - vacation_info['vacation_end']).days
            return {
                'in_vacation_reserve': False,
                'status': 'ENDED',
                'days_past_vacation': days_past_vacation,
                'vacation_end': vacation_info['vacation_end']
            }
    
    @staticmethod
    def update_semester2_date(booking, new_semester2_start, updated_by=None):
        """
        Update Semester 2 start date during vacation reserve
        
        Args:
            booking: The booking instance
            new_semester2_start: New Semester 2 start date
            updated_by: User who made the update (student or admin)
        
        Returns:
            dict with updated booking information
        """
        vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
        
        if not vacation_status['in_vacation_reserve'] and vacation_status['status'] != 'UPCOMING':
            raise ValidationError(
                "Semester 2 date can only be updated during vacation reserve period or before it starts"
            )
        
        old_semester2_start = booking.vacation_gap_end
        
        # Validate new date
        if new_semester2_start <= booking.vacation_gap_start:
            raise ValidationError("Semester 2 start must be after Semester 1 end")
        
        # Update booking
        booking.vacation_gap_end = new_semester2_start
        
        # Recalculate move-out date (Semester 2 end = S2 start + 17 weeks)
        # Always use SEMESTER_BASED with num_semesters=1 — S2 is always exactly 17 weeks
        # regardless of whether the original booking was Model A or Model D.
        from .billing_service import BillingService
        from .constants import BillingModel
        new_move_out = BillingService.calculate_move_out_date(
            new_semester2_start,
            BillingModel.SEMESTER_BASED.value,
            num_semesters=1
        )
        booking.move_out_date = new_move_out
        booking.save()
        
        # Log the change (would typically create a booking history entry)
        return {
            'success': True,
            'old_semester2_start': old_semester2_start,
            'new_semester2_start': new_semester2_start,
            'new_move_out_date': new_move_out,
            'updated_by': updated_by,
            'updated_at': date.today()
        }
    
    @staticmethod
    def cancel_semester2(booking, cancelled_by, reason=None):
        """
        Cancel Semester 2 during vacation reserve
        
        Args:
            booking: The booking instance
            cancelled_by: User who cancelled (student or admin)
            reason: Reason for cancellation
        
        Returns:
            dict with cancellation information
        """
        vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
        
        if not vacation_status['in_vacation_reserve']:
            raise ValidationError(
                "Semester 2 can only be cancelled during vacation reserve period"
            )
        
        # Calculate refund amount (Semester 2 price)
        semester2_price = booking.total_amount / 2  # Assuming equal split
        
        # Update booking to single semester
        # move_out_date for single-semester = end of Semester 1
        # = vacation_gap_start - 1 day (last paid day)
        semester1_end = booking.vacation_gap_start - timedelta(days=1)
        booking.num_semesters = 1
        booking.move_out_date = semester1_end
        booking.semester_structure = None
        booking.vacation_gap_start = None
        booking.vacation_gap_end = None
        booking.save()
        
        # Release room slot
        if booking.room_type:
            booking.room_type.available_slots += 1
            booking.room_type.save()
        
        return {
            'success': True,
            'refund_amount': semester2_price,
            'cancelled_by': cancelled_by,
            'reason': reason,
            'cancelled_at': date.today()
        }
    
    @staticmethod
    def check_no_return_escalation(booking, current_date=None):
        """
        Check if no-return escalation is required (Day 15 after Semester 2 start)
        
        Returns:
            dict with escalation status
        """
        if current_date is None:
            current_date = date.today()
        
        vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
        
        if vacation_status['status'] != 'ENDED':
            return {
                'escalation_required': False,
                'reason': 'Vacation reserve not ended yet'
            }
        
        # Read semester2_start directly from the booking record
        # (the status dict does not carry semester2_start when status=ENDED)
        semester2_start = booking.vacation_gap_end
        if not semester2_start:
            return {
                'escalation_required': False,
                'reason': 'No Semester 2 date recorded on booking'
            }
        days_past_semester2 = (current_date - semester2_start).days
        
        if days_past_semester2 >= VACATION_RESERVE_NO_RETURN_ESCALATION_DAYS:
            return {
                'escalation_required': True,
                'days_past_semester2': days_past_semester2,
                'action': 'ADMIN_REVIEW',
                'reason': f'Student has not returned {days_past_semester2} days after Semester 2 start'
            }
        
        return {
            'escalation_required': False,
            'days_past_semester2': days_past_semester2,
            'reason': 'Below escalation threshold'
        }
    
    @staticmethod
    def should_send_vacation_reminder(booking, current_date=None):
        """
        Check if a vacation reminder should be sent today
        
        Returns:
            str or None: Reminder type if should send
        """
        if current_date is None:
            current_date = date.today()
        
        vacation_status = VacationReserveService.get_vacation_reserve_status(booking)
        
        if not vacation_status['in_vacation_reserve']:
            return None
        
        semester2_start = vacation_status['semester2_start']
        days_until_return = (semester2_start - current_date).days
        
        # Reminder schedule: 3 weeks, 1 week, 2 days before
        if days_until_return == 21:  # 3 weeks
            return 'VACATION_RETURN_3_WEEKS'
        elif days_until_return == 7:  # 1 week
            return 'VACATION_RETURN_1_WEEK'
        elif days_until_return == 2:  # 2 days
            return 'VACATION_RETURN_2_DAYS'
        elif days_until_return == 0:  # Day of return
            return 'VACATION_RETURN_TODAY'
        
        return None
    
    @staticmethod
    def get_vacation_reserve_summary(booking):
        """
        Get complete vacation reserve summary for display
        
        Returns:
            dict with all vacation reserve information
        """
        if booking.semester_structure != SemesterStructure.SPLIT_STAY.value:
            return None
        
        vacation_info = VacationReserveService.calculate_vacation_reserve_period(
            booking.vacation_gap_start,
            booking.vacation_gap_end
        )
        
        semester1_end = booking.vacation_gap_start - timedelta(days=1)
        semester2_end = booking.vacation_gap_end + timedelta(days=SEMESTER_DAYS)
        
        return {
            'semester1_start': booking.move_in_date,
            'semester1_end': semester1_end,
            'semester1_duration_weeks': SEMESTER_DAYS // 7,
            'vacation_reserve_start': vacation_info['vacation_start'],
            'vacation_reserve_end': vacation_info['vacation_end'],
            'vacation_reserve_days': vacation_info['vacation_days'],
            'semester2_start': booking.vacation_gap_end,
            'semester2_end': semester2_end,
            'semester2_duration_weeks': SEMESTER_DAYS // 7,
            'total_duration_weeks': (SEMESTER_DAYS // 7) * 2,
            'room_locked': True,
            'no_charge_during_vacation': True
        }
