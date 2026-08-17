"""
Duration Selection Service

Handles duration selection logic for the student booking flow as per Part 3.
This service manages the duration selection screens for all four billing models.
"""

from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from .constants import (
    BillingModel, SemesterStructure,
    SEMESTER_WEEKS, SEMESTER_DAYS,
    ACADEMIC_YEAR_WEEKS, ACADEMIC_YEAR_DAYS,
    WEEKS_PER_YEAR, DAYS_PER_YEAR,
    DAYS_PER_MONTH,
    DEFAULT_MAX_SEMESTERS, DEFAULT_MIN_MONTHS, DEFAULT_MAX_MONTHS
)
from .billing_service import BillingService


class DurationSelectionService:
    """Service for handling duration selection in the booking flow"""
    
    @staticmethod
    def get_duration_options(billing_model, pricing_data):
        """
        Get available duration options based on billing model
        
        Returns a list of duration options with pricing information
        """
        if billing_model == BillingModel.SEMESTER_BASED.value:
            return DurationSelectionService._get_semester_options(pricing_data)
        
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            return DurationSelectionService._get_monthly_options(pricing_data)
        
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            return DurationSelectionService._get_annual_options(pricing_data)
        
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            return DurationSelectionService._get_academic_year_options(pricing_data)
        
        else:
            raise ValidationError(f"Unknown billing model: {billing_model}")
    
    @staticmethod
    def _get_semester_options(pricing_data):
        """Model A: Semester-Based options (1-3 semesters)"""
        semester_price = pricing_data.get('semester_price', Decimal('0'))
        max_semesters = pricing_data.get('max_semesters', DEFAULT_MAX_SEMESTERS)
        
        options = []
        for num_semesters in range(1, max_semesters + 1):
            total_price = semester_price * num_semesters
            total_weeks = num_semesters * SEMESTER_WEEKS
            total_days = num_semesters * SEMESTER_DAYS
            total_months = total_days / DAYS_PER_MONTH  # Approximate months
            
            options.append({
                'num_semesters': num_semesters,
                'total_weeks': total_weeks,
                'total_days': total_days,
                'total_months': round(total_months, 2),
                'price': total_price,
                'price_per_semester': semester_price,
                'requires_semester_structure': num_semesters >= 2
            })
        
        return options
    
    @staticmethod
    def _get_monthly_options(pricing_data):
        """Model B: Monthly-Based options"""
        monthly_price = pricing_data.get('monthly_price', Decimal('0'))
        min_months = pricing_data.get('min_months', DEFAULT_MIN_MONTHS)
        max_months = pricing_data.get('max_months', DEFAULT_MAX_MONTHS)
        
        options = []
        for num_months in range(min_months, max_months + 1):
            total_price = monthly_price * num_months
            total_days = num_months * DAYS_PER_MONTH
            
            options.append({
                'num_months': num_months,
                'total_days': total_days,
                'price': total_price,
                'price_per_month': monthly_price
            })
        
        return options
    
    @staticmethod
    def _get_annual_options(pricing_data):
        """Model C: Annual-Based options (1 or 2 years)"""
        yearly_price = pricing_data.get('yearly_price', Decimal('0'))
        two_years_price = pricing_data.get('two_years_price')
        allow_two_year = pricing_data.get('allow_two_year_advance', False)
        
        options = []
        
        # 1 year option
        options.append({
            'num_years': 1,
            'total_weeks': WEEKS_PER_YEAR,
            'total_days': DAYS_PER_YEAR,
            'price': yearly_price,
            'price_per_year': yearly_price
        })
        
        # 2 year option if allowed
        if allow_two_year and two_years_price:
            options.append({
                'num_years': 2,
                'total_weeks': WEEKS_PER_YEAR * 2,
                'total_days': DAYS_PER_YEAR * 2,
                'price': two_years_price,
                'price_per_year': two_years_price / 2,
                'discount': yearly_price * 2 - two_years_price
            })
        
        return options
    
    @staticmethod
    def _get_academic_year_options(pricing_data):
        """Model D: Academic Year (combined 2 semesters)"""
        semester_price = pricing_data.get('semester_price', Decimal('0'))
        academic_year_price = pricing_data.get('academic_year_price')
        
        # Calculate individual semester total
        individual_total = semester_price * 2
        
        # Use academic year price if set, otherwise calculate with default 10% discount
        if academic_year_price:
            combined_price = academic_year_price
            discount = individual_total - academic_year_price
        else:
            combined_price = individual_total * Decimal('0.9')
            discount = individual_total - combined_price
        
        return [{
            'num_semesters': 2,
            'total_weeks': ACADEMIC_YEAR_WEEKS,
            'total_days': ACADEMIC_YEAR_DAYS,
            'price': combined_price,
            'individual_semester_price': semester_price,
            'individual_total': individual_total,
            'discount': discount,
            'requires_semester_structure': True  # Always requires structure selection
        }]
    
    @staticmethod
    def validate_duration_selection(billing_model, duration_params, pricing_data):
        """
        Validate the duration selection against pricing configuration
        
        Args:
            billing_model: The selected billing model
            duration_params: dict with num_semesters, num_months, or num_years
            pricing_data: Pricing configuration from RoomTypePricing/UnitTypePricing
        
        Returns:
            dict with validated parameters and calculated totals
        """
        if billing_model == BillingModel.SEMESTER_BASED.value:
            num_semesters = duration_params.get('num_semesters')
            max_semesters = pricing_data.get('max_semesters', DEFAULT_MAX_SEMESTERS)
            
            if not num_semesters or num_semesters < 1 or num_semesters > max_semesters:
                raise ValidationError(
                    f"Number of semesters must be between 1 and {max_semesters}"
                )
            
            semester_price = pricing_data.get('semester_price', Decimal('0'))
            total_price = semester_price * num_semesters
            
            return {
                'num_semesters': num_semesters,
                'total_price': total_price,
                'requires_semester_structure': num_semesters >= 2
            }
        
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            num_months = duration_params.get('num_months')
            min_months = pricing_data.get('min_months', DEFAULT_MIN_MONTHS)
            max_months = pricing_data.get('max_months', DEFAULT_MAX_MONTHS)
            
            if not num_months or num_months < min_months or num_months > max_months:
                raise ValidationError(
                    f"Number of months must be between {min_months} and {max_months}"
                )
            
            monthly_price = pricing_data.get('monthly_price', Decimal('0'))
            total_price = monthly_price * num_months
            
            return {
                'num_months': num_months,
                'total_price': total_price,
                'requires_semester_structure': False
            }
        
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            num_years = duration_params.get('num_years')
            allow_two_year = pricing_data.get('allow_two_year_advance', False)
            
            if not num_years or num_years not in [1, 2]:
                raise ValidationError("Number of years must be 1 or 2")
            
            if num_years == 2 and not allow_two_year:
                raise ValidationError("2-year advance payment is not available for this room type")
            
            yearly_price = pricing_data.get('yearly_price', Decimal('0'))
            
            if num_years == 1:
                total_price = yearly_price
            else:
                two_years_price = pricing_data.get('two_years_price')
                if two_years_price:
                    total_price = two_years_price
                else:
                    total_price = yearly_price * 2
            
            return {
                'num_years': num_years,
                'total_price': total_price,
                'requires_semester_structure': False
            }
        
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            # Academic Year is always 2 semesters
            academic_year_price = pricing_data.get('academic_year_price')
            semester_price = pricing_data.get('semester_price', Decimal('0'))
            
            if academic_year_price:
                total_price = academic_year_price
            else:
                total_price = semester_price * 2 * Decimal('0.9')
            
            return {
                'num_semesters': 2,
                'total_price': total_price,
                'requires_semester_structure': True
            }
        
        else:
            raise ValidationError(f"Unknown billing model: {billing_model}")
    
    @staticmethod
    def calculate_booking_summary(move_in_date, billing_model, duration_params, semester_structure=None, vacation_gap_start=None, vacation_gap_end=None):
        """
        Calculate complete booking summary for display
        
        Returns a dict with all dates, pricing, and structure information
        """
        # Calculate move-out date
        move_out_date = BillingService.calculate_move_out_date(
            move_in_date,
            billing_model,
            **duration_params,
            semester_structure=semester_structure,
            vacation_gap_start=vacation_gap_start,
            vacation_gap_end=vacation_gap_end
        )
        
        summary = {
            'move_in_date': move_in_date,
            'move_out_date': move_out_date,
            'billing_model': billing_model,
            'semester_structure': semester_structure,
            'vacation_gap_start': vacation_gap_start,
            'vacation_gap_end': vacation_gap_end,
        }
        
        # Add semester-specific details
        if billing_model in [BillingModel.SEMESTER_BASED.value, BillingModel.ACADEMIC_YEAR.value]:
            num_semesters = duration_params.get('num_semesters', 1)
            
            if semester_structure == SemesterStructure.SPLIT_STAY.value and vacation_gap_start and vacation_gap_end:
                # Split stay with vacation gap
                semester1_end = move_in_date + timedelta(days=SEMESTER_DAYS)
                semester2_start = vacation_gap_end
                semester2_end = semester2_start + timedelta(days=SEMESTER_DAYS)
                
                summary.update({
                    'semester1_start': move_in_date,
                    'semester1_end': semester1_end,
                    'semester1_duration_weeks': SEMESTER_WEEKS,
                    'semester2_start': semester2_start,
                    'semester2_end': semester2_end,
                    'semester2_duration_weeks': SEMESTER_WEEKS,
                    'vacation_gap_start': vacation_gap_start,
                    'vacation_gap_end': vacation_gap_end,
                    'vacation_gap_days': (vacation_gap_end - vacation_gap_start).days,
                    'total_duration_weeks': SEMESTER_WEEKS * num_semesters,
                    'total_duration_days': (semester2_end - move_in_date).days,
                })
            else:
                # Continuous stay or single semester
                summary.update({
                    'total_duration_weeks': SEMESTER_WEEKS * num_semesters,
                    'total_duration_days': (move_out_date - move_in_date).days,
                })
        
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            num_months = duration_params.get('num_months', 1)
            summary.update({
                'total_duration_months': num_months,
                'total_duration_days': (move_out_date - move_in_date).days,
            })
        
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            num_years = duration_params.get('num_years', 1)
            summary.update({
                'total_duration_years': num_years,
                'total_duration_weeks': WEEKS_PER_YEAR * num_years,
                'total_duration_days': (move_out_date - move_in_date).days,
            })
        
        return summary
