"""
BillingService - Pricing and billing operations.
Handles pricing calculations, billing model management, and cost calculations.
"""

from decimal import Decimal
from bookings.exceptions import PricingError


class BillingService:
    """Service for billing and pricing operations."""
    
    def __init__(self):
        pass
    
    def calculate_pricing(self, room_type=None, unit_type=None, billing_model=None, duration_params=None):
        """
        Calculate pricing based on billing model and duration.
        
        Args:
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            billing_model: Billing model string
            duration_params: Dict with duration parameters (num_semesters, num_months, num_years)
            
        Returns:
            dict: Pricing breakdown
            
        Raises:
            PricingError: If pricing calculation fails
        """
        pricing = None
        if room_type:
            pricing = room_type.pricing_models.first()
        elif unit_type:
            pricing = unit_type.pricing_models.first()
        
        if not pricing:
            raise PricingError("Pricing configuration not found")
        
        duration_params = duration_params or {}
        total_amount = Decimal('0')
        monthly_rent = Decimal('0')
        
        if billing_model == 'SEMESTER_BASED':
            num_semesters = duration_params.get('num_semesters', 1)
            semester_price = pricing.semester_price or Decimal('0')
            total_amount = semester_price * Decimal(num_semesters)
            monthly_rent = total_amount / (Decimal(num_semesters) * Decimal('4.3'))  # Approximate months per semester
            
        elif billing_model == 'MONTHLY_BASED':
            num_months = duration_params.get('num_months', 1)
            monthly_price = pricing.monthly_price or Decimal('0')
            total_amount = monthly_price * Decimal(num_months)
            monthly_rent = monthly_price
            
        elif billing_model == 'ANNUAL_BASED':
            num_years = duration_params.get('num_years', 1)
            yearly_price = pricing.yearly_price or Decimal('0')
            total_amount = yearly_price * Decimal(num_years)
            monthly_rent = total_amount / (Decimal(num_years) * Decimal('12'))
            
        elif billing_model == 'ACADEMIC_YEAR':
            academic_year_price = pricing.academic_year_price or Decimal('0')
            if not academic_year_price:
                # Fallback to 2 semesters with discount
                semester_price = pricing.semester_price or Decimal('0')
                academic_year_price = semester_price * Decimal('2') * Decimal('0.9')
            total_amount = academic_year_price
            monthly_rent = total_amount / Decimal('9')  # Academic year is ~9 months
        
        else:
            raise PricingError(f"Unknown billing model: {billing_model}")
        
        return {
            'total_amount': total_amount,
            'monthly_rent': monthly_rent,
            'security_deposit': pricing.security_deposit or Decimal('0'),
            'billing_model': billing_model,
            'duration_params': duration_params,
        }
    
    def get_billing_model(self, room_type=None, unit_type=None):
        """
        Get billing model for room or unit type.
        
        Args:
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            
        Returns:
            str: Billing model string
        """
        if room_type:
            return room_type.billing_model
        elif unit_type:
            return unit_type.billing_model
        return None
    
    def get_pricing_data(self, room_type=None, unit_type=None):
        """
        Get pricing data for room or unit type.
        
        Args:
            room_type: Optional RoomType object
            unit_type: Optional UnitType object
            
        Returns:
            dict: Pricing data
        """
        pricing = None
        if room_type:
            pricing = room_type.pricing_models.first()
        elif unit_type:
            pricing = unit_type.pricing_models.first()
        
        if not pricing:
            return {}
        
        return {
            'semester_price': pricing.semester_price,
            'monthly_price': pricing.monthly_price,
            'yearly_price': pricing.yearly_price,
            'academic_year_price': pricing.academic_year_price,
            'two_years_price': pricing.two_years_price,
            'security_deposit': pricing.security_deposit,
            'max_semesters': pricing.max_semesters,
            'min_months': pricing.min_months,
            'max_months': pricing.max_months,
            'allow_two_year_advance': pricing.allow_two_year_advance,
        }
