"""
Overstay Service

Handles overstay calculations and management as per Part 9.
Overstay begins on day 8 after the paid period ends (after grace period).
"""

from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from .constants import (
    RoomStatus,
    SEMESTER_DAYS,
    DAYS_PER_YEAR,
    DEFAULT_OVERSTAY_MULTIPLIER,
    MIN_OVERSTAY_MULTIPLIER,
    MAX_OVERSTAY_MULTIPLIER,
    OVERSTAY_ESCALATION_DAYS
)
from .grace_period_service import GracePeriodService


class OverstayService:
    """Service for overstay calculation and management"""
    
    @staticmethod
    def calculate_normal_daily_rate(pricing_data, billing_model):
        """
        Calculate the normal daily rate for overstay calculation
        
        Formula: Normal daily rate = Price ÷ total paid days
        
        Args:
            pricing_data: Pricing information
            billing_model: The billing model used
        
        Returns:
            Decimal: Normal daily rate
        """
        if billing_model == 'SEMESTER_BASED':
            semester_price = pricing_data.get('semester_price', Decimal('0'))
            return semester_price / Decimal(SEMESTER_DAYS)
        
        elif billing_model == 'MONTHLY_BASED':
            monthly_price = pricing_data.get('monthly_price', Decimal('0'))
            return monthly_price / Decimal(30)  # 30 days per month
        
        elif billing_model == 'ANNUAL_BASED':
            yearly_price = pricing_data.get('yearly_price', Decimal('0'))
            return yearly_price / Decimal(DAYS_PER_YEAR)
        
        elif billing_model == 'ACADEMIC_YEAR':
            academic_year_price = pricing_data.get('academic_year_price')
            semester_price = pricing_data.get('semester_price', Decimal('0'))
            
            if academic_year_price:
                total_price = academic_year_price
            else:
                total_price = semester_price * 2 * Decimal('0.9')
            
            return total_price / Decimal(SEMESTER_DAYS * 2)
        
        else:
            raise ValidationError(f"Unknown billing model: {billing_model}")
    
    @staticmethod
    def calculate_overstay_daily_rate(normal_daily_rate, multiplier=None):
        """
        Calculate overstay daily rate
        
        Formula: Overstay daily rate = Normal daily rate × multiplier
        
        Args:
            normal_daily_rate: The normal daily rate
            multiplier: Overstay multiplier (default 1.5)
        
        Returns:
            Decimal: Overstay daily rate
        """
        if multiplier is None:
            multiplier = DEFAULT_OVERSTAY_MULTIPLIER
        
        # Validate multiplier
        if multiplier < MIN_OVERSTAY_MULTIPLIER or multiplier > MAX_OVERSTAY_MULTIPLIER:
            raise ValidationError(
                f"Overstay multiplier must be between {MIN_OVERSTAY_MULTIPLIER} and {MAX_OVERSTAY_MULTIPLIER}"
            )
        
        return normal_daily_rate * Decimal(str(multiplier))
    
    @staticmethod
    def get_overstay_status(booking, current_date=None):
        """
        Get current overstay status for a booking
        
        Returns:
            dict with overstay status, days, charges, etc.
        """
        if current_date is None:
            current_date = date.today()
        
        move_out_date = booking.move_out_date
        
        # Get grace period info
        grace_status = GracePeriodService.get_grace_period_status(booking, current_date)
        
        # If still in grace period or before, no overstay
        if grace_status['status'] in ['ACTIVE', 'GRACE_PERIOD']:
            return {
                'in_overstay': False,
                'status': 'NOT_IN_OVERSTAY',
                'grace_status': grace_status['status']
            }
        
        # Calculate overstay start date (day after grace period ends)
        overstay_start_date = grace_status['slot_available_date']
        
        if current_date < overstay_start_date:
            return {
                'in_overstay': False,
                'status': 'NOT_IN_OVERSTAY',
                'grace_status': grace_status['status']
            }
        
        # Calculate days in overstay
        days_in_overstay = (current_date - overstay_start_date).days + 1
        
        # Get pricing configuration
        if booking.room_type:
            pricing = booking.room_type.pricing_models.filter(
                payment_type__icontains=booking.billing_model.lower()
            ).first()
            
            if pricing:
                normal_daily_rate = OverstayService.calculate_normal_daily_rate(
                    {
                        'semester_price': pricing.semester_price,
                        'monthly_price': pricing.monthly_price,
                        'yearly_price': pricing.yearly_price,
                        'academic_year_price': pricing.academic_year_price
                    },
                    booking.billing_model
                )
                multiplier = pricing.overstay_multiplier
            else:
                normal_daily_rate = Decimal('0')
                multiplier = DEFAULT_OVERSTAY_MULTIPLIER
        else:
            normal_daily_rate = Decimal('0')
            multiplier = DEFAULT_OVERSTAY_MULTIPLIER
        
        overstay_daily_rate = OverstayService.calculate_overstay_daily_rate(
            normal_daily_rate,
            multiplier
        )
        
        # Calculate total overstay charge
        total_charge = overstay_daily_rate * days_in_overstay
        
        # Determine overstay stage
        if days_in_overstay <= 7:
            stage = 'EARLY_OVERSTAY'
            escalated = False
        elif days_in_overstay >= OVERSTAY_ESCALATION_DAYS:
            stage = 'ESCALATED_OVERSTAY'
            escalated = True
        else:
            stage = 'EARLY_OVERSTAY'
            escalated = False
        
        return {
            'in_overstay': True,
            'status': stage,
            'escalated': escalated,
            'overstay_start_date': overstay_start_date,
            'days_in_overstay': days_in_overstay,
            'normal_daily_rate': normal_daily_rate,
            'overstay_multiplier': multiplier,
            'overstay_daily_rate': overstay_daily_rate,
            'total_charge': total_charge,
            'grace_period_end': grace_status['grace_period_end'],
            'slot_available_date': grace_status['slot_available_date']
        }
    
    @staticmethod
    def should_send_overstay_notification(booking, current_date=None):
        """
        Check if an overstay notification should be sent today
        
        Returns:
            str or None: Notification type if should send
        """
        if current_date is None:
            current_date = date.today()
        
        overstay_status = OverstayService.get_overstay_status(booking, current_date)
        
        if not overstay_status['in_overstay']:
            return None
        
        days_in_overstay = overstay_status['days_in_overstay']
        
        # Daily notifications during overstay
        if days_in_overstay >= 1:
            if overstay_status['escalated']:
                return f'ESCALATED_OVERSTAY_DAY_{days_in_overstay}'
            else:
                return f'OVERSTAY_DAY_{days_in_overstay}'
        
        return None
    
    @staticmethod
    def check_escalation_required(booking, current_date=None):
        """
        Check if overstay escalation is required (Day 15)
        
        Returns:
            dict with escalation status
        """
        if current_date is None:
            current_date = date.today()
        
        overstay_status = OverstayService.get_overstay_status(booking, current_date)
        
        if not overstay_status['in_overstay']:
            return {
                'escalation_required': False,
                'reason': 'Not in overstay'
            }
        
        if overstay_status['escalated']:
            return {
                'escalation_required': True,
                'days_in_overstay': overstay_status['days_in_overstay'],
                'total_charge': overstay_status['total_charge'],
                'action': 'ADMIN_ESCALATION',
                'reason': f'Overstay exceeded {OVERSTAY_ESCALATION_DAYS} days'
            }
        
        return {
            'escalation_required': False,
            'days_in_overstay': overstay_status['days_in_overstay'],
            'reason': 'Below escalation threshold'
        }
    
    @staticmethod
    def apply_overstay_charge(booking, days_to_charge=None):
        """
        Apply overstay charge to booking
        
        Args:
            booking: The booking instance
            days_to_charge: Number of days to charge (default: all days)
        
        Returns:
            Decimal: Total charge applied
        """
        overstay_status = OverstayService.get_overstay_status(booking)
        
        if not overstay_status['in_overstay']:
            return Decimal('0')
        
        if days_to_charge is None:
            days_to_charge = overstay_status['days_in_overstay']
        
        charge = overstay_status['overstay_daily_rate'] * days_to_charge
        
        # This would typically create a payment record or add to booking
        # For now, return the calculated charge
        return charge
    
    @staticmethod
    def waive_overstay_charges(booking, reason, waived_by):
        """
        Waive overstay charges for special circumstances (admin action)
        
        Args:
            booking: The booking instance
            reason: Reason for waiver
            waived_by: Admin user who waived the charges
        
        Returns:
            dict with waiver information
        """
        overstay_status = OverstayService.get_overstay_status(booking)
        
        if not overstay_status['in_overstay']:
            return {
                'success': False,
                'reason': 'No overstay charges to waive'
            }
        
        # This would typically update payment records
        return {
            'success': True,
            'total_waived': overstay_status['total_charge'],
            'reason': reason,
            'waived_by': waived_by,
            'waived_at': date.today()
        }
