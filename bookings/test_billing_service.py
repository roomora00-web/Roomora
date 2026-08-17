"""
Tests for Billing Service

Tests the three immutable rules:
Rule 1: Student sets the start. The system sets the end.
Rule 2: One semester is exactly 17 weeks. Always.
Rule 3: Admin is the sole controller of all pricing and configuration.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal

from .constants import (
    BillingModel, SemesterStructure,
    SEMESTER_WEEKS, SEMESTER_DAYS,
    ACADEMIC_YEAR_WEEKS, ACADEMIC_YEAR_DAYS,
    WEEKS_PER_YEAR, DAYS_PER_YEAR,
    DAYS_PER_MONTH,
    PROPERTY_TYPE_BILLING_COMPATIBILITY
)
from .billing_service import BillingService


class BillingConstantsTest(TestCase):
    """Test that billing constants are correctly defined"""
    
    def test_semester_constant(self):
        """Rule 2: One semester is exactly 17 weeks"""
        self.assertEqual(SEMESTER_WEEKS, 17)
        self.assertEqual(SEMESTER_DAYS, 119)  # 17 * 7
    
    def test_academic_year_constant(self):
        """Academic Year = 2 semesters = 34 weeks"""
        self.assertEqual(ACADEMIC_YEAR_WEEKS, 34)
        self.assertEqual(ACADEMIC_YEAR_DAYS, 238)  # 34 * 7
    
    def test_annual_constant(self):
        """Annual = 52 weeks"""
        self.assertEqual(WEEKS_PER_YEAR, 52)
        self.assertEqual(DAYS_PER_YEAR, 364)  # 52 * 7
    
    def test_monthly_constant(self):
        """Monthly = 30 days"""
        self.assertEqual(DAYS_PER_MONTH, 30)


class BillingModelCompatibilityTest(TestCase):
    """Test property type to billing model compatibility"""
    
    def test_hostel_compatibility(self):
        """Hostels should only support SEMESTER_BASED and MONTHLY_BASED"""
        compatible = PROPERTY_TYPE_BILLING_COMPATIBILITY['HOSTEL']
        self.assertIn(BillingModel.SEMESTER_BASED, compatible)
        self.assertIn(BillingModel.MONTHLY_BASED, compatible)
        self.assertNotIn(BillingModel.ANNUAL_BASED, compatible)
        self.assertNotIn(BillingModel.ACADEMIC_YEAR, compatible)
    
    def test_apartment_compatibility(self):
        """Apartments should support all billing models"""
        compatible = PROPERTY_TYPE_BILLING_COMPATIBILITY['APARTMENT']
        self.assertIn(BillingModel.SEMESTER_BASED, compatible)
        self.assertIn(BillingModel.MONTHLY_BASED, compatible)
        self.assertIn(BillingModel.ANNUAL_BASED, compatible)
        self.assertIn(BillingModel.ACADEMIC_YEAR, compatible)
    
    def test_compound_house_compatibility(self):
        """Compound houses should not support semester-based billing"""
        compatible = PROPERTY_TYPE_BILLING_COMPATIBILITY['COMPOUND_HOUSE']
        self.assertNotIn(BillingModel.SEMESTER_BASED, compatible)
        self.assertNotIn(BillingModel.ACADEMIC_YEAR, compatible)
        self.assertIn(BillingModel.MONTHLY_BASED, compatible)
        self.assertIn(BillingModel.ANNUAL_BASED, compatible)


class SemesterBasedBillingTest(TestCase):
    """Test Model A: Semester-Based billing"""
    
    def test_single_semester_calculation(self):
        """Rule 1: System calculates move-out date for 1 semester"""
        move_in = date(2025, 1, 15)
        move_out = BillingService.calculate_move_out_date(
            move_in, 
            BillingModel.SEMESTER_BASED.value,
            num_semesters=1
        )
        expected = move_in + timedelta(days=SEMESTER_DAYS)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 119)
    
    def test_two_semesters_calculation(self):
        """Test 2 semester calculation (continuous)"""
        move_in = date(2025, 1, 15)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.SEMESTER_BASED.value,
            num_semesters=2
        )
        expected = move_in + timedelta(days=SEMESTER_DAYS * 2)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 238)
    
    def test_three_semesters_calculation(self):
        """Test maximum 3 semesters"""
        move_in = date(2025, 1, 15)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.SEMESTER_BASED.value,
            num_semesters=3
        )
        expected = move_in + timedelta(days=SEMESTER_DAYS * 3)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 357)
    
    def test_invalid_semester_count(self):
        """Should reject invalid semester counts"""
        move_in = date(2025, 1, 15)
        
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.SEMESTER_BASED.value,
                num_semesters=0
            )
        
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.SEMESTER_BASED.value,
                num_semesters=4
            )


class MonthlyBasedBillingTest(TestCase):
    """Test Model B: Monthly-Based billing"""
    
    def test_single_month_calculation(self):
        """Rule 1: System calculates move-out date for 1 month"""
        move_in = date(2025, 3, 1)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.MONTHLY_BASED.value,
            num_months=1
        )
        expected = move_in + timedelta(days=DAYS_PER_MONTH)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 30)
    
    def test_six_months_calculation(self):
        """Test 6 month calculation"""
        move_in = date(2025, 3, 1)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.MONTHLY_BASED.value,
            num_months=6
        )
        expected = move_in + timedelta(days=DAYS_PER_MONTH * 6)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 180)
    
    def test_invalid_month_count(self):
        """Should reject invalid month counts"""
        move_in = date(2025, 3, 1)
        
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.MONTHLY_BASED.value,
                num_months=0
            )
        
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.MONTHLY_BASED.value,
                num_months=13
            )


class AnnualBasedBillingTest(TestCase):
    """Test Model C: Annual-Based billing"""
    
    def test_one_year_calculation(self):
        """Rule 1: System calculates move-out date for 1 year"""
        move_in = date(2025, 2, 1)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.ANNUAL_BASED.value,
            num_years=1
        )
        expected = move_in + timedelta(days=DAYS_PER_YEAR)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 364)
    
    def test_two_year_calculation(self):
        """Test 2-year advance payment"""
        move_in = date(2025, 2, 1)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.ANNUAL_BASED.value,
            num_years=2
        )
        expected = move_in + timedelta(days=DAYS_PER_YEAR * 2)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 728)
    
    def test_invalid_year_count(self):
        """Should reject invalid year counts"""
        move_in = date(2025, 2, 1)
        
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.ANNUAL_BASED.value,
                num_years=3
            )


class AcademicYearBillingTest(TestCase):
    """Test Model D: Academic Year billing"""
    
    def test_continuous_stay_calculation(self):
        """Test continuous stay (34 consecutive weeks)"""
        move_in = date(2025, 1, 15)
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.ACADEMIC_YEAR.value,
            semester_structure=SemesterStructure.CONTINUOUS_STAY.value
        )
        expected = move_in + timedelta(days=ACADEMIC_YEAR_DAYS)
        self.assertEqual(move_out, expected)
        self.assertEqual((move_out - move_in).days, 238)
    
    def test_split_stay_calculation(self):
        """Test split stay with vacation gap"""
        move_in = date(2025, 1, 15)
        vacation_start = date(2025, 5, 15)
        vacation_end = date(2025, 6, 15)
        
        move_out = BillingService.calculate_move_out_date(
            move_in,
            BillingModel.ACADEMIC_YEAR.value,
            semester_structure=SemesterStructure.SPLIT_STAY.value,
            vacation_gap_start=vacation_start,
            vacation_gap_end=vacation_end
        )
        
        # Semester 1: Jan 15 → Jan 15 + 119 = May 14 (S1 end)
        # Vacation: May 15 – June 14 (30 days; vacation_gap_start=May 15, vacation_gap_end=June 15)
        # Semester 2: June 15 (= vacation_gap_end, the S2 move-in) → June 15 + 119 = Oct 12
        # Total calendar days (Jan 15 → Oct 12): 270 days
        expected = vacation_end + timedelta(days=SEMESTER_DAYS)  # June 15 + 119 = Oct 12
        self.assertEqual(move_out, expected)
    
    def test_split_stay_invalid_dates(self):
        """Should reject invalid vacation gap dates"""
        move_in = date(2025, 1, 15)
        
        # Vacation start before move-in
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.ACADEMIC_YEAR.value,
                semester_structure=SemesterStructure.SPLIT_STAY.value,
                vacation_gap_start=date(2025, 1, 10),
                vacation_gap_end=date(2025, 6, 15)
            )
        
        # Vacation end before vacation start
        with self.assertRaises(ValidationError):
            BillingService.calculate_move_out_date(
                move_in,
                BillingModel.ACADEMIC_YEAR.value,
                semester_structure=SemesterStructure.SPLIT_STAY.value,
                vacation_gap_start=date(2025, 6, 15),
                vacation_gap_end=date(2025, 5, 15)
            )


class PricingCalculationTest(TestCase):
    """Test total amount calculation based on billing model"""
    
    def test_semester_based_pricing(self):
        """Test semester-based pricing calculation"""
        pricing_data = {'semester_price': Decimal('2000.00')}
        total = BillingService.calculate_total_amount(
            BillingModel.SEMESTER_BASED.value,
            pricing_data,
            num_semesters=2
        )
        self.assertEqual(total, Decimal('4000.00'))
    
    def test_monthly_based_pricing(self):
        """Test monthly-based pricing calculation"""
        pricing_data = {'monthly_price': Decimal('500.00')}
        total = BillingService.calculate_total_amount(
            BillingModel.MONTHLY_BASED.value,
            pricing_data,
            num_months=6
        )
        self.assertEqual(total, Decimal('3000.00'))
    
    def test_annual_based_pricing(self):
        """Test annual-based pricing calculation"""
        pricing_data = {'yearly_price': Decimal('25000.00')}
        total = BillingService.calculate_total_amount(
            BillingModel.ANNUAL_BASED.value,
            pricing_data,
            num_years=1
        )
        self.assertEqual(total, Decimal('25000.00'))
    
    def test_two_year_pricing(self):
        """Test 2-year pricing with discount"""
        pricing_data = {
            'yearly_price': Decimal('25000.00'),
            'two_years_price': Decimal('45000.00')
        }
        total = BillingService.calculate_total_amount(
            BillingModel.ANNUAL_BASED.value,
            pricing_data,
            num_years=2
        )
        self.assertEqual(total, Decimal('45000.00'))
    
    def test_academic_year_pricing(self):
        """Test academic year pricing with discount"""
        pricing_data = {
            'semester_price': Decimal('2000.00'),
            'academic_year_price': Decimal('3600.00')
        }
        total = BillingService.calculate_total_amount(
            BillingModel.ACADEMIC_YEAR.value,
            pricing_data
        )
        self.assertEqual(total, Decimal('3600.00'))


class CompatibilityValidationTest(TestCase):
    """Test billing model compatibility validation"""
    
    def test_valid_combination(self):
        """Should accept valid property type and billing model combination"""
        result = BillingService.validate_billing_model_compatibility(
            'HOSTEL',
            BillingModel.SEMESTER_BASED.value
        )
        self.assertTrue(result)
    
    def test_invalid_combination(self):
        """Should reject invalid property type and billing model combination"""
        with self.assertRaises(ValidationError):
            BillingService.validate_billing_model_compatibility(
                'HOSTEL',
                BillingModel.ANNUAL_BASED.value
            )
