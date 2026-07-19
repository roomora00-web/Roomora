from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import secrets


class PaymentRecord(models.Model):
    """
    Payment record model for StayMatch payment system.
    Stores all payment information including gateway responses, refunds, and disbursements.
    """
    
    PAYMENT_METHOD_CHOICES = [
        ('mtn_momo', 'MTN Mobile Money'),
        ('vodafone_cash', 'Vodafone Cash'),
        ('airteltigo_money', 'AirtelTigo Money'),
        ('card_visa', 'Visa Card'),
        ('card_mastercard', 'Mastercard'),
        ('card_verve', 'Verve Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('pending_verification', 'Pending Verification'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='payment_records')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_records')
    
    # Payment references
    payment_reference = models.CharField(max_length=100, unique=True, editable=False)
    gateway_reference = models.CharField(max_length=200, null=True, blank=True, help_text='Paystack transaction ID')
    
    # Amount breakdown
    amount_accommodation = models.DecimalField(max_digits=10, decimal_places=2, help_text='Amount going to landlord')
    amount_platform_fee = models.DecimalField(max_digits=10, decimal_places=2, help_text='StayMatch commission (5%)')
    amount_total = models.DecimalField(max_digits=10, decimal_places=2, help_text='Total charged to user')
    currency = models.CharField(max_length=3, default='GHS')
    
    # Payment method and status
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='initiated')
    
    # Attempt tracking
    attempt_count = models.IntegerField(default=0, help_text='Number of payment attempts')
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=500, null=True, blank=True)
    
    # Payment window timing
    payment_window_opens_at = models.DateTimeField(help_text='When payment window opens')
    payment_window_closes_at = models.DateTimeField(help_text='2-hour payment deadline')
    paid_at = models.DateTimeField(null=True, blank=True, help_text='When payment was successfully completed')
    
    # Gateway response (stored for records)
    gateway_response = models.JSONField(null=True, blank=True, help_text='Full Paystack response')
    
    # Refund tracking
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_initiated_at = models.DateTimeField(null=True, blank=True)
    refund_completed_at = models.DateTimeField(null=True, blank=True)
    refund_gateway_reference = models.CharField(max_length=200, null=True, blank=True)
    refund_reason = models.CharField(max_length=500, null=True, blank=True)
    
    # Disbursement to landlord
    disbursed_to_landlord = models.BooleanField(default=False)
    disbursement_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    disbursed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='disbursements_made')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staymatch_payment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['user']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['payment_window_closes_at'], name='idx_payment_window_close'),
        ]
    
    def __str__(self):
        return f"{self.payment_reference} - {self.payment_status} - {self.amount_total} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = self.generate_payment_reference()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_payment_reference():
        """Generate unique payment reference like PAY-20250315-0847"""
        timestamp = timezone.now().strftime('%Y%m%d')
        random_suffix = secrets.token_hex(3).upper()[:6]
        return f"PAY-{timestamp}-{random_suffix}"
    
    @property
    def time_remaining_seconds(self):
        """Calculate remaining time in payment window"""
        if self.payment_status in ['completed', 'refunded', 'partially_refunded']:
            return 0
        if timezone.now() > self.payment_window_closes_at:
            return 0
        remaining = self.payment_window_closes_at - timezone.now()
        return int(remaining.total_seconds())
    
    @property
    def can_retry(self):
        """Check if user can retry payment"""
        if self.payment_status in ['completed', 'refunded', 'partially_refunded', 'expired']:
            return False
        if timezone.now() > self.payment_window_closes_at:
            return False
        return True
    
    @property
    def is_expired(self):
        """Check if payment window has expired"""
        return timezone.now() > self.payment_window_closes_at and self.payment_status not in ['completed', 'refunded', 'partially_refunded']
