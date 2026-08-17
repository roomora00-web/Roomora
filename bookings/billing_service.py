"""
Billing Service - Duration Calculation and Validation

This service implements the three immutable rules:
Rule 1: Student sets the start. The system sets the end.
Rule 2: One semester is exactly 17 weeks. Always.
Rule 3: Admin is the sole controller of all pricing and configuration.
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from .constants import (
    BillingModel, SemesterStructure,
    SEMESTER_WEEKS, SEMESTER_DAYS,
    ACADEMIC_YEAR_WEEKS, ACADEMIC_YEAR_DAYS,
    WEEKS_PER_YEAR, DAYS_PER_YEAR,
    DAYS_PER_MONTH,
    PROPERTY_TYPE_BILLING_COMPATIBILITY,
    DEFAULT_MAX_SEMESTERS, DEFAULT_MIN_MONTHS, DEFAULT_MAX_MONTHS
)


class BillingService:
    """Service for billing model calculations and validation"""
    
    @staticmethod
    def validate_billing_model_compatibility(property_type, billing_model):
        """
        Validate that the billing model is compatible with the property type
        as per specification in Part 1.2
        """
        compatible_models = PROPERTY_TYPE_BILLING_COMPATIBILITY.get(property_type, [])
        
        if billing_model not in compatible_models:
            raise ValidationError(
                f"Billing model '{billing_model}' is not compatible with "
                f"property type '{property_type}'. "
                f"Compatible models: {', '.join(compatible_models)}"
            )
        
        return True
    
    @staticmethod
    def calculate_move_out_date(move_in_date, billing_model, **kwargs):
        """
        Calculate move-out date based on billing model (Rule 1: System sets the end)
        
        Args:
            move_in_date: datetime.date - Student-selected move-in date
            billing_model: str - The billing model (SEMESTER_BASED, MONTHLY_BASED, etc.)
            **kwargs: Additional parameters based on billing model:
                - num_semesters: int (for SEMESTER_BASED, ACADEMIC_YEAR)
                - num_months: int (for MONTHLY_BASED)
                - num_years: int (for ANNUAL_BASED)
                - semester_structure: str (for ACADEMIC_YEAR)
                - vacation_gap_start: date (for ACADEMIC_YEAR with SPLIT_STAY)
                - vacation_gap_end: date (for ACADEMIC_YEAR with SPLIT_STAY)
        
        Returns:
            datetime.date - Calculated move-out date
        """
        if billing_model == BillingModel.SEMESTER_BASED.value:
            return BillingService._calculate_semester_based(move_in_date, **kwargs)
        
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            return BillingService._calculate_monthly_based(move_in_date, **kwargs)
        
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            return BillingService._calculate_annual_based(move_in_date, **kwargs)
        
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            return BillingService._calculate_academic_year(move_in_date, **kwargs)
        
        else:
            raise ValidationError(f"Unknown billing model: {billing_model}")
    
    @staticmethod
    def _calculate_semester_based(move_in_date, num_semesters=None, max_semesters=None, **kwargs):
        """
        Model A: Semester-Based
        Move-out = Move-in + (Number of semesters × 17 weeks)
        
        Args:
            max_semesters: Optional per-room override for the maximum semesters allowed.
                           Defaults to DEFAULT_MAX_SEMESTERS (3) if not provided.
        """
        if num_semesters is None:
            raise ValidationError("num_semesters is required for SEMESTER_BASED billing")
        
        # Use per-room max if provided, otherwise fall back to platform default
        effective_max = max_semesters if max_semesters is not None else DEFAULT_MAX_SEMESTERS
        
        if num_semesters < 1 or num_semesters > effective_max:
            raise ValidationError(
                f"Number of semesters must be between 1 and {effective_max}"
            )
        
        # Rule 2: One semester is exactly 17 weeks
        total_days = num_semesters * SEMESTER_DAYS
        move_out_date = move_in_date + timedelta(days=total_days)
        
        return move_out_date
    
    @staticmethod
    def _calculate_monthly_based(move_in_date, num_months=None, **kwargs):
        """
        Model B: Monthly-Based
        Move-out = Move-in + (Number of months × 30 days)
        """
        if num_months is None:
            raise ValidationError("num_months is required for MONTHLY_BASED billing")
        
        if num_months < DEFAULT_MIN_MONTHS or num_months > DEFAULT_MAX_MONTHS:
            raise ValidationError(
                f"Number of months must be between {DEFAULT_MIN_MONTHS} and {DEFAULT_MAX_MONTHS}"
            )
        
        # Monthly billing uses 30-day months
        total_days = num_months * DAYS_PER_MONTH
        move_out_date = move_in_date + timedelta(days=total_days)
        
        return move_out_date
    
    @staticmethod
    def _calculate_annual_based(move_in_date, num_years=1, **kwargs):
        """
        Model C: Annual-Based
        Move-out = Move-in + 52 weeks (364 days) for 1 year
        Move-out = Move-in + 104 weeks (728 days) for 2 years
        """
        if num_years not in [1, 2]:
            raise ValidationError("Number of years must be 1 or 2 for ANNUAL_BASED billing")
        
        # Annual billing uses 52-week years
        total_days = num_years * DAYS_PER_YEAR
        move_out_date = move_in_date + timedelta(days=total_days)
        
        return move_out_date
    
    @staticmethod
    def _calculate_academic_year(move_in_date, semester_structure=None, **kwargs):
        """
        Model D: Academic Year (Combined Two-Semester)
        Academic Year = 2 × 17 weeks = 34 weeks (238 days) of paid occupancy
        
        For CONTINUOUS_STAY: 34 consecutive calendar weeks
        For SPLIT_STAY: 34 weeks split with vacation gap
        """
        if semester_structure is None:
            raise ValidationError("semester_structure is required for ACADEMIC_YEAR billing")
        
        if semester_structure == SemesterStructure.CONTINUOUS_STAY.value:
            # 34 consecutive weeks
            move_out_date = move_in_date + timedelta(days=ACADEMIC_YEAR_DAYS)
            return move_out_date
        
        elif semester_structure == SemesterStructure.SPLIT_STAY.value:
            # Split with vacation gap
            vacation_gap_start = kwargs.get('vacation_gap_start')
            vacation_gap_end = kwargs.get('vacation_gap_end')
            
            if not vacation_gap_start or not vacation_gap_end:
                raise ValidationError(
                    "vacation_gap_start and vacation_gap_end are required for SPLIT_STAY structure"
                )
            
            if vacation_gap_start <= move_in_date:
                raise ValidationError("vacation_gap_start must be after move_in_date")
            
            if vacation_gap_end <= vacation_gap_start:
                raise ValidationError("vacation_gap_end must be after vacation_gap_start")
            
            # Calculate semester 1 end (before vacation)
            semester1_days = SEMESTER_DAYS
            semester1_end = move_in_date + timedelta(days=semester1_days)
            
            # Calculate vacation duration
            vacation_duration = (vacation_gap_end - vacation_gap_start).days
            
            # Calculate semester 2 (after vacation)
            semester2_start = vacation_gap_end
            semester2_days = SEMESTER_DAYS
            move_out_date = semester2_start + timedelta(days=semester2_days)
            
            return move_out_date
        
        else:
            raise ValidationError(f"Unknown semester structure: {semester_structure}")
    
    @staticmethod
    def calculate_total_amount(billing_model, pricing_data, **kwargs):
        """
        Calculate total amount based on billing model and pricing
        
        Args:
            billing_model: str - The billing model
            pricing_data: dict - Pricing information from RoomTypePricing/UnitTypePricing
            **kwargs: Duration parameters (num_semesters, num_months, num_years)
        
        Returns:
            decimal.Decimal - Total amount
        """
        from decimal import Decimal
        
        if billing_model == BillingModel.SEMESTER_BASED.value:
            num_semesters = kwargs.get('num_semesters', 1)
            semester_price = pricing_data.get('semester_price', Decimal('0'))
            return semester_price * num_semesters
        
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            num_months = kwargs.get('num_months', 1)
            monthly_price = pricing_data.get('monthly_price', Decimal('0'))
            return monthly_price * num_months
        
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            num_years = kwargs.get('num_years', 1)
            yearly_price = pricing_data.get('yearly_price', Decimal('0'))
            if num_years == 2:
                # Check if two_years_price is set, otherwise use 2x yearly
                two_years_price = pricing_data.get('two_years_price')
                if two_years_price:
                    return two_years_price
                return yearly_price * 2
            return yearly_price
        
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            # Academic year has its own combined price
            academic_year_price = pricing_data.get('academic_year_price')
            if academic_year_price:
                return academic_year_price
            # Fallback: calculate from semester prices with discount
            semester_price = pricing_data.get('semester_price', Decimal('0'))
            # Apply 10% discount as default for academic year
            return semester_price * 2 * Decimal('0.9')
        
        else:
            raise ValidationError(f"Unknown billing model: {billing_model}")
    
    @staticmethod
    def extend_monthly_booking(booking, additional_months):
        """
        Extend a Monthly-Based booking by adding more months
        
        Args:
            booking: Booking instance
            additional_months: int - Number of months to add
        
        Returns:
            datetime.date - New move-out date
        """
        if booking.billing_model != BillingModel.MONTHLY_BASED.value:
            raise ValidationError("Only MONTHLY_BASED bookings can be extended")
        
        if booking.status not in ['ACTIVE', 'CONFIRMED_ASSIGNED']:
            raise ValidationError("Only active bookings can be extended")
        
        # Calculate new move-out date
        additional_days = additional_months * DAYS_PER_MONTH
        new_move_out_date = booking.move_out_date + timedelta(days=additional_days)
        
        # Update booking
        booking.num_months = (booking.num_months or 0) + additional_months
        booking.move_out_date = new_move_out_date
        booking.save()
        
        return new_move_out_date
    
    @staticmethod
    def get_billing_model_description(billing_model):
        """Get human-readable description of billing model"""
        from .constants import BILLING_MODEL_DESCRIPTIONS
        return BILLING_MODEL_DESCRIPTIONS.get(billing_model, "Unknown billing model")
