from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for PaymentRecord model.
    Provides comprehensive payment management for admins.
    """
    list_display = [
        'payment_reference',
        'booking_reference',
        'user_email',
        'amount_total',
        'payment_status',
        'payment_method',
        'time_remaining',
        'created_at'
    ]
    list_filter = [
        'payment_status',
        'payment_method',
        'currency',
        'disbursed_to_landlord',
        'created_at'
    ]
    search_fields = [
        'payment_reference',
        'booking__reference_number',
        'user__email',
        'user__first_name',
        'user__last_name',
        'gateway_reference'
    ]
    readonly_fields = [
        'payment_reference',
        'gateway_reference',
        'amount_accommodation',
        'amount_platform_fee',
        'amount_total',
        'payment_window_opens_at',
        'payment_window_closes_at',
        'paid_at',
        'attempt_count',
        'last_attempt_at',
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_reference',
                'booking',
                'user',
                'payment_status',
                'payment_method'
            )
        }),
        ('Amount Breakdown', {
            'fields': (
                'amount_accommodation',
                'amount_platform_fee',
                'amount_total',
                'currency'
            )
        }),
        ('Payment Window', {
            'fields': (
                'payment_window_opens_at',
                'payment_window_closes_at',
                'paid_at'
            )
        }),
        ('Gateway Information', {
            'fields': (
                'gateway_reference',
                'gateway_response'
            )
        }),
        ('Attempt Tracking', {
            'fields': (
                'attempt_count',
                'last_attempt_at',
                'failure_reason'
            )
        }),
        ('Refund Information', {
            'fields': (
                'refund_amount',
                'refund_initiated_at',
                'refund_completed_at',
                'refund_gateway_reference',
                'refund_reason'
            )
        }),
        ('Disbursement Information', {
            'fields': (
                'disbursed_to_landlord',
                'disbursement_amount',
                'disbursed_at',
                'disbursed_by'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )
    actions = ['mark_as_disbursed', 'send_payment_reminder']
    
    def booking_reference(self, obj):
        return obj.booking.reference_number if obj.booking else 'N/A'
    booking_reference.short_description = 'Booking Reference'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def time_remaining(self, obj):
        if obj.payment_status in ['completed', 'refunded', 'partially_refunded']:
            return 'Completed'
        
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        
        remaining = obj.time_remaining_seconds
        if remaining <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        
        if hours > 0:
            return format_html('<span style="color: orange;">{}h {}m</span>', hours, minutes)
        else:
            return format_html('<span style="color: red;">{}m</span>', minutes)
    
    time_remaining.short_description = 'Time Remaining'
    
    def mark_as_disbursed(self, request, queryset):
        """Mark selected payments as disbursed to landlord"""
        count = 0
        for payment in queryset:
            if payment.payment_status == 'completed' and not payment.disbursed_to_landlord:
                payment.disbursed_to_landlord = True
                payment.disbursement_amount = payment.amount_accommodation
                payment.disbursed_at = timezone.now()
                payment.disbursed_by = request.user
                payment.save()
                count += 1
        
        self.message_user(request, f'{count} payment(s) marked as disbursed.')
    
    mark_as_disbursed.short_description = 'Mark selected as disbursed to landlord'
    
    def send_payment_reminder(self, request, queryset):
        """Send payment reminder for selected pending payments"""
        count = 0
        for payment in queryset:
            if payment.payment_status == 'initiated' and not payment.is_expired:
                # Trigger reminder notification
                from .services import PaymentService
                service = PaymentService()
                service._send_notification(
                    user=payment.user,
                    notification_type='payment_reminder',
                    payment=payment
                )
                count += 1
        
        self.message_user(request, f'{count} payment reminder(s) sent.')
    
    send_payment_reminder.short_description = 'Send payment reminder'
