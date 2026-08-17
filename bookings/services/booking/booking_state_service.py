"""
BookingStateService - State machine for booking status transitions.
Handles all booking status transitions with validation.
"""

from django.db import transaction
from django.utils import timezone

from bookings.models import BookingStatusTimeline
from bookings.exceptions import InvalidStateTransitionError


class BookingStateService:
    """Service for managing booking state transitions."""
    
    # Define valid state transitions
    STATE_TRANSITIONS = {
        'INITIATED': ['UNDER_REVIEW', 'TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'],
        'UNDER_REVIEW': ['APPROVED', 'REJECTED', 'TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'],
        'ASSIGNED_AWAITING': ['CONFIRMED_ASSIGNED', 'TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'],
        'CONFIRMED_ASSIGNED': ['ACTIVE', 'TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'],
        'ACTIVE': ['COMPLETED', 'TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'],
        'TEMPORARILY_CANCELLED': ['INITIATED', 'PERMANENTLY_CANCELLED'],
        'PERMANENTLY_CANCELLED': [],
        'COMPLETED': [],
        'REJECTED': [],
        'WAITLISTED': ['UNDER_REVIEW', 'TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'],
    }
    
    def __init__(self):
        pass
    
    def is_valid_transition(self, from_state, to_state):
        """
        Check if a state transition is valid.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            bool: True if transition is valid
        """
        valid_transitions = self.STATE_TRANSITIONS.get(from_state, [])
        return to_state in valid_transitions
    
    @transaction.atomic
    def transition_state(self, booking, new_status, reason=None, triggered_by=None):
        """
        Transition booking to a new state.
        
        Args:
            booking: Booking object
            new_status: New status
            reason: Reason for transition
            triggered_by: User who triggered transition
            
        Returns:
            Updated booking object
            
        Raises:
            InvalidStateTransitionError: If transition is invalid
        """
        from_state = booking.status
        
        # Validate transition
        if not self.is_valid_transition(from_state, new_status):
            raise InvalidStateTransitionError(from_state, new_status)
        
        # Update booking status
        booking.status = new_status
        booking.save()
        
        # Create timeline entry
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status=from_state,
            new_status=new_status,
            reason=reason or f'Transitioned from {from_state} to {new_status}',
            triggered_by=triggered_by
        )
        
        return booking
    
    def get_available_transitions(self, booking):
        """
        Get list of valid transitions for current booking state.
        
        Args:
            booking: Booking object
            
        Returns:
            list: List of valid status strings
        """
        return self.STATE_TRANSITIONS.get(booking.status, [])
    
    def can_cancel(self, booking):
        """
        Check if booking can be cancelled.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if can be cancelled
        """
        return 'TEMPORARILY_CANCELLED' in self.get_available_transitions(booking)
    
    def can_reinstate(self, booking):
        """
        Check if booking can be reinstated.
        
        Args:
            booking: Booking object
            
        Returns:
            bool: True if can be reinstated
        """
        return booking.status == 'TEMPORARILY_CANCELLED'
    
    def is_terminal_state(self, status):
        """
        Check if status is a terminal state (no further transitions).
        
        Args:
            status: Status string
            
        Returns:
            bool: True if terminal state
        """
        return len(self.STATE_TRANSITIONS.get(status, [])) == 0
    
    def get_state_description(self, status):
        """
        Get human-readable description for status.
        
        Args:
            status: Status string
            
        Returns:
            str: Description
        """
        descriptions = {
            'INITIATED': 'Booking initiated and soft-locked',
            'UNDER_REVIEW': 'Under review by admin',
            'ASSIGNED_AWAITING': 'Room assigned, awaiting roommate',
            'CONFIRMED_ASSIGNED': 'Confirmed and assigned to room',
            'ACTIVE': 'Active booking',
            'TEMPORARILY_CANCELLED': 'Temporarily cancelled',
            'PERMANENTLY_CANCELLED': 'Permanently cancelled',
            'COMPLETED': 'Booking completed',
            'REJECTED': 'Booking rejected',
            'WAITLISTED': 'Waitlisted',
        }
        return descriptions.get(status, status)
