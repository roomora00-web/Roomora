"""
Billing Model Constants and Configuration

This module contains the immutable constants for the billing system as per specification:
- Rule 1: Student sets start, system sets end
- Rule 2: One semester is exactly 17 weeks
- Rule 3: Admin controls all pricing and configuration
"""

from enum import Enum


class BillingModel(str, Enum):
    """The four billing models as per specification"""
    SEMESTER_BASED = "SEMESTER_BASED"
    MONTHLY_BASED = "MONTHLY_BASED"
    ANNUAL_BASED = "ANNUAL_BASED"
    ACADEMIC_YEAR = "ACADEMIC_YEAR"


class SemesterStructure(str, Enum):
    """Semester structure options for Model D (Academic Year)"""
    CONTINUOUS_STAY = "CONTINUOUS_STAY"  # 34 consecutive weeks
    SPLIT_STAY = "SPLIT_STAY"  # Split with vacation gap


class RoomStatus(str, Enum):
    """Room status state machine as per Part 7"""
    AVAILABLE = "AVAILABLE"
    SOFT_LOCKED = "SOFT_LOCKED"
    OCCUPIED = "OCCUPIED"
    FULLY_OCCUPIED = "FULLY_OCCUPIED"
    VACATION_RESERVE = "VACATION_RESERVE"
    PRACTICAL_CHECKOUT = "PRACTICAL_CHECKOUT"  # Subset of Vacation Reserve
    GRACE_PERIOD = "GRACE_PERIOD"
    OVERSTAY = "OVERSTAY"
    MAINTENANCE = "MAINTENANCE"
    ARCHIVED = "ARCHIVED"


# Rule 2: Universal semester constant
SEMESTER_WEEKS = 17
SEMESTER_DAYS = SEMESTER_WEEKS * 7  # 119 days

# Academic Year = 2 semesters
ACADEMIC_YEAR_WEEKS = SEMESTER_WEEKS * 2  # 34 weeks
ACADEMIC_YEAR_DAYS = SEMESTER_DAYS * 2  # 238 days

# Annual billing constant
WEEKS_PER_YEAR = 52
DAYS_PER_YEAR = WEEKS_PER_YEAR * 7  # 364 days

# Monthly billing constant
DAYS_PER_MONTH = 30

# Grace period constants (Part 8)
DEFAULT_GRACE_PERIOD_DAYS = 7
MIN_GRACE_PERIOD_DAYS = 3
MAX_GRACE_PERIOD_DAYS = 14

# Practical checkout window for split stay (Part 8.3)
PRACTICAL_CHECKOUT_HOURS = 48

# Overstay constants (Part 9)
DEFAULT_OVERSTAY_MULTIPLIER = 1.5
MIN_OVERSTAY_MULTIPLIER = 1.0
MAX_OVERSTAY_MULTIPLIER = 2.0

# Overstay escalation thresholds (Part 9.3)
OVERSTAY_ESCALATION_DAYS = 15  # Day 15 triggers admin escalation

# Vacation Reserve no-return escalation (Part 10.2 Rule 6)
VACATION_RESERVE_NO_RETURN_ESCALATION_DAYS = 15

# Pre-expiry reminder schedule (Part 11.1)
PRE_EXPIRY_REMINDER_WEEKS = [4, 2, 1]  # 4 weeks, 2 weeks, 1 week before
PRE_EXPIRY_REMINDER_DAYS = [3, 0]  # 3 days before, day of expiry
GRACE_PERIOD_REMINDER_DAYS = [3, 6]  # Day 3 and Day 6 of grace period

# Property type to billing model compatibility
PROPERTY_TYPE_BILLING_COMPATIBILITY = {
    'HOSTEL': [
        BillingModel.SEMESTER_BASED,
        BillingModel.MONTHLY_BASED,
    ],
    'APARTMENT': [
        BillingModel.SEMESTER_BASED,
        BillingModel.MONTHLY_BASED,
        BillingModel.ACADEMIC_YEAR,
        BillingModel.ANNUAL_BASED,
    ],
    'FLAT': [
        BillingModel.SEMESTER_BASED,
        BillingModel.MONTHLY_BASED,
        BillingModel.ACADEMIC_YEAR,
        BillingModel.ANNUAL_BASED,
    ],
    'COMPOUND_HOUSE': [
        BillingModel.MONTHLY_BASED,
        BillingModel.ANNUAL_BASED,
    ],
    'TOWNHOUSE': [
        BillingModel.MONTHLY_BASED,
        BillingModel.ANNUAL_BASED,
    ],
    'DUPLEX': [
        BillingModel.MONTHLY_BASED,
        BillingModel.ANNUAL_BASED,
    ],
    'VILLA': [
        BillingModel.MONTHLY_BASED,
        BillingModel.ANNUAL_BASED,
    ],
    'STUDIO': [
        BillingModel.SEMESTER_BASED,
        BillingModel.MONTHLY_BASED,
        BillingModel.ACADEMIC_YEAR,
        BillingModel.ANNUAL_BASED,
    ],
    'STUDENT_APARTMENT': [
        BillingModel.SEMESTER_BASED,
        BillingModel.MONTHLY_BASED,
        BillingModel.ACADEMIC_YEAR,
    ],
}

# Billing model descriptions for UI
BILLING_MODEL_DESCRIPTIONS = {
    BillingModel.SEMESTER_BASED: "Pay per 17-week semester. Select 1-3 semesters.",
    BillingModel.MONTHLY_BASED: "Pay per calendar month. Flexible duration with extension options.",
    BillingModel.ANNUAL_BASED: "Pay for 52-week year. Long-term commitment with optional 2-year advance.",
    BillingModel.ACADEMIC_YEAR: "Combined 2-semester (34-week) rate with discount. Requires semester structure selection.",
}

# Default configurations
DEFAULT_MAX_SEMESTERS = 3  # Maximum semesters bookable at once
DEFAULT_MIN_MONTHS = 1  # Minimum months for monthly booking
DEFAULT_MAX_MONTHS = 12  # Maximum months bookable at once for monthly
