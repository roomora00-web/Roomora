"""
Duration Selection Serializers

Serializers for the duration selection flow as per Part 3.
"""

from rest_framework import serializers
from datetime import date

from .constants import BillingModel, SemesterStructure
from .duration_service import DurationSelectionService
from .billing_service import BillingService


class DurationSelectionSerializer(serializers.Serializer):
    """Base serializer for duration selection"""
    billing_model = serializers.ChoiceField(choices=[
        (BillingModel.SEMESTER_BASED.value, 'Semester-Based'),
        (BillingModel.MONTHLY_BASED.value, 'Monthly-Based'),
        (BillingModel.ANNUAL_BASED.value, 'Annual-Based'),
        (BillingModel.ACADEMIC_YEAR.value, 'Academic Year'),
    ])
    move_in_date = serializers.DateField()
    
    # Duration fields (one will be used based on billing model)
    num_semesters = serializers.IntegerField(required=False, min_value=1, max_value=3)
    num_months = serializers.IntegerField(required=False, min_value=1, max_value=12)
    num_years = serializers.IntegerField(required=False, min_value=1, max_value=2)


class SemesterBasedDurationSerializer(serializers.Serializer):
    """Serializer for Semester-Based duration selection"""
    num_semesters = serializers.IntegerField(min_value=1, max_value=3)
    move_in_date = serializers.DateField()
    
    def validate(self, attrs):
        num_semesters = attrs['num_semesters']
        move_in_date = attrs['move_in_date']
        
        # Calculate move-out date
        move_out_date = BillingService.calculate_move_out_date(
            move_in_date,
            BillingModel.SEMESTER_BASED.value,
            num_semesters=num_semesters
        )
        
        attrs['move_out_date'] = move_out_date
        attrs['requires_semester_structure'] = num_semesters >= 2
        
        return attrs


class MonthlyBasedDurationSerializer(serializers.Serializer):
    """Serializer for Monthly-Based duration selection"""
    num_months = serializers.IntegerField(min_value=1, max_value=12)
    move_in_date = serializers.DateField()
    
    def validate(self, attrs):
        num_months = attrs['num_months']
        move_in_date = attrs['move_in_date']
        
        # Calculate move-out date
        move_out_date = BillingService.calculate_move_out_date(
            move_in_date,
            BillingModel.MONTHLY_BASED.value,
            num_months=num_months
        )
        
        attrs['move_out_date'] = move_out_date
        attrs['requires_semester_structure'] = False
        
        return attrs


class AnnualBasedDurationSerializer(serializers.Serializer):
    """Serializer for Annual-Based duration selection"""
    num_years = serializers.IntegerField(min_value=1, max_value=2)
    move_in_date = serializers.DateField()
    
    def validate(self, attrs):
        num_years = attrs['num_years']
        move_in_date = attrs['move_in_date']
        
        # Calculate move-out date
        move_out_date = BillingService.calculate_move_out_date(
            move_in_date,
            BillingModel.ANNUAL_BASED.value,
            num_years=num_years
        )
        
        attrs['move_out_date'] = move_out_date
        attrs['requires_semester_structure'] = False
        
        return attrs


class AcademicYearDurationSerializer(serializers.Serializer):
    """Serializer for Academic Year duration selection"""
    move_in_date = serializers.DateField()
    
    def validate(self, attrs):
        move_in_date = attrs['move_in_date']
        
        # Academic Year is always 2 semesters
        move_out_date = BillingService.calculate_move_out_date(
            move_in_date,
            BillingModel.ACADEMIC_YEAR.value,
            semester_structure=SemesterStructure.CONTINUOUS_STAY.value
        )
        
        attrs['move_out_date'] = move_out_date
        attrs['num_semesters'] = 2
        attrs['requires_semester_structure'] = True
        
        return attrs


class SemesterStructureSerializer(serializers.Serializer):
    """Serializer for semester structure selection (Part 4)"""
    semester_structure = serializers.ChoiceField(choices=[
        (SemesterStructure.CONTINUOUS_STAY.value, 'Continuous Stay'),
        (SemesterStructure.SPLIT_STAY.value, 'Split Stay with Vacation Gap'),
    ])
    
    # For split stay only
    vacation_gap_start = serializers.DateField(required=False)
    vacation_gap_end = serializers.DateField(required=False)
    
    def validate(self, attrs):
        semester_structure = attrs['semester_structure']
        
        if semester_structure == SemesterStructure.SPLIT_STAY.value:
            if 'vacation_gap_start' not in attrs or 'vacation_gap_end' not in attrs:
                raise serializers.ValidationError(
                    "vacation_gap_start and vacation_gap_end are required for split stay"
                )
            
            if attrs['vacation_gap_start'] >= attrs['vacation_gap_end']:
                raise serializers.ValidationError(
                    "vacation_gap_end must be after vacation_gap_start"
                )
        
        return attrs


class VacationDateDeclarationSerializer(serializers.Serializer):
    """Serializer for vacation date declaration (Part 5)"""
    vacation_gap_end = serializers.DateField(help_text='Semester 2 start date')
    
    def validate_vacation_gap_end(self, value):
        # Ensure date is in the future
        if value < date.today():
            raise serializers.ValidationError("Semester 2 start date must be in the future")
        return value


class BookingSummarySerializer(serializers.Serializer):
    """Serializer for booking summary (Part 6)"""
    booking_id = serializers.UUIDField()
    move_in_date = serializers.DateField()
    move_out_date = serializers.DateField()
    billing_model = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    semester_structure = serializers.CharField(required=False)
    vacation_gap_start = serializers.DateField(required=False)
    vacation_gap_end = serializers.DateField(required=False)
    
    # For split stay summary
    semester1_start = serializers.DateField(required=False)
    semester1_end = serializers.DateField(required=False)
    semester2_start = serializers.DateField(required=False)
    semester2_end = serializers.DateField(required=False)
    vacation_reserve_start = serializers.DateField(required=False)
    vacation_reserve_end = serializers.DateField(required=False)


class DurationOptionsResponseSerializer(serializers.Serializer):
    """Response serializer for duration options"""
    billing_model = serializers.CharField()
    options = serializers.ListField(child=serializers.DictField())
