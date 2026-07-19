"""
Commands - Command pattern for booking operations.
Encapsulates booking operations as command objects.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import date
from django.db import transaction

from bookings.dto import BookingRequestDTO, DurationSelectionDTO, SemesterStructureDTO, VacationDeclarationDTO, ConsentDTO
from bookings.services.booking.booking_service import BookingService
from bookings.services.booking.booking_state_service import BookingStateService
from bookings.services.booking.booking_validation_service import BookingValidationService
from bookings.services.billing.billing_service import BillingService
from bookings.services.billing.duration_service import DurationService
from bookings.services.matching.compatibility_service import CompatibilityService
from bookings.services.matching.consent_service import ConsentService
from bookings.services.matching.room_assignment_service import RoomAssignmentService
from bookings.repositories import BookingRepository
from bookings.exceptions import BookingError


@dataclass
class CreateBookingCommand:
    """Command to create a new booking."""
    dto: BookingRequestDTO
    
    def execute(self):
        """Execute the command."""
        booking_service = BookingService()
        validation_service = BookingValidationService()
        
        # Get objects
        from django.contrib.auth import get_user_model
        from properties.models import Property, RoomType, UnitType
        
        User = get_user_model()
        tenant = User.objects.get(id=self.dto.tenant_id)
        property_obj = Property.objects.get(id=self.dto.property_id)
        
        room_type = None
        unit_type = None
        if self.dto.room_type_id:
            room_type = RoomType.objects.get(id=self.dto.room_type_id)
        if self.dto.unit_type_id:
            unit_type = UnitType.objects.get(id=self.dto.unit_type_id)
        
        # Validate
        validation_service.validate_booking_request(tenant, property_obj, room_type, unit_type)
        
        # Create booking
        booking = booking_service.create_initial_booking(tenant, property_obj, room_type, unit_type)
        
        return booking


@dataclass
class SubmitBookingCommand:
    """Command to submit/finalize a booking."""
    booking_id: int
    duration_params: dict
    billing_model: str
    move_in_date: date
    semester_structure: Optional[str] = None
    vacation_gap_end: Optional[date] = None
    
    def execute(self):
        """Execute the command."""
        from bookings.models import Booking, BillingAllocation, RoomAllocation
        from properties.models import RoomType, UnitType
        
        booking = Booking.objects.get(id=self.booking_id)
        
        # Get pricing
        billing_service = BillingService()
        duration_service = DurationService()
        
        # Calculate summary
        summary = duration_service.calculate_booking_summary(
            move_in_date=self.move_in_date,
            billing_model=self.billing_model,
            duration_params=self.duration_params,
            semester_structure=self.semester_structure,
            vacation_gap_end=self.vacation_gap_end
        )
        
        # Calculate pricing
        pricing = billing_service.calculate_pricing(
            room_type=booking.room_type,
            unit_type=booking.unit_type,
            billing_model=self.billing_model,
            duration_params=self.duration_params
        )
        
        with transaction.atomic():
            # Update booking dates
            booking.move_in_date = summary['move_in_date']
            booking.move_out_date = summary['move_out_date']
            
            # Create billing allocation
            billing_allocation = BillingAllocation.objects.create(
                booking=booking,
                billing_model=self.billing_model,
                num_semesters=self.duration_params.get('num_semesters'),
                num_months=self.duration_params.get('num_months'),
                num_years=self.duration_params.get('num_years'),
                semester_structure=self.semester_structure,
                vacation_gap_start=summary.get('vacation_gap_start'),
                vacation_gap_end=summary.get('vacation_gap_end'),
                semester1_end=summary.get('semester1_end'),
                semester2_start=summary.get('semester2_start'),
                semester2_end=summary.get('semester2_end'),
                monthly_rent=pricing['monthly_rent'],
                total_amount=pricing['total_amount'],
                security_deposit=pricing['security_deposit'],
                total_duration_weeks=summary.get('total_duration_weeks')
            )
            
            # Create room allocation
            occupancy_type = None
            if booking.room_type:
                occupancy_type = booking.room_type.occupancy_type
            
            room_allocation = RoomAllocation.objects.create(
                booking=booking,
                room_type=booking.room_type,
                unit_type=booking.unit_type,
                occupancy_type=occupancy_type,
                allocation_status='RESERVED'
            )
            
            # Update booking status
            state_service = BookingStateService()
            state_service.transition_state(booking, 'UNDER_REVIEW', 'Booking submitted', booking.tenant)
            
            booking.save()
        
        return booking


@dataclass
class CancelBookingCommand:
    """Command to cancel a booking."""
    booking_id: int
    reason: str
    permanent: bool = False
    triggered_by_id: Optional[int] = None
    
    def execute(self):
        """Execute the command."""
        from bookings.models import Booking
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        booking = Booking.objects.get(id=self.booking_id)
        triggered_by = User.objects.get(id=self.triggered_by_id) if self.triggered_by_id else booking.tenant
        
        booking_service = BookingService()
        
        if self.permanent:
            return booking_service.permanently_cancel_booking(booking, self.reason, triggered_by)
        else:
            return booking_service.cancel_booking(booking, self.reason, triggered_by)


@dataclass
class ReinstateBookingCommand:
    """Command to reinstate a cancelled booking."""
    booking_id: int
    triggered_by_id: Optional[int] = None
    
    def execute(self):
        """Execute the command."""
        from bookings.models import Booking
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        booking = Booking.objects.get(id=self.booking_id)
        triggered_by = User.objects.get(id=self.triggered_by_id) if self.triggered_by_id else booking.tenant
        
        booking_service = BookingService()
        return booking_service.reinstate_booking(booking, triggered_by)


@dataclass
class RecordConsentCommand:
    """Command to record consent."""
    dto: ConsentDTO
    
    def execute(self):
        """Execute the command."""
        from bookings.models import Booking, ConsentRecord
        
        booking = Booking.objects.get(id=self.dto.booking_id)
        consent_service = ConsentService()
        
        # Get or create consent record
        consent_record, created = ConsentRecord.objects.get_or_create(booking=booking)
        
        if self.dto.consent_type == 'user':
            consent_service.record_user_consent(booking, self.dto.user_ip)
            consent_record.user_consent = True
            consent_record.user_consent_date = booking.user_consent_date
            consent_record.user_consent_ip = self.dto.user_ip
        else:
            consent_service.record_roommate_consent(booking, booking.roommate, self.dto.user_ip)
            consent_record.roommate_consent = True
            consent_record.roommate_consent_date = booking.roommate_consent_date
            consent_record.roommate_consent_ip = self.dto.user_ip
        
        # Update consent status
        if consent_record.user_consent and consent_record.roommate_consent:
            consent_record.consent_status = 'BOTH_CONSENTED'
        elif consent_record.user_consent:
            consent_record.consent_status = 'USER_CONSENTED'
        elif consent_record.roommate_consent:
            consent_record.consent_status = 'ROOMMATE_CONSENTED'
        
        consent_record.save()
        
        return consent_record


@dataclass
class AssignRoomCommand:
    """Command to assign a room to a booking."""
    booking_id: int
    room_id: int
    assigned_by_id: int
    
    def execute(self):
        """Execute the command."""
        from bookings.models import Booking
        from properties.models import Room
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        booking = Booking.objects.get(id=self.booking_id)
        room = Room.objects.get(id=self.room_id)
        assigned_by = User.objects.get(id=self.assigned_by_id)
        
        room_assignment_service = RoomAssignmentService()
        assignment = room_assignment_service.assign_room(booking, room, assigned_by)
        
        # Update room allocation
        from bookings.models import RoomAllocation
        room_allocation, created = RoomAllocation.objects.get_or_create(booking=booking)
        room_allocation.assigned_room = room
        room_allocation.allocation_status = 'CONFIRMED'
        room_allocation.confirmed_at = timezone.now()
        room_allocation.save()
        
        # Transition booking status
        state_service = BookingStateService()
        state_service.transition_state(booking, 'CONFIRMED_ASSIGNED', 'Room assigned', assigned_by)
        
        return assignment
