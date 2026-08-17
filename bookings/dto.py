"""
DTOs (Data Transfer Objects) - Data contracts for booking operations.
Defines the structure of data passed between layers.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import date


@dataclass
class BookingRequestDTO:
    """DTO for creating a booking request."""
    tenant_id: int
    property_id: int
    room_type_id: Optional[int] = None
    unit_type_id: Optional[int] = None
    move_in_date: Optional[date] = None
    billing_model: Optional[str] = None
    num_semesters: Optional[int] = None
    num_months: Optional[int] = None
    num_years: Optional[int] = None
    semester_structure: Optional[str] = None
    vacation_gap_end: Optional[date] = None
    
    def validate(self):
        """Validate the DTO."""
        if not self.room_type_id and not self.unit_type_id:
            raise ValueError("Either room_type_id or unit_type_id must be provided")
        return True


@dataclass
class BookingResponseDTO:
    """DTO for booking response."""
    booking_id: int
    reference_number: str
    status: str
    current_step: str
    next_action: Optional[str] = None
    redirect_url: Optional[str] = None
    requires_lifestyle: bool = False
    requires_consent: bool = False
    error: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'booking_id': self.booking_id,
            'reference_number': self.reference_number,
            'status': self.status,
            'current_step': self.current_step,
            'next_action': self.next_action,
            'redirect_url': self.redirect_url,
            'requires_lifestyle': self.requires_lifestyle,
            'requires_consent': self.requires_consent,
            'error': self.error,
        }


@dataclass
class DurationSelectionDTO:
    """DTO for duration selection."""
    booking_id: int
    move_in_date: date
    billing_model: str
    num_semesters: Optional[int] = None
    num_months: Optional[int] = None
    num_years: Optional[int] = None
    requires_semester_structure: bool = False
    
    def validate(self):
        """Validate the DTO."""
        if self.billing_model == 'SEMESTER_BASED' and not self.num_semesters:
            raise ValueError("num_semesters required for SEMESTER_BASED billing")
        if self.billing_model == 'MONTHLY_BASED' and not self.num_months:
            raise ValueError("num_months required for MONTHLY_BASED billing")
        if self.billing_model == 'ANNUAL_BASED' and not self.num_years:
            raise ValueError("num_years required for ANNUAL_BASED billing")
        return True


@dataclass
class SemesterStructureDTO:
    """DTO for semester structure selection."""
    booking_id: int
    semester_structure: str  # CONTINUOUS_STAY or SPLIT_STAY
    
    def validate(self):
        """Validate the DTO."""
        valid_structures = ['CONTINUOUS_STAY', 'SPLIT_STAY']
        if self.semester_structure not in valid_structures:
            raise ValueError(f"Invalid semester structure. Must be one of: {valid_structures}")
        return True


@dataclass
class VacationDeclarationDTO:
    """DTO for vacation date declaration."""
    booking_id: int
    vacation_gap_end: date
    
    def validate(self):
        """Validate the DTO."""
        if not self.vacation_gap_end:
            raise ValueError("vacation_gap_end is required")
        return True


@dataclass
class ConsentDTO:
    """DTO for consent operations."""
    booking_id: int
    consent_type: str  # 'user' or 'roommate'
    consent_given: bool
    user_ip: Optional[str] = None
    
    def validate(self):
        """Validate the DTO."""
        valid_types = ['user', 'roommate']
        if self.consent_type not in valid_types:
            raise ValueError(f"Invalid consent_type. Must be one of: {valid_types}")
        return True


@dataclass
class PricingSummaryDTO:
    """DTO for pricing summary."""
    billing_model: str
    total_amount: float
    monthly_rent: float
    security_deposit: float
    duration_weeks: int
    move_in_date: date
    move_out_date: date
    duration_params: Dict[str, Any]
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'billing_model': self.billing_model,
            'total_amount': float(self.total_amount),
            'monthly_rent': float(self.monthly_rent),
            'security_deposit': float(self.security_deposit),
            'duration_weeks': self.duration_weeks,
            'move_in_date': self.move_in_date.isoformat(),
            'move_out_date': self.move_out_date.isoformat(),
            'duration_params': self.duration_params,
        }


@dataclass
class CompatibilityMatchDTO:
    """DTO for compatibility match results."""
    booking_id: int
    roommate_id: int
    roommate_name: str
    compatibility_score: float
    high_priority_score: float
    medium_priority_score: float
    low_priority_score: float
    alignments: list
    differences: list
    routing_decision: str  # 'AUTO_ASSIGN' or 'CONSENT_REQUIRED'
    room_id: Optional[int] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'booking_id': self.booking_id,
            'roommate_id': self.roommate_id,
            'roommate_name': self.roommate_name,
            'compatibility_score': float(self.compatibility_score),
            'high_priority_score': float(self.high_priority_score),
            'medium_priority_score': float(self.medium_priority_score),
            'low_priority_score': float(self.low_priority_score),
            'alignments': self.alignments,
            'differences': self.differences,
            'routing_decision': self.routing_decision,
            'room_id': self.room_id,
        }
