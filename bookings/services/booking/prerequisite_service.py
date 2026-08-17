"""
Booking Prerequisite Validation Service

Validates all prerequisites before a booking can be initiated according to the new booking flow specification.

Prerequisites:
1. Authentication - User must be logged in
2. Email Verification - User's email must be verified
3. Phone Verification - User's phone must be verified
4. Account Status - Account must be Active (not suspended/deactivated)
5. No Unresolved Overstay - User must not have unresolved overstay on any previous booking
"""

from typing import Dict, Tuple, Optional
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accounts.models import User
from bookings.models import Booking


class PrerequisiteCheckResult:
    """Result of a prerequisite check"""
    
    def __init__(self, passed: bool, message: str, redirect_url: Optional[str] = None):
        self.passed = passed
        self.message = message
        self.redirect_url = redirect_url
    
    def to_dict(self) -> Dict:
        return {
            'passed': self.passed,
            'message': self.message,
            'redirect_url': self.redirect_url
        }


class PrerequisiteService:
    """Service for validating booking prerequisites"""
    
    @staticmethod
    def check_authentication(user: Optional[User]) -> PrerequisiteCheckResult:
        """
        Prerequisite 1: Authentication
        User must be logged in to an active StayMatch account.
        """
        if user is None or not user.is_authenticated:
            return PrerequisiteCheckResult(
                passed=False,
                message="You must be logged in to book a property.",
                redirect_url="/login/"
            )
        
        if not user.is_active:
            return PrerequisiteCheckResult(
                passed=False,
                message="Your account is not active. Please contact support.",
                redirect_url="/"
            )
        
        return PrerequisiteCheckResult(
            passed=True,
            message="Authentication verified."
        )
    
    @staticmethod
    def check_email_verification(user: User) -> PrerequisiteCheckResult:
        """
        Prerequisite 2: Email Verification
        User's email address must be verified.
        """
        if not user.email_verified:
            return PrerequisiteCheckResult(
                passed=False,
                message="Please verify your email address before booking.",
                redirect_url="/verify-email/"
            )
        
        return PrerequisiteCheckResult(
            passed=True,
            message="Email verified."
        )
    

    @staticmethod
    def check_account_status(user: User) -> PrerequisiteCheckResult:
        """
        Prerequisite 4: Account Status
        User's account must be in Active status.
        Suspended or deactivated accounts cannot initiate bookings.
        """
        if user.is_deactivated:
            return PrerequisiteCheckResult(
                passed=False,
                message="Your account has been deactivated. Please contact support.",
                redirect_url="/contact-support/"
            )
        
        if user.account_status in ['DISABLED', 'UNDER_REVIEW']:
            status_display = user.get_account_status_display()
            return PrerequisiteCheckResult(
                passed=False,
                message=f"Your account status is {status_display}. Please contact support.",
                redirect_url="/contact-support/"
            )
        
        return PrerequisiteCheckResult(
            passed=True,
            message="Account status is active."
        )
    
    @staticmethod
    def check_overstay_status(user: User) -> PrerequisiteCheckResult:
        """
        Prerequisite 5: No Unresolved Overstay
        If the user has an unresolved overstay on any previous booking,
        their ability to make new bookings is suspended.
        """
        if user.has_unresolved_overstay:
            return PrerequisiteCheckResult(
                passed=False,
                message="You have an unresolved overstay on a previous booking. Please contact support to resolve this before making new bookings.",
                redirect_url="/contact-support/"
            )
        
        # Also check for any active bookings in overstay status
        overstay_bookings = Booking.objects.filter(
            tenant=user,
            room_status='OVERSTAY'
        ).exists()
        
        if overstay_bookings:
            return PrerequisiteCheckResult(
                passed=False,
                message="You have an unresolved overstay on a previous booking. Please contact support to resolve this before making new bookings.",
                redirect_url="/contact-support/"
            )
        
        return PrerequisiteCheckResult(
            passed=True,
            message="No unresolved overstay."
        )
    
    @staticmethod
    def check_existing_bookings(user: User) -> PrerequisiteCheckResult:
        """
        Prerequisite 6: No Existing Active Booking
        Users cannot hold multiple active or pending bookings simultaneously.
        """
        active_bookings = Booking.objects.filter(tenant=user).exclude(
            status__in=['COMPLETED', 'PERMANENTLY_CANCELLED', 'TEMPORARILY_CANCELLED', 'EXPIRED', 'REJECTED', 'CANCELLED']
        )
        
        if active_bookings.exists():
            return PrerequisiteCheckResult(
                passed=False,
                message="You already have an active or pending booking. You cannot initiate another booking.",
                redirect_url="/api/bookings/bookings/my_bookings/"
            )
            
        return PrerequisiteCheckResult(
            passed=True,
            message="No existing active bookings."
        )
    
    @staticmethod
    def validate_all_prerequisites(user: Optional[User]) -> Tuple[bool, Dict]:
        """
        Validate all five prerequisites simultaneously.
        Returns tuple of (all_passed, results_dict)
        """
        results = {}
        
        # Check authentication first (required for other checks)
        auth_result = PrerequisiteService.check_authentication(user)
        results['authentication'] = auth_result.to_dict()
        
        if not auth_result.passed:
            return False, results
        
        # Check remaining prerequisites
        results['email_verification'] = PrerequisiteService.check_email_verification(user).to_dict()
        results['account_status'] = PrerequisiteService.check_account_status(user).to_dict()
        results['overstay_status'] = PrerequisiteService.check_overstay_status(user).to_dict()
        results['existing_bookings'] = PrerequisiteService.check_existing_bookings(user).to_dict()
        
        # Check if all passed
        all_passed = all(result['passed'] for result in results.values())
        
        return all_passed, results
    
    @staticmethod
    def get_first_failed_prerequisite(user: Optional[User]) -> Optional[PrerequisiteCheckResult]:
        """
        Get the first failed prerequisite check.
        Returns None if all prerequisites pass.
        """
        auth_result = PrerequisiteService.check_authentication(user)
        if not auth_result.passed:
            return auth_result
        
        email_result = PrerequisiteService.check_email_verification(user)
        if not email_result.passed:
            return email_result
        
        account_result = PrerequisiteService.check_account_status(user)
        if not account_result.passed:
            return account_result
        
        overstay_result = PrerequisiteService.check_overstay_status(user)
        if not overstay_result.passed:
            return overstay_result
            
        existing_result = PrerequisiteService.check_existing_bookings(user)
        if not existing_result.passed:
            return existing_result
        
        return None
