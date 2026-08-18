"""
Duration Selection Service

Handles duration selection, date calculations, and pricing for different billing models:
- Semester-Based Billing
- Monthly-Based Billing
- Annual-Based Billing
- Academic Year (Combined Two Semesters)

Calculates move-out dates, grace periods, vacation reserves, and pricing totals.
"""

from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta, date
from django.utils import timezone
from properties.models import RoomType, UnitType, RoomTypePricing, UnitTypePricing


class DurationCalculationResult:
    """Result of duration calculation"""
    
    def __init__(self, success: bool, data: Dict = None, message: str = ""):
        self.success = success
        self.data = data or {}
        self.message = message
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message
        }


class DurationService:
    """Service for duration calculations and pricing"""
    
    SEMESTER_WEEKS = 17
    SEMESTER_DAYS = 119
    GRACE_PERIOD_DAYS = 7
    PRACTICAL_CHECKOUT_HOURS = 48
    
    @staticmethod
    def get_billing_model(room_type_id: Optional[int], unit_type_id: Optional[int]) -> Optional[Dict]:
        """Get the billing model configuration for a room type or unit type"""
        if room_type_id:
            room_type = RoomType.objects.filter(id=room_type_id).first()
            if room_type:
                pricing = room_type.pricing_models.first()
                model_type = (room_type.billing_model or 'SEMESTER_BASED').replace('_BASED', '')
                if pricing:
                    academic_price = pricing.academic_year_price
                    if academic_price is None:
                        academic_price = (pricing.semester_price * 2) if pricing.semester_price else 0
                        
                    return {
                        'type': model_type,
                        'semester_price': pricing.semester_price or 4500,
                        'monthly_price': pricing.monthly_price or 800,
                        'yearly_price': pricing.yearly_price or 8000,
                        'academic_year_price': academic_price or 9000,
                        'minimum_months': pricing.min_months or 1,
                    }
                else:
                    return {
                        'type': model_type,
                        'semester_price': 4500,
                        'monthly_price': 800,
                        'yearly_price': 8000,
                        'academic_year_price': 9000,
                        'minimum_months': 1,
                    }
        
        elif unit_type_id:
            unit_type = UnitType.objects.filter(id=unit_type_id).first()
            if unit_type:
                pricing = unit_type.pricing_models.first()
                model_type = (unit_type.billing_model or 'SEMESTER_BASED').replace('_BASED', '')
                if pricing:
                    academic_price = pricing.academic_year_price
                    if academic_price is None:
                        academic_price = (pricing.semester_price * 2) if pricing.semester_price else 0
                        
                    return {
                        'type': model_type,
                        'semester_price': pricing.semester_price or 4500,
                        'monthly_price': pricing.monthly_price or 800,
                        'yearly_price': pricing.yearly_price or 8000,
                        'academic_year_price': academic_price or 9000,
                        'minimum_months': pricing.min_months or 1,
                    }
                else:
                    return {
                        'type': model_type,
                        'semester_price': 4500,
                        'monthly_price': 800,
                        'yearly_price': 8000,
                        'academic_year_price': 9000,
                        'minimum_months': 1,
                    }
        
        # General default fallback if neither room_type nor unit_type could be found
        return {
            'type': 'SEMESTER',
            'semester_price': 4500,
            'monthly_price': 800,
            'yearly_price': 8000,
            'academic_year_price': 9000,
            'minimum_months': 1,
        }
    
    @staticmethod
    def calculate_semester_duration(
        move_in_date: date,
        num_semesters: int,
        price_per_semester: float
    ) -> DurationCalculationResult:
        """Calculate duration for semester-based billing"""
        if num_semesters < 1:
            return DurationCalculationResult(
                success=False,
                message="At least 1 semester is required"
            )
        
        total_days = num_semesters * DurationService.SEMESTER_DAYS
        total_weeks = num_semesters * DurationService.SEMESTER_WEEKS
        total_price = num_semesters * price_per_semester
        
        # Final semester end = move_in + (num_semesters × 17 weeks)
        semester_end = move_in_date + timedelta(days=DurationService.SEMESTER_DAYS * num_semesters)
        # Grace period applies after the last semester ends
        grace_period_start = semester_end + timedelta(days=1)
        grace_period_end = semester_end + timedelta(days=DurationService.GRACE_PERIOD_DAYS)
        room_opens_to_others = grace_period_end + timedelta(days=1)
        
        return DurationCalculationResult(
            success=True,
            data={
                'move_in_date': move_in_date,
                # move_out_date is the canonical key used in submit_duration
                'move_out_date': semester_end,
                'semester_end_date': semester_end,
                'grace_period_start': grace_period_start,
                'grace_period_end': grace_period_end,
                'room_opens_to_others': room_opens_to_others,
                'num_semesters': num_semesters,
                'total_days': total_days,
                'total_weeks': total_weeks,
                'total_months': round(total_days / 30, 1),
                'price_per_semester': price_per_semester,
                'total_price': total_price,
                'billing_model': 'SEMESTER',
            }
        )
    
    @staticmethod
    def calculate_monthly_duration(
        move_in_date: date,
        num_months: int,
        price_per_month: float,
        minimum_months: int = 2
    ) -> DurationCalculationResult:
        """Calculate duration for monthly-based billing"""
        if num_months < minimum_months:
            return DurationCalculationResult(
                success=False,
                message=f"Minimum stay is {minimum_months} months"
            )
        
        total_price = num_months * price_per_month
        
        # Use exactly 30 days per month — consistent with DAYS_PER_MONTH constant
        total_days = num_months * 30
        move_out_date = move_in_date + timedelta(days=total_days)
        
        grace_period_start = move_out_date + timedelta(days=1)
        grace_period_end = move_out_date + timedelta(days=DurationService.GRACE_PERIOD_DAYS)
        room_opens_to_others = grace_period_end + timedelta(days=1)
        
        return DurationCalculationResult(
            success=True,
            data={
                'move_in_date': move_in_date,
                'move_out_date': move_out_date,
                'grace_period_start': grace_period_start,
                'grace_period_end': grace_period_end,
                'room_opens_to_others': room_opens_to_others,
                'num_months': num_months,
                'total_days': total_days,
                'price_per_month': price_per_month,
                'total_price': total_price,
                'billing_model': 'MONTHLY',
            }
        )
    
    @staticmethod
    def calculate_annual_duration(
        move_in_date: date,
        num_years: int,
        price_per_year: float
    ) -> DurationCalculationResult:
        """Calculate duration for annual-based billing"""
        if num_years < 1:
            return DurationCalculationResult(
                success=False,
                message="At least 1 year is required"
            )
        
        total_days = num_years * 364  # 52 weeks * 7 days
        total_weeks = num_years * 52
        total_price = num_years * price_per_year
        
        # Apply discount for 2+ years
        if num_years >= 2:
            discount = 0.0625  # 6.25% discount (GH₵ 8,000 * 2 = 16,000, actual = 15,000)
            total_price = total_price * (1 - discount)
        
        move_out_date = move_in_date + timedelta(days=total_days)
        grace_period_end = move_out_date + timedelta(days=DurationService.GRACE_PERIOD_DAYS)
        room_opens_to_others = grace_period_end + timedelta(days=1)
        
        return DurationCalculationResult(
            success=True,
            data={
                'move_in_date': move_in_date,
                'move_out_date': move_out_date,
                'grace_period_start': move_out_date + timedelta(days=1),
                'grace_period_end': grace_period_end,
                'room_opens_to_others': room_opens_to_others,
                'num_years': num_years,
                'total_days': total_days,
                'total_weeks': total_weeks,
                'price_per_year': price_per_year,
                'total_price': total_price,
                'discount_applied': num_years >= 2,
                'billing_model': 'ANNUAL',
            }
        )
    
    @staticmethod
    def calculate_academic_year_duration(
        move_in_date: date,
        price_per_semester: float,
        academic_year_price: float
    ) -> DurationCalculationResult:
        """Calculate duration for academic year (combined two semesters)"""
        # Academic year = 2 semesters (34 weeks)
        total_semesters = 2
        total_days = total_semesters * DurationService.SEMESTER_DAYS
        total_weeks = total_semesters * DurationService.SEMESTER_WEEKS
        
        price_per_semester = price_per_semester or 0
        academic_year_price = academic_year_price or (price_per_semester * total_semesters)
        
        individual_price = total_semesters * price_per_semester
        savings = individual_price - academic_year_price
        
        semester1_end = move_in_date + timedelta(days=DurationService.SEMESTER_DAYS)
        semester2_start = semester1_end + timedelta(days=1)  # Default continuous
        semester2_end = semester2_start + timedelta(days=DurationService.SEMESTER_DAYS)
        
        grace_period_start = semester2_end + timedelta(days=1)
        grace_period_end = semester2_end + timedelta(days=DurationService.GRACE_PERIOD_DAYS)
        room_opens_to_others = grace_period_end + timedelta(days=1)
        
        return DurationCalculationResult(
            success=True,
            data={
                'move_in_date': move_in_date,
                # move_out_date is the canonical final date used for booking storage
                'move_out_date': semester2_end,
                'semester1_end_date': semester1_end,
                'semester2_start_date': semester2_start,
                'semester2_end_date': semester2_end,
                'grace_period_start': grace_period_start,
                'grace_period_end': grace_period_end,
                'room_opens_to_others': room_opens_to_others,
                'num_semesters': total_semesters,
                'total_semesters': total_semesters,
                'total_days': total_days,
                'total_weeks': total_weeks,
                'individual_price': individual_price,
                'academic_year_price': academic_year_price,
                'savings': savings,
                'total_price': academic_year_price,
                'billing_model': 'ACADEMIC_YEAR',
                'structure': 'CONTINUOUS',  # Default, can be changed to SPLIT
            }
        )
    
    @staticmethod
    def calculate_split_stay(
        move_in_date: date,
        semester2_start_date: date,
        price_per_semester: float
    ) -> DurationCalculationResult:
        """Calculate duration for split stay with vacation gap"""
        semester1_end = move_in_date + timedelta(days=DurationService.SEMESTER_DAYS)
        practical_checkout = semester1_end + timedelta(hours=DurationService.PRACTICAL_CHECKOUT_HOURS)
        
        vacation_reserve_start = practical_checkout + timedelta(days=1)
        vacation_reserve_end = semester2_start_date - timedelta(days=1)
        
        semester2_end = semester2_start_date + timedelta(days=DurationService.SEMESTER_DAYS)
        total_days = DurationService.SEMESTER_DAYS * 2  # Billed days (no vacation)
        grace_period_start = semester2_end + timedelta(days=1)
        grace_period_end = semester2_end + timedelta(days=DurationService.GRACE_PERIOD_DAYS)
        room_opens_to_others = grace_period_end + timedelta(days=1)
        
        total_price = 2 * price_per_semester  # Only charged for semesters, not vacation
        
        return DurationCalculationResult(
            success=True,
            data={
                'move_in_date': move_in_date,
                # move_out_date is the canonical final calendar date
                'move_out_date': semester2_end,
                'semester1_end_date': semester1_end,
                'practical_checkout_start': semester1_end + timedelta(days=1),
                'practical_checkout_end': practical_checkout,
                'vacation_start_date': vacation_reserve_start,
                'vacation_end_date': vacation_reserve_end,
                'vacation_reserve_start': vacation_reserve_start,
                'vacation_reserve_end': vacation_reserve_end,
                'semester2_start_date': semester2_start_date,
                'semester2_end_date': semester2_end,
                'grace_period_start': grace_period_start,
                'grace_period_end': grace_period_end,
                'room_opens_to_others': room_opens_to_others,
                'num_semesters': 2,
                'total_semesters': 2,
                'total_days': total_days,
                'total_price': total_price,
                'vacation_charge': 0,
                'billing_model': 'ACADEMIC_YEAR',
                'structure': 'SPLIT',
            }
        )
    
    @staticmethod
    def calculate_duration(
        billing_model: str,
        move_in_date: date,
        duration_value: int,
        pricing_data: Dict,
        structure: str = 'CONTINUOUS',
        semester2_start_date: Optional[date] = None
    ) -> DurationCalculationResult:
        """
        Main calculation method that routes to appropriate calculation based on billing model
        """
        if billing_model == 'SEMESTER':
            return DurationService.calculate_semester_duration(
                move_in_date=move_in_date,
                num_semesters=duration_value,
                price_per_semester=pricing_data.get('semester_price', 0)
            )
        
        elif billing_model == 'MONTHLY':
            return DurationService.calculate_monthly_duration(
                move_in_date=move_in_date,
                num_months=duration_value,
                price_per_month=pricing_data.get('monthly_price', 0),
                minimum_months=pricing_data.get('minimum_months', 2)
            )
        
        elif billing_model == 'ANNUAL':
            return DurationService.calculate_annual_duration(
                move_in_date=move_in_date,
                num_years=duration_value,
                price_per_year=pricing_data.get('yearly_price', 0)
            )
        
        elif billing_model == 'ACADEMIC_YEAR':
            if structure == 'SPLIT' and semester2_start_date:
                return DurationService.calculate_split_stay(
                    move_in_date=move_in_date,
                    semester2_start_date=semester2_start_date,
                    price_per_semester=pricing_data.get('semester_price', 0)
                )
            else:
                return DurationService.calculate_academic_year_duration(
                    move_in_date=move_in_date,
                    price_per_semester=pricing_data.get('semester_price', 0),
                    academic_year_price=pricing_data.get('academic_year_price', 0)
                )
        
        return DurationCalculationResult(
            success=False,
            message=f"Unknown billing model: {billing_model}"
        )
