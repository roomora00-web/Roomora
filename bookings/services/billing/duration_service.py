"""
DurationService - Duration management operations.
Handles duration calculations, semester structures, and vacation gaps.
"""

from datetime import datetime, timedelta, date
from bookings.constants import BillingModel, SemesterStructure


class DurationService:
    """Service for duration management."""
    
    def __init__(self):
        pass
    
    def calculate_booking_summary(self, move_in_date, billing_model, duration_params, semester_structure=None, vacation_gap_end=None):
        """
        Calculate booking summary including dates and pricing breakdown.
        
        Args:
            move_in_date: Date object
            billing_model: Billing model string
            duration_params: Dict with duration parameters
            semester_structure: Optional semester structure
            vacation_gap_end: Optional vacation gap end date
            
        Returns:
            dict: Booking summary
        """
        if not move_in_date:
            raise ValueError("move_in_date is required")
            
        move_in = move_in_date if isinstance(move_in_date, date) else datetime.strptime(str(move_in_date), '%Y-%m-%d').date()
        
        summary = {
            'move_in_date': move_in,
            'billing_model': billing_model,
            'semester_structure': semester_structure,
        }
        
        if billing_model == BillingModel.SEMESTER_BASED.value:
            num_semesters = duration_params.get('num_semesters', 1)
            summary['num_semesters'] = num_semesters
            summary['total_duration_weeks'] = num_semesters * 17
            summary['move_out_date'] = move_in + timedelta(weeks=num_semesters * 17)
            
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            num_months = duration_params.get('num_months', 1)
            summary['num_months'] = num_months
            summary['total_duration_weeks'] = num_months * 4
            summary['move_out_date'] = move_in + timedelta(days=num_months * 30)
            
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            num_years = duration_params.get('num_years', 1)
            summary['num_years'] = num_years
            summary['total_duration_weeks'] = num_years * 52
            summary['move_out_date'] = move_in + timedelta(days=num_years * 365)
            
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            summary['num_semesters'] = 2
            summary['total_duration_weeks'] = 34
            
            if semester_structure == SemesterStructure.SPLIT_STAY.value:
                # Split stay with vacation gap
                s1_end = move_in + timedelta(days=119)  # ~17 weeks
                summary['semester1_end'] = s1_end
                summary['vacation_gap_start'] = s1_end + timedelta(days=1)
                
                if vacation_gap_end:
                    vacation_end = vacation_gap_end if isinstance(vacation_gap_end, date) else datetime.strptime(str(vacation_gap_end), '%Y-%m-%d').date()
                    summary['vacation_gap_end'] = vacation_end
                    summary['semester2_start'] = vacation_end + timedelta(days=1)
                    summary['semester2_end'] = summary['semester2_start'] + timedelta(days=119)
                    summary['move_out_date'] = summary['semester2_end']
                else:
                    summary['move_out_date'] = s1_end + timedelta(days=119)
            else:
                # Continuous stay
                summary['move_out_date'] = move_in + timedelta(weeks=34)
        
        return summary
    
    def get_duration_options(self, billing_model, pricing_data):
        """
        Get available duration options based on billing model.
        
        Args:
            billing_model: Billing model string
            pricing_data: Pricing data dict
            
        Returns:
            list: Duration options with pricing
        """
        options = []
        
        if billing_model == BillingModel.SEMESTER_BASED.value:
            max_semesters = pricing_data.get('max_semesters', 3)
            semester_price = pricing_data.get('semester_price', 0)
            for i in range(1, max_semesters + 1):
                options.append({
                    'num_semesters': i,
                    'total_weeks': i * 17,
                    'total_months': i * 4.3,
                    'price': semester_price * i if semester_price else 0,
                })
                
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            min_months = pricing_data.get('min_months', 1)
            max_months = pricing_data.get('max_months', 12)
            monthly_price = pricing_data.get('monthly_price', 0)
            for i in range(min_months, max_months + 1):
                options.append({
                    'num_months': i,
                    'total_weeks': i * 4,
                    'total_months': i,
                    'price': monthly_price * i if monthly_price else 0,
                })
                
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            allow_two_year = pricing_data.get('allow_two_year_advance', False)
            yearly_price = pricing_data.get('yearly_price', 0)
            two_years_price = pricing_data.get('two_years_price', 0)
            
            options.append({
                'num_years': 1,
                'total_weeks': 52,
                'total_months': 12,
                'price': yearly_price if yearly_price else 0,
            })
            
            if allow_two_year and two_years_price:
                options.append({
                    'num_years': 2,
                    'total_weeks': 104,
                    'total_months': 24,
                    'price': two_years_price,
                    'discount': (yearly_price * 2) - two_years_price if yearly_price else 0,
                })
                
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            academic_year_price = pricing_data.get('academic_year_price', 0)
            semester_price = pricing_data.get('semester_price', 0)
            options.append({
                'num_semesters': 2,
                'total_weeks': 34,
                'total_months': 9,
                'price': academic_year_price if academic_year_price else (semester_price * 2),
            })
        
        return options
    
    def calculate_semester_dates(self, move_in_date, num_semesters):
        """
        Calculate semester start and end dates.
        
        Args:
            move_in_date: Date object
            num_semesters: Number of semesters
            
        Returns:
            dict: Semester dates
        """
        move_in = move_in_date if isinstance(move_in_date, date) else datetime.strptime(str(move_in_date), '%Y-%m-%d').date()
        
        dates = {
            'semester1_start': move_in,
            'semester1_end': move_in + timedelta(days=119),  # ~17 weeks
        }
        
        if num_semesters >= 2:
            dates['semester2_start'] = dates['semester1_end'] + timedelta(days=1)
            dates['semester2_end'] = dates['semester2_start'] + timedelta(days=119)
        
        if num_semesters >= 3:
            dates['semester3_start'] = dates['semester2_end'] + timedelta(days=1)
            dates['semester3_end'] = dates['semester3_start'] + timedelta(days=119)
        
        return dates
