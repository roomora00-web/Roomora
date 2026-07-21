from django.db import models
from django.conf import settings
from django.utils import timezone
from .constants import BillingModel, SemesterStructure, RoomStatus


class Booking(models.Model):
    # PART 11: Complete 17 Booking Statuses
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated (Soft Locked)'),
        ('LIFESTYLE_PENDING', 'Lifestyle Pending'),
        ('LIFESTYLE_COMPLETE', 'Lifestyle Complete'),
        ('AWAITING_COMPATIBILITY', 'Awaiting Compatibility'),
        ('AUTO_ASSIGNED', 'Auto Assigned'),
        ('CONSENT_PENDING', 'Consent Pending'),
        ('CONSENT_ACCEPTED', 'Consent Accepted'),
        ('TEMPORARILY_CANCELLED', 'Temporarily Cancelled'),
        ('REINSTATED', 'Reinstated'),
        ('ADMIN_PENDING', 'Admin Pending'),
        ('PAYMENT_REQUIRED', 'Payment Required'),
        ('PAYMENT_PROCESSING', 'Payment Processing'),
        ('PAYMENT_PENDING_VERIFICATION', 'Payment Pending Verification'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('PAYMENT_EXPIRED', 'Payment Expired'),
        ('PAYMENT_COMPLETE', 'Payment Complete'),
        ('CONFIRMED', 'Confirmed'),
        ('ACTIVE', 'Active'),
        ('VACATION_RESERVE', 'Vacation Reserve'),
        ('GRACE_PERIOD', 'Grace Period'),
        ('COMPLETED', 'Completed'),
        ('PERMANENTLY_CANCELLED', 'Permanently Cancelled'),
        ('EXPIRED', 'Expired'),
        ('ASSIGNED_AWAITING', 'Assigned - Awaiting Roommate'),
        ('CONFIRMED_ASSIGNED', 'Confirmed and Assigned'),
        ('UNDER_REVIEW', 'Under Review'),
        ('WAITING_CONSENT', 'Waiting Consent'),
        ('COMPATIBILITY_REVIEW', 'Compatibility Review'),
        ('WAITLISTED', 'Waitlisted'),
        ('REJECTED', 'Rejected'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('FAILED', 'Failed'),
    ]
    
    BOOKING_TYPE_CHOICES = [
        ('DIRECT', 'Direct Booking'),
        ('ROOMMATE_MATCH', 'Roommate Match'),
        ('AGENCY', 'Agency Booking'),
    ]
    
    BILLING_MODEL_CHOICES = [
        (BillingModel.SEMESTER_BASED.value, 'Semester-Based'),
        (BillingModel.MONTHLY_BASED.value, 'Monthly-Based'),
        (BillingModel.ANNUAL_BASED.value, 'Annual-Based'),
        (BillingModel.ACADEMIC_YEAR.value, 'Academic Year'),
    ]
    
    SEMESTER_STRUCTURE_CHOICES = [
        (SemesterStructure.CONTINUOUS_STAY.value, 'Continuous Stay (34 consecutive weeks)'),
        (SemesterStructure.SPLIT_STAY.value, 'Split Stay with Vacation Gap'),
    ]
    
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    accommodation_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='bookings')
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    room = models.ForeignKey('properties.Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES, default='DIRECT')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='INITIATED')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Billing Model Fields
    billing_model = models.CharField(max_length=20, choices=BILLING_MODEL_CHOICES, null=True, blank=True)
    
    # Phase 1: House Rules Acknowledgment (Part 14 naming)
    house_rules_acknowledged = models.BooleanField(default=False, help_text='User acknowledged property prohibited items/rules')
    house_rules_acknowledged_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when house rules were acknowledged')
    
    # Soft-lock expiration (48-hour window for completing booking)
    soft_lock_expires_at = models.DateTimeField(null=True, blank=True, help_text='When the soft-lock on the slot expires')
    soft_lock_released = models.BooleanField(default=False, help_text='Whether the soft lock has been released')
    reminder_sent = models.BooleanField(default=False, help_text='Has the 36-hour reminder been sent?')
    
    # Occupancy tracking for new booking flow
    occupancy_position = models.PositiveIntegerField(null=True, blank=True, help_text='Position in room (1=first occupant, 2=second, etc.)')
    is_first_occupant = models.BooleanField(default=False, help_text='Whether this is the first occupant in the room')
    
    # Lifestyle questionnaire progress (JSON field for partial answers)
    lifestyle_progress = models.JSONField(null=True, blank=True, help_text='Partial lifestyle questionnaire answers')
    
    # Phase 8: Temporary Cancellation Timers
    slot_hold_expires_at = models.DateTimeField(null=True, blank=True, help_text='6 hour slot hold after rejection')
    temp_cancel_expires_at = models.DateTimeField(null=True, blank=True, help_text='24 hour window to reinstate')
    
    # Part 7: Consent Workflow Fields (Part 14 naming)
    consent_status = models.CharField(max_length=20, choices=[
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='not_required', help_text='Consent status')
    consent_deadline = models.DateTimeField(null=True, blank=True, help_text='24-hour consent deadline')
    consent_given_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when consent was given')
    consent_rejected_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when consent was rejected')
    temp_cancelled_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when temporary cancellation occurred')
    reinstated_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when booking was reinstated')
    reinstatement_count = models.PositiveIntegerField(default=0, help_text='Number of times booking was reinstated')
    compatibility_result = models.JSONField(null=True, blank=True, help_text='Stored compatibility result data')
    
    # Reference number for support
    reference_number = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    
    # Dates (Rule 1: Student sets start, system sets end)
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text='Total duration in days')
    duration_months = models.PositiveIntegerField(null=True, blank=True)
    
    # Billing Model Duration Fields (Part 14 naming)
    semesters_selected = models.PositiveIntegerField(null=True, blank=True, help_text='Number of semesters (1-3) for Semester-Based or Academic Year')
    months_selected = models.PositiveIntegerField(null=True, blank=True, help_text='Number of months for Monthly-Based')
    years_selected = models.PositiveIntegerField(null=True, blank=True, help_text='Number of years (1 or 2) for Annual-Based')
    
    # Stay Structure (Part 14)
    stay_structure = models.CharField(max_length=30, choices=SEMESTER_STRUCTURE_CHOICES, null=True, blank=True, help_text='Continuous or Split stay')
    
    # Semester 2 Fields (Part 14)
    semester_2_start_date = models.DateField(null=True, blank=True, help_text='Semester 2 start date for split stays')
    semester_2_end_date = models.DateField(null=True, blank=True, help_text='Semester 2 end date')
    semester_2_cancelled = models.BooleanField(default=False, help_text='Whether Semester 2 was cancelled')
    semester_2_refund_issued = models.BooleanField(default=False, help_text='Whether refund was issued for cancelled S2')
    
    # Room Status State Machine (Part 7)
    room_status = models.CharField(max_length=30, choices=[(s.value, s.value) for s in RoomStatus], default='AVAILABLE', null=True, blank=True)
    grace_period_start = models.DateField(null=True, blank=True, help_text='Grace period start date')
    grace_period_end = models.DateField(null=True, blank=True, help_text='Grace period end date')
    overstay_start = models.DateTimeField(null=True, blank=True, help_text='Timestamp when overstay began')
    overstay_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Daily overstay charge rate')
    overstay_accrued = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Total overstay charges accrued')
    
    # Vacation Reserve Fields (Part 14)
    vacation_reserve_start = models.DateField(null=True, blank=True, help_text='Vacation reserve start date')
    vacation_reserve_end = models.DateField(null=True, blank=True, help_text='Vacation reserve end date')
    
    # Pricing (Part 14 naming)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Price per billing unit')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Total booking price')
    currency = models.CharField(max_length=3, default='GHS', help_text='Currency code')
    rental_period = models.CharField(max_length=20, choices=[
        ('semester', 'Semester'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual')
    ], null=True, blank=True, help_text='Rental period type')
    
    # Pricing (legacy fields - kept for backward compatibility)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Roommate matching (if applicable)
    preferred_roommates = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='preferred_roommate_bookings')
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    matched_with_booking_id = models.PositiveIntegerField(null=True, blank=True, help_text='ID of the booking this is matched with')
    lifestyle_assessment_required = models.BooleanField(default=False)
    lifestyle_assessment_completed = models.BooleanField(default=False)
    matching_timestamp = models.DateTimeField(null=True, blank=True, help_text='When compatibility was calculated')
    
    # Lifestyle Profile (Part 14)
    lifestyle_profile_id = models.PositiveIntegerField(null=True, blank=True, help_text='ID of lifestyle profile used')
    lifestyle_submitted_at = models.DateTimeField(null=True, blank=True, help_text='When lifestyle questionnaire was submitted')
    
    # Room assignment details (Part 14 naming)
    assigned_room = models.ForeignKey('properties.Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='tentative_bookings', help_text='Physical room assigned to this booking')
    occupancy = models.PositiveIntegerField(null=True, blank=True, help_text='How many share this room')
    
    # Cancellation details (Part 14)
    permanently_cancelled_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when permanently cancelled')
    cancellation_reason = models.CharField(max_length=500, null=True, blank=True, help_text='Reason for cancellation')
    cancellation_initiated_by = models.CharField(max_length=20, choices=[
        ('user', 'User'),
        ('system', 'System'),
        ('admin', 'Admin')
    ], null=True, blank=True, help_text='Who initiated the cancellation')
    refund_status = models.CharField(max_length=20, choices=[
        ('not_applicable', 'Not Applicable'),
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ], default='not_applicable', help_text='Refund status')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Refund amount')
    
    # Admin approval details (Part 14)
    admin_reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_bookings', help_text='Admin who reviewed this booking')
    admin_reviewed_at = models.DateTimeField(null=True, blank=True, help_text='When admin reviewed this booking')
    admin_notes = models.TextField(blank=True, help_text='Admin notes on approval/rejection')
    
    # Metadata
    version = models.PositiveIntegerField(default=1, help_text='Booking schema version')
    flags = models.JSONField(default=list, blank=True, help_text='Any issues/concerns')
    
    # Additional details
    special_requests = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Admin approval (legacy - keep for backward compatibility)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.id} - {self.tenant.email} - {self.accommodation_property.title}"
    
    def release_slots(self):
        """
        Clears the physical room assignment. 
        Note: The actual mathematical slot recalculation is now handled automatically 
        by the post_save and post_delete signals in recalculate_inventory_on_booking_change.
        """
        if self.assigned_room:
            self.assigned_room = None

    def delete(self, *args, **kwargs):
        """Release slots when a booking is physically deleted"""
        if self.status not in ['PERMANENTLY_CANCELLED', 'TEMPORARILY_CANCELLED', 'REJECTED']:
            self.release_slots()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Generate reference number on creation and handle cancellations"""
        if not self.reference_number:
            import random
            import string
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.digits, k=4))
            self.reference_number = f"SM-{date_str}-{random_str}"
            
        # Check if status is changing to cancelled
        if self.pk:
            old_booking = Booking.objects.get(pk=self.pk)
            if old_booking.status not in ['PERMANENTLY_CANCELLED', 'TEMPORARILY_CANCELLED', 'REJECTED'] and self.status in ['PERMANENTLY_CANCELLED', 'TEMPORARILY_CANCELLED', 'REJECTED']:
                self.release_slots()
                
        super().save(*args, **kwargs)

    def set_status(self, new_status, changed_by=None, note=None):
        """Update booking status and record the transition in the timeline."""
        previous = self.status
        self.status = new_status
        self.save()
        BookingStatusTimeline.objects.create(
            booking=self,
            previous_status=previous,
            new_status=new_status,
            triggered_by=changed_by if changed_by is not None else None,
            reason=note or ''
        )

    def add_timeline(self, previous_status, new_status, changed_by=None, note=''):
        BookingStatusTimeline.objects.create(
            booking=self,
            previous_status=previous_status,
            new_status=new_status,
            triggered_by=changed_by if changed_by is not None else None,
            reason=note
        )
    
    @property
    def is_active(self):
        return self.status in ['PENDING', 'APPROVED']
    
    @property
    def calculated_move_out(self):
        from datetime import timedelta
        if self.move_out_date:
            return self.move_out_date
        
        # Fallback to billing allocation
        if hasattr(self, 'billing_allocation'):
            ba = self.billing_allocation
            if getattr(ba, 'semester2_end', None):
                return ba.semester2_end
            elif getattr(ba, 'semester1_end', None):
                return ba.semester1_end
                
        # Fallback to raw duration_days calculation (for legacy bookings)
        if self.move_in_date and self.duration_days:
            return self.move_in_date + timedelta(days=self.duration_days)
            
        return None

    @property
    def days_remaining(self):
        from django.utils import timezone
        end_date = self.calculated_move_out
        if not end_date:
            return None
            
        today = timezone.now().date()
        if today > end_date:
            return 0
            
        delta = end_date - today
        return delta.days

    @property
    def calculated_duration_label(self):
        """
        Generate a human-readable duration label based on booking dates.
        Falls back to months_selected, years_selected, or duration_months if dates aren't available.
        """
        # If billing/rental period indicates semesters, prefer semester label
        if self.rental_period and 'semester' in str(self.rental_period).lower():
            if self.semesters_selected:
                return f"{self.semesters_selected} semester{'s' if self.semesters_selected > 1 else ''}"
            # try to infer from duration_days (17 weeks = 119 days per semester)
            if self.move_in_date and self.move_out_date:
                days = (self.move_out_date - self.move_in_date).days
                semesters = round(days / 119)
                if semesters >= 1:
                    return f"{semesters} semester{'s' if semesters > 1 else ''}"

        # General inference: if dates span roughly whole semesters, prefer semester label
        if self.move_in_date and self.move_out_date:
            days = (self.move_out_date - self.move_in_date).days
            # infer semesters if close to multiples of 119 days
            if days >= 112:
                inferred_semesters = int(round(days / 119))
                if inferred_semesters >= 1:
                    # check closeness (within 7 days) to avoid false positives
                    if abs(days - (inferred_semesters * 119)) <= 7:
                        return f"{inferred_semesters} semester{'s' if inferred_semesters > 1 else ''}"

        if self.move_in_date and self.move_out_date:
            days = (self.move_out_date - self.move_in_date).days
            months = round(days / 30.44)  # Average days per month
            years = days // 365

            if years > 0:
                return f"{years} year{'s' if years > 1 else ''}"
            elif months > 0:
                return f"{months} month{'s' if months > 1 else ''}"
            elif days > 0:
                return f"{days} day{'s' if days > 1 else ''}"
        
        # Fallback to stored selection fields
        if self.months_selected:
            return f"{self.months_selected} month{'s' if self.months_selected > 1 else ''}"
        elif self.years_selected:
            return f"{self.years_selected} year{'s' if self.years_selected > 1 else ''}"
        elif self.duration_months:
            return f"{self.duration_months} month{'s' if self.duration_months > 1 else ''}"
        
        return "—"
    
    @property
    def progress_percentage(self):
        from django.utils import timezone
        end_date = self.calculated_move_out
        start_date = self.move_in_date
        
        if not start_date or not end_date:
            return 0
            
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return 100
            
        today = timezone.now().date()
        if today < start_date:
            return 0
        if today > end_date:
            return 100
            
        days_passed = (today - start_date).days
        percentage = (days_passed / total_days) * 100
        return min(max(int(percentage), 0), 100)
    
    @property
    def remaining_balance(self):
        return self.total_amount - self.amount_paid
    
    @property
    def requires_roommate_matching(self):
        """Check if this booking requires roommate matching"""
        if self.room_type:
            # Check if room type has shared occupancy
            if self.room_type.occupancy_type in ['DOUBLE', 'TRIPLE', 'QUAD']:
                return True
        if self.unit_type:
            # Check if unit type allows shared apartment
            if self.unit_type.shared_apartment_allowed:
                return True
        return False
    
    def trigger_lifestyle_assessment(self):
        """Trigger lifestyle assessment for roommate matching"""
        if self.requires_roommate_matching:
            self.lifestyle_assessment_required = True
            self.save()
            return True
        return False
    
    def set_soft_lock(self, hours=48):
        """Set soft-lock on the booking with expiration"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.soft_lock_expires_at = timezone.now() + timedelta(hours=hours)
        self.save()
    
    def is_soft_lock_active(self):
        """Check if soft-lock is still active"""
        from django.utils import timezone
        
        if not self.soft_lock_expires_at:
            return False
        return timezone.now() < self.soft_lock_expires_at
    
    def is_soft_lock_expired(self):
        """Check if soft-lock has expired"""
        from django.utils import timezone
        
        if not self.soft_lock_expires_at:
            return True
        return timezone.now() >= self.soft_lock_expires_at
    
    def release_soft_lock(self):
        """Release soft-lock and update slot availability"""
        if self.is_soft_lock_active():
            if self.assigned_room:
                if self.assigned_room.pending_slots > 0:
                    self.assigned_room.pending_slots -= 1
                    self.assigned_room.save()
            else:
                # Fallback if no specific physical room was assigned
                if self.room_type and hasattr(self.room_type, 'available_slots'):
                    self.room_type.available_slots += 1
                    self.room_type.save()
                elif self.unit_type and hasattr(self.unit_type, 'available_units'):
                    self.unit_type.available_units += 1
                    self.unit_type.save()
        
        self.soft_lock_expires_at = None
        self.save()
    
    def unlock_lifestyle_profile(self):
        """Unlock lifestyle profile when booking is cancelled"""
        if hasattr(self.tenant, 'lifestyle_profile'):
            profile = self.tenant.lifestyle_profile
            if profile.is_locked:
                # Check if user has any other active bookings with locked profiles
                other_locked_bookings = Booking.objects.filter(
                    tenant=self.tenant,
                    status__in=['ACTIVE', 'CONFIRMED_ASSIGNED', 'APPROVED_ASSIGNED', 'BOTH_ACCEPTED']
                ).exclude(id=self.id)

                if not other_locked_bookings.exists():
                    # No other active bookings, unlock the profile
                    profile.is_locked = False
                    profile.save()
                return True
        return False
    
    def reserve_slot(self):
        """Reserve a slot by incrementing pending slots on a Room"""
        if self.assigned_room:
            # Physical room path
            if (self.assigned_room.occupied_slots + self.assigned_room.pending_slots) < self.assigned_room.total_slots:
                self.assigned_room.pending_slots += 1
                self.assigned_room.save()
                return True
            return False
            
        # Fallback to RoomType/UnitType
        if self.room_type:
            if hasattr(self.room_type, 'available_slots') and self.room_type.available_slots > 0:
                self.room_type.available_slots -= 1
                self.room_type.save()
                return True
        if self.unit_type:
            if hasattr(self.unit_type, 'available_units') and self.unit_type.available_units > 0:
                self.unit_type.available_units -= 1
                self.unit_type.save()
                return True
        return False


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('MOBILE_MONEY', 'Mobile Money'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Transaction details
    transaction_id = models.CharField(max_length=200, unique=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    receipt_number = models.CharField(max_length=200, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.booking.id} - {self.amount}"


class RoommateMatch(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='roommate_matches')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roommate_matches')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Compatibility breakdown
    sleep_compatibility = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cleanliness_compatibility = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    noise_compatibility = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    social_compatibility = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Matching criteria
    lifestyle_match = models.DecimalField(max_digits=5, decimal_places=2)
    schedule_match = models.DecimalField(max_digits=5, decimal_places=2)
    budget_match = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Responses
    user_response = models.TextField(blank=True)
    landlord_response = models.TextField(blank=True)
    
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'roommate_matches'
        verbose_name = 'Roommate Match'
        verbose_name_plural = 'Roommate Matches'
        unique_together = ['booking', 'user']
        ordering = ['-compatibility_score']
    
    def __str__(self):
        return f"Match: {self.booking.tenant.email} - {self.user.email} ({self.compatibility_score}%)"


class RoomAllocationEngine:
    """Service for allocating compatible roommates to shared accommodations"""
    
    @staticmethod
    def find_compatible_roommates(booking, min_compatibility=70):
        """Find compatible roommates for a booking"""
        from accounts.models import LifestyleProfile
        
        if not booking.requires_roommate_matching:
            return []
        
        # Get the tenant's lifestyle profile
        try:
            tenant_profile = LifestyleProfile.objects.get(user=booking.tenant)
        except LifestyleProfile.DoesNotExist:
            return []
        
        if not tenant_profile.is_complete:
            return []
        
        # Find other users with complete lifestyle profiles
        potential_roommates = LifestyleProfile.objects.filter(
            is_complete=True
        ).exclude(user=booking.tenant)
        
        compatible_matches = []
        
        for profile in potential_roommates:
            # Check gender preference
            if tenant_profile.gender_preference != 'ANY':
                if profile.user.profile.gender != tenant_profile.gender_preference:
                    continue
            
            # Calculate compatibility
            compatibility_score = tenant_profile.calculate_compatibility(profile)
            
            if compatibility_score >= min_compatibility:
                compatible_matches.append({
                    'user': profile.user,
                    'compatibility_score': compatibility_score,
                    'lifestyle_profile': profile
                })
        
        # Sort by compatibility score (highest first)
        compatible_matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return compatible_matches
    
    @staticmethod
    def create_roommate_matches(booking, min_compatibility=70):
        """Create roommate match records for a booking"""
        compatible_roommates = RoomAllocationEngine.find_compatible_roommates(
            booking, min_compatibility
        )
        
        matches = []
        for match_data in compatible_roommates:
            match = RoommateMatch.objects.create(
                booking=booking,
                user=match_data['user'],
                compatibility_score=match_data['compatibility_score'],
                lifestyle_match=match_data['compatibility_score'],
                schedule_match=85.0,  # Placeholder - calculate based on actual data
                budget_match=90.0,  # Placeholder - calculate based on actual data
            )
            matches.append(match)
        
        return matches
    
    @staticmethod
    def assign_roommate(booking, selected_user):
        """Assign a selected roommate to the booking"""
        # Find the match record
        match = RoommateMatch.objects.filter(
            booking=booking,
            user=selected_user,
            status='PENDING'
        ).first()
        
        if not match:
            return False
        
        # Update match status
        match.status = 'ACCEPTED'
        match.responded_at = timezone.now()
        match.save()
        
        # Update booking
        booking.booking_type = 'ROOMMATE_MATCH'
        booking.lifestyle_assessment_completed = True
        booking.compatibility_score = match.compatibility_score
        booking.save()
        
        # Add to preferred roommates
        booking.preferred_roommates.add(selected_user)
        
        return True


class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booking_requests')
    accommodation_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='booking_requests')
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_requests')
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_requests')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Request details
    preferred_move_in_date = models.DateField()
    preferred_duration_months = models.PositiveIntegerField()
    message = models.TextField()
    
    # Response
    response_message = models.TextField(blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_requests')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Converted to booking
    converted_to_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='original_request')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_requests'
        verbose_name = 'Booking Request'
        verbose_name_plural = 'Booking Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request {self.id} - {self.user.email} - {self.accommodation_property.title}"


class LeaseAgreement(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_SIGNATURE', 'Pending Signature'),
        ('SIGNED', 'Signed'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='lease_agreement')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    
    # Lease terms
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Document
    agreement_document = models.FileField(upload_to='lease_agreements/', blank=True, null=True)
    digital_signature = models.TextField(blank=True)  # Store signature data
    
    # Signatures
    tenant_signed = models.BooleanField(default=False)
    tenant_signed_at = models.DateTimeField(null=True, blank=True)
    landlord_signed = models.BooleanField(default=False)
    landlord_signed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional terms
    special_terms = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lease_agreements'
        verbose_name = 'Lease Agreement'
        verbose_name_plural = 'Lease Agreements'
    
    def __str__(self):
        return f"Lease {self.id} - Booking {self.booking.id}"


class BookingHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('MODIFIED', 'Modified'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('LEASE_SIGNED', 'Lease Signed'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_actions')
    
    # Previous values (for modifications)
    previous_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_history'
        verbose_name = 'Booking History'
        verbose_name_plural = 'Booking History'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - Booking {self.booking.id}"


class PropertySearch(models.Model):
    """Stores user search queries for recent search display and recommendations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_searches')
    
    # Search criteria
    city = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    room_type = models.CharField(max_length=50, blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'property_searches'
        verbose_name = 'Property Search'
        verbose_name_plural = 'Property Searches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        search_str = f"Search by {self.user.email}"
        if self.city:
            search_str += f" in {self.city}"
        if self.room_type:
            search_str += f" ({self.room_type})"
        return search_str


class RecentlyViewed(models.Model):
    """Tracks recently viewed properties for user activity and recommendations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='viewed_by')
    
    # Metadata
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recently_viewed'
        verbose_name = 'Recently Viewed'
        verbose_name_plural = 'Recently Viewed'
        ordering = ['-viewed_at']
        unique_together = [('user', 'property')]
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} viewed {self.property.title}"
    
    def save(self, *args, **kwargs):
        """Update viewed_at timestamp whenever record is accessed"""
        self.viewed_at = timezone.now()
        super().save(*args, **kwargs)


class BookingConsent(models.Model):
    """Track consent from both parties in a roommate match (Phase 6)"""
    CONSENT_STATUS_CHOICES = [
        ('PENDING', 'Pending Response'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='consent_record')
    
    # User (tenant) consent
    user_status = models.CharField(max_length=20, choices=CONSENT_STATUS_CHOICES, default='PENDING')
    user_responded_at = models.DateTimeField(null=True, blank=True)
    
    # Roommate consent (if applicable)
    roommate_status = models.CharField(max_length=20, choices=CONSENT_STATUS_CHOICES, default='PENDING')
    roommate_responded_at = models.DateTimeField(null=True, blank=True)
    
    # Consent deadline
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text='Consent expires after 24 hours if not accepted')
    
    # Notification tracking
    user_notified_at = models.DateTimeField(null=True, blank=True)
    roommate_notified_at = models.DateTimeField(null=True, blank=True)
    admin_notified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking_consents'
        verbose_name = 'Booking Consent'
        verbose_name_plural = 'Booking Consents'
    
    def __str__(self):
        return f"Consent for Booking {self.booking.id}"
    
    @property
    def both_accepted(self):
        """Check if both parties have accepted"""
        return (self.user_status == 'ACCEPTED' and 
                self.roommate_status == 'ACCEPTED')
    
    @property
    def is_expired(self):
        """Check if consent window has expired"""
        return timezone.now() > self.expires_at


class RoomAssignment(models.Model):
    """Track final room assignments after consent approval (Phase 6)"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='room_assignment')
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True)
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Assignment details
    assigned_room = models.ForeignKey('properties.Room', on_delete=models.CASCADE, related_name='assignments', help_text='The physical room assigned', null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='room_assignments')
    
    # Roommate assignments (if shared room) - changed to ManyToMany for multi-occupant support
    assigned_roommates = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='roommate_assignments')
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    moved_in_date = models.DateField(null=True, blank=True)
    moved_out_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'room_assignments'
        verbose_name = 'Room Assignment'
        verbose_name_plural = 'Room Assignments'
    
    def __str__(self):
        room_name = self.assigned_room.room_number if self.assigned_room else "Unassigned"
        return f"Assignment {self.booking.id} - Room {room_name}"
    
    @property
    def assigned_roommate(self):
        """Backwards compatibility - return first roommate if exists"""
        return self.assigned_roommates.first()


class BookingStatusTimeline(models.Model):
    """Audit trail for booking status transitions (Phase 6)"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='timeline')
    
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_transitions')
    triggered_by_type = models.CharField(
        max_length=20,
        choices=[('USER', 'User'), ('ADMIN', 'Admin'), ('SYSTEM', 'System')],
        default='SYSTEM'
    )
    
    # Reason/notes
    reason = models.TextField(blank=True, help_text='Why the status changed')
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_timeline'
        verbose_name = 'Booking Timeline Entry'
        verbose_name_plural = 'Booking Timeline Entries'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['booking', 'created_at']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking.id}: {self.previous_status or 'START'} → {self.new_status}"


class VisitRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='visit_requests')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='visit_requests')
    
    # Contact info (useful if user is a guest)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Visit Details
    visit_date = models.DateField()
    visit_time = models.TimeField()
    party_size = models.CharField(max_length=50)
    contact_method = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visit_requests'
        verbose_name = 'Visit Request'
        verbose_name_plural = 'Visit Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Visit to {self.property.title} by {self.name} on {self.visit_date}"


class HouseRulesAcknowledgment(models.Model):
    """Track house rules acknowledgment per session for booking prerequisites"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='house_rules_acknowledgments')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='house_rules_acknowledgments')
    
    # Session tracking
    session_key = models.CharField(max_length=100, blank=True, help_text='Session identifier for per-session acknowledgment')
    
    # Acknowledgment details
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'house_rules_acknowledgments'
        verbose_name = 'House Rules Acknowledgment'
        verbose_name_plural = 'House Rules Acknowledgments'
        ordering = ['-acknowledged_at']
        indexes = [
            models.Index(fields=['user', 'property', '-acknowledged_at']),
            models.Index(fields=['session_key', '-acknowledged_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} acknowledged rules for {self.property.title}"
    
    @classmethod
    def is_valid_for_session(cls, user, property_id, session_key, max_age_hours=24):
        """Check if there's a valid acknowledgment within the current session"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        if session_key:
            # Check for session-specific acknowledgment
            acknowledgment = cls.objects.filter(
                user=user,
                property_id=property_id,
                session_key=session_key,
                acknowledged_at__gte=cutoff_time
            ).first()
        else:
            # Fallback to recent acknowledgment without session
            acknowledgment = cls.objects.filter(
                user=user,
                property_id=property_id,
                acknowledged_at__gte=cutoff_time
            ).first()
        
        return acknowledgment is not None


class RoomSetupDeclaration(models.Model):
    """Phase 11: Room Setup Declarations for shared rooms"""
    CATEGORY_CHOICES = [
        ('ELECTRICAL', 'Electrical Appliance'),
        ('FURNITURE', 'Furniture'),
        ('PERSONAL', 'Personal Equipment'),
        ('OTHER', 'Other'),
    ]
    
    CONSUMPTION_CHOICES = [
        ('HIGH', 'High Consumption'),
        ('MEDIUM', 'Medium Consumption'),
        ('LOW', 'Low Consumption'),
        ('NONE', 'Not Applicable'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='setup_declarations')
    room_assignment = models.ForeignKey('RoomAssignment', on_delete=models.CASCADE, related_name='declarations')
    
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # System assigned
    consumption_level = models.CharField(max_length=20, choices=CONSUMPTION_CHOICES, default='NONE')
    is_flagged = models.BooleanField(default=False, help_text='Flagged if violates property house rules')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'room_setup_declarations'
        verbose_name = 'Room Setup Declaration'
        verbose_name_plural = 'Room Setup Declarations'
        
    def __str__(self):
        return f"{self.user.email} - {self.item_name}"


class ConflictReport(models.Model):
    """Phase 13: Conflict Resolution reporting"""
    ISSUE_CHOICES = [
        ('NOISE', 'Noise'),
        ('CLEANLINESS', 'Cleanliness'),
        ('VISITORS', 'Visitors'),
        ('ITEMS', 'Items/Appliances'),
        ('PERSONAL', 'Personal Conflict'),
        ('OTHER', 'Other'),
    ]
    
    RESOLUTION_CHOICES = [
        ('MEDIATION', 'Mediation'),
        ('TRANSFER', 'Room Transfer'),
        ('LEASE_REVIEW', 'Lease Review'),
        ('ADMIN_CONTACT', 'Admin Contact'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_conflicts')
    room_assignment = models.ForeignKey('RoomAssignment', on_delete=models.CASCADE, related_name='conflict_reports')
    
    issue_type = models.CharField(max_length=20, choices=ISSUE_CHOICES)
    description = models.TextField()
    attempted_direct_resolution = models.BooleanField(default=False)
    preferred_resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conflict_reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Conflict Report: {self.get_issue_type_display()} by {self.reporter.email}"

class RoomMessage(models.Model):
    """Phase 11: Room Discussion Thread"""
    room_assignment = models.ForeignKey('RoomAssignment', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='room_messages', null=True, blank=True)
    is_system = models.BooleanField(default=False)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'room_messages'
        verbose_name = 'Room Message'
        verbose_name_plural = 'Room Messages'
        ordering = ['created_at']
        
    def __str__(self):
        if self.is_system:
            return f"System Message at {self.created_at}"
        return f"Message by {self.sender.email if self.sender else 'Unknown'} at {self.created_at}"

class LifestyleProfileLockLog(models.Model):
    ACTION_CHOICES = [
        ('LOCKED', 'Locked'),
        ('UNLOCKED', 'Unlocked'),
        ('ADMIN_UNLOCK_REQUESTED', 'Admin Unlock Requested'),
        ('ADMIN_UNLOCK_APPROVED', 'Admin Unlock Approved'),
        ('ADMIN_UNLOCK_DENIED', 'Admin Unlock Denied'),
    ]
    
    lifestyle_profile = models.ForeignKey('accounts.LifestyleProfile', on_delete=models.CASCADE, related_name='lock_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lifestyle_lock_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    triggered_by_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_lock_actions')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'lifestyle_lock_logs'
        verbose_name = 'Lifestyle Profile Lock Log'
        verbose_name_plural = 'Lifestyle Profile Lock Logs'
        ordering = ['-created_at']



class CompatibilityScore(models.Model):
    """Stores the calculated compatibility between a booking and an existing occupant."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='compatibility_scores')
    roommate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_compatibility_scores')
    
    score = models.DecimalField(max_digits=5, decimal_places=2)
    high_priority_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    medium_priority_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    low_priority_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    alignment_summary = models.TextField(blank=True)
    difference_summary = models.TextField(blank=True)
    
    routing_decision = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compatibility_scores'
        verbose_name = 'Compatibility Score'
        verbose_name_plural = 'Compatibility Scores'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking.tenant.email} & {self.roommate.email} - {self.score}%"

class BillingAllocation(models.Model):
    """Stores billing and pricing allocation for a booking."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='billing_allocation')
    
    # Billing model
    billing_model = models.CharField(max_length=50, choices=Booking.BILLING_MODEL_CHOICES)
    
    # Duration parameters
    num_semesters = models.IntegerField(null=True, blank=True)
    num_months = models.IntegerField(null=True, blank=True)
    num_years = models.IntegerField(null=True, blank=True)
    
    # Semester structure (for academic year)
    semester_structure = models.CharField(max_length=50, choices=Booking.SEMESTER_STRUCTURE_CHOICES, null=True, blank=True)
    
    # Vacation gap dates (for split stay)
    vacation_gap_start = models.DateField(null=True, blank=True)
    vacation_gap_end = models.DateField(null=True, blank=True)
    
    # Semester dates
    semester1_end = models.DateField(null=True, blank=True)
    semester2_start = models.DateField(null=True, blank=True)
    semester2_end = models.DateField(null=True, blank=True)
    
    # Pricing
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Duration tracking
    total_duration_weeks = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_allocations'
        verbose_name = 'Billing Allocation'
        verbose_name_plural = 'Billing Allocations'
    
    def __str__(self):
        return f"{self.booking.reference_number} - {self.billing_model}"


class RoomAllocation(models.Model):
    """Stores room allocation details for a booking."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='room_allocation')
    
    # Room/unit type
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True)
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Physical room assignment
    assigned_room = models.ForeignKey('properties.Room', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Occupancy type
    occupancy_type = models.CharField(max_length=20, null=True, blank=True)
    
    # Slot number (if applicable)
    slot_number = models.IntegerField(null=True, blank=True)
    
    # Allocation status
    ALLOCATION_STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('CONFIRMED', 'Confirmed'),
        ('RELEASED', 'Released'),
    ]
    allocation_status = models.CharField(max_length=20, choices=ALLOCATION_STATUS_CHOICES, default='RESERVED')
    
    # Timestamps
    allocated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'room_allocations'
        verbose_name = 'Room Allocation'
        verbose_name_plural = 'Room Allocations'
    
    def __str__(self):
        return f"{self.booking.reference_number} - {self.allocation_status}"


class ConsentRecord(models.Model):
    """Stores consent records for roommate matching."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='new_consent_record')
    
    # User consent
    user_consent = models.BooleanField(default=False)
    user_consent_date = models.DateTimeField(null=True, blank=True)
    user_consent_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Roommate consent
    roommate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_consent_records')
    roommate_consent = models.BooleanField(default=False)
    roommate_consent_date = models.DateTimeField(null=True, blank=True)
    roommate_consent_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Consent deadline
    consent_deadline = models.DateTimeField(null=True, blank=True)
    
    # Consent status
    CONSENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('USER_CONSENTED', 'User Consented'),
        ('ROOMMATE_CONSENTED', 'Roommate Consented'),
        ('BOTH_CONSENTED', 'Both Consented'),
        ('EXPIRED', 'Expired'),
        ('REJECTED', 'Rejected'),
    ]
    consent_status = models.CharField(max_length=20, choices=CONSENT_STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'consent_records'
        verbose_name = 'Consent Record'
        verbose_name_plural = 'Consent Records'
    
    def __str__(self):
        return f"{self.booking.reference_number} - {self.consent_status}"


class BookingDraft(models.Model):
    """Stores booking draft data to replace session-based storage."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booking_drafts')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='booking_drafts')
    
    # Room/unit selection
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey('properties.Room', on_delete=models.SET_NULL, null=True, blank=True)
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Duration selection
    billing_model = models.CharField(max_length=50, choices=Booking.BILLING_MODEL_CHOICES, null=True, blank=True)
    move_in_date = models.DateField(null=True, blank=True)
    num_semesters = models.IntegerField(null=True, blank=True)
    num_months = models.IntegerField(null=True, blank=True)
    num_years = models.IntegerField(null=True, blank=True)
    
    # Semester structure
    semester_structure = models.CharField(max_length=50, choices=Booking.SEMESTER_STRUCTURE_CHOICES, null=True, blank=True)
    vacation_gap_end = models.DateField(null=True, blank=True)
    
    # Temporary data (JSON for flexibility)
    temporary_data = models.JSONField(default=dict, blank=True)
    
    # Status
    DRAFT_STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
        ('CONVERTED', 'Converted to Booking'),
    ]
    status = models.CharField(max_length=20, choices=DRAFT_STATUS_CHOICES, default='IN_PROGRESS')
    
    # Expiration (48 hours)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Final booking reference (if converted)
    final_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_drafts'
        verbose_name = 'Booking Draft'
        verbose_name_plural = 'Booking Drafts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Draft for {self.user.email} - {self.property.name}"
    
    def is_expired(self):
        """Check if draft has expired."""
        if self.expires_at and self.expires_at < timezone.now():
            return True
    alignment_summary = models.TextField(blank=True)
    difference_summary = models.TextField(blank=True)
    
    routing_decision = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compatibility_scores'
        verbose_name = 'Compatibility Score'
        verbose_name_plural = 'Compatibility Scores'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking.tenant.email} & {self.roommate.email} - {self.score}%"

class BillingAllocation(models.Model):
    """Stores billing and pricing allocation for a booking."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='billing_allocation')
    
    # Billing model
    billing_model = models.CharField(max_length=50, choices=Booking.BILLING_MODEL_CHOICES)
    
    # Duration parameters
    num_semesters = models.IntegerField(null=True, blank=True)
    num_months = models.IntegerField(null=True, blank=True)
    num_years = models.IntegerField(null=True, blank=True)
    
    # Semester structure (for academic year)
    semester_structure = models.CharField(max_length=50, choices=Booking.SEMESTER_STRUCTURE_CHOICES, null=True, blank=True)
    
    # Vacation gap dates (for split stay)
    vacation_gap_start = models.DateField(null=True, blank=True)
    vacation_gap_end = models.DateField(null=True, blank=True)
    
    # Semester dates
    semester1_end = models.DateField(null=True, blank=True)
    semester2_start = models.DateField(null=True, blank=True)
    semester2_end = models.DateField(null=True, blank=True)
    
    # Pricing
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Duration tracking
    total_duration_weeks = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_allocations'
        verbose_name = 'Billing Allocation'
        verbose_name_plural = 'Billing Allocations'
    
    def __str__(self):
        return f"{self.booking.reference_number} - {self.billing_model}"


class RoomAllocation(models.Model):
    """Stores room allocation details for a booking."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='room_allocation')
    
    # Room/unit type
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True)
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Physical room assignment
    assigned_room = models.ForeignKey('properties.Room', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Occupancy type
    occupancy_type = models.CharField(max_length=20, null=True, blank=True)
    
    # Slot number (if applicable)
    slot_number = models.IntegerField(null=True, blank=True)
    
    # Allocation status
    ALLOCATION_STATUS_CHOICES = [
        ('RESERVED', 'Reserved'),
        ('CONFIRMED', 'Confirmed'),
        ('RELEASED', 'Released'),
    ]
    allocation_status = models.CharField(max_length=20, choices=ALLOCATION_STATUS_CHOICES, default='RESERVED')
    
    # Timestamps
    allocated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'room_allocations'
        verbose_name = 'Room Allocation'
        verbose_name_plural = 'Room Allocations'
    
    def __str__(self):
        return f"{self.booking.reference_number} - {self.allocation_status}"


class ConsentRecord(models.Model):
    """Stores consent records for roommate matching."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='new_consent_record')
    
    # User consent
    user_consent = models.BooleanField(default=False)
    user_consent_date = models.DateTimeField(null=True, blank=True)
    user_consent_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Roommate consent
    roommate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_consent_records')
    roommate_consent = models.BooleanField(default=False)
    roommate_consent_date = models.DateTimeField(null=True, blank=True)
    roommate_consent_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Consent deadline
    consent_deadline = models.DateTimeField(null=True, blank=True)
    
    # Consent status
    CONSENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('USER_CONSENTED', 'User Consented'),
        ('ROOMMATE_CONSENTED', 'Roommate Consented'),
        ('BOTH_CONSENTED', 'Both Consented'),
        ('EXPIRED', 'Expired'),
        ('REJECTED', 'Rejected'),
    ]
    consent_status = models.CharField(max_length=20, choices=CONSENT_STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'consent_records'
        verbose_name = 'Consent Record'
        verbose_name_plural = 'Consent Records'
    
    def __str__(self):
        return f"{self.booking.reference_number} - {self.consent_status}"


class BookingDraft(models.Model):
    """Stores booking draft data to replace session-based storage."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booking_drafts')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='booking_drafts')
    
    # Room/unit selection
    room_type = models.ForeignKey('properties.RoomType', on_delete=models.SET_NULL, null=True, blank=True)
    unit_type = models.ForeignKey('properties.UnitType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Duration selection
    billing_model = models.CharField(max_length=50, choices=Booking.BILLING_MODEL_CHOICES, null=True, blank=True)
    move_in_date = models.DateField(null=True, blank=True)
    num_semesters = models.IntegerField(null=True, blank=True)
    num_months = models.IntegerField(null=True, blank=True)
    num_years = models.IntegerField(null=True, blank=True)
    
    # Semester structure
    semester_structure = models.CharField(max_length=50, choices=Booking.SEMESTER_STRUCTURE_CHOICES, null=True, blank=True)
    vacation_gap_end = models.DateField(null=True, blank=True)
    
    # Temporary data (JSON for flexibility)
    temporary_data = models.JSONField(default=dict, blank=True)
    
    # Status
    DRAFT_STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
        ('CONVERTED', 'Converted to Booking'),
    ]
    status = models.CharField(max_length=20, choices=DRAFT_STATUS_CHOICES, default='IN_PROGRESS')
    
    # Expiration (48 hours)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Final booking reference (if converted)
    final_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_drafts'
        verbose_name = 'Booking Draft'
        verbose_name_plural = 'Booking Drafts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Draft for {self.user.email} - {self.property.name}"
    
    def is_expired(self):
        """Check if draft has expired."""
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Booking)
@receiver(post_delete, sender=Booking)
def recalculate_inventory_on_booking_change(sender, instance, **kwargs):
    """
    Robustly recalculate all related inventory slots anytime a booking is 
    created, updated, or deleted, guaranteeing mathematical consistency.
    """
    if instance.room_type:
        instance.room_type.recalculate_capacity()
    if instance.unit_type:
        instance.unit_type.recalculate_capacity()
    if instance.assigned_room:
        instance.assigned_room.recalculate_occupancy()

class AdminBookingQueue(Booking):
    """
    Proxy model to allow adding the Admin Booking Queue to the Django Admin sidebar natively.
    """
    class Meta:
        proxy = True
        verbose_name = 'Admin Booking Queue'
        verbose_name_plural = 'Admin Booking Queue'
