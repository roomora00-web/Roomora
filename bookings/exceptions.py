"""
Standardized booking system exceptions.
All booking-related errors should inherit from BookingError.
"""


class BookingError(Exception):
    """Base exception for all booking-related errors."""
    
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
            'details': self.details
        }


class SlotUnavailableError(BookingError):
    """Raised when a requested slot is not available."""
    
    def __init__(self, message: str = "The requested slot is no longer available", details: dict = None):
        super().__init__('SLOT_UNAVAILABLE', message, details)


class DuplicateBookingError(BookingError):
    """Raised when user attempts to create a duplicate active booking."""
    
    def __init__(self, message: str = "You already have an active booking", details: dict = None):
        super().__init__('DUPLICATE_BOOKING', message, details)


class ConsentExpiredError(BookingError):
    """Raised when consent deadline has expired."""
    
    def __init__(self, message: str = "Consent deadline has expired", details: dict = None):
        super().__init__('CONSENT_EXPIRED', message, details)


class InvalidStateTransitionError(BookingError):
    """Raised when attempting an invalid state transition."""
    
    def __init__(self, from_state: str, to_state: str, details: dict = None):
        message = f"Invalid state transition from {from_state} to {to_state}"
        if details is None:
            details = {'from_state': from_state, 'to_state': to_state}
        super().__init__('INVALID_STATE_TRANSITION', message, details)


class ValidationError(BookingError):
    """Raised when booking validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__('VALIDATION_ERROR', message, details)


class PricingError(BookingError):
    """Raised when pricing calculation fails."""
    
    def __init__(self, message: str = "Pricing calculation failed", details: dict = None):
        super().__init__('PRICING_ERROR', message, details)


class RoomAssignmentError(BookingError):
    """Raised when room assignment fails."""
    
    def __init__(self, message: str = "Room assignment failed", details: dict = None):
        super().__init__('ROOM_ASSIGNMENT_ERROR', message, details)


class CompatibilityError(BookingError):
    """Raised when compatibility calculation fails."""
    
    def __init__(self, message: str = "Compatibility calculation failed", details: dict = None):
        super().__init__('COMPATIBILITY_ERROR', message, details)


class SoftLockExpiredError(BookingError):
    """Raised when soft-lock has expired."""
    
    def __init__(self, message: str = "Booking soft-lock has expired", details: dict = None):
        super().__init__('SOFT_LOCK_EXPIRED', message, details)


class EmailVerificationRequiredError(BookingError):
    """Raised when user email is not verified."""
    
    def __init__(self, message: str = "Email verification required", details: dict = None):
        super().__init__('EMAIL_VERIFICATION_REQUIRED', message, details)
