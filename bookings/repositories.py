"""
BookingRepository - Data access layer for bookings.
Abstracts database operations for bookings.
"""

from django.db.models import Q
from bookings.models import Booking, BookingDraft, BillingAllocation, RoomAllocation, ConsentRecord


class BookingRepository:
    """Repository for booking data access."""
    
    def find_by_id(self, booking_id):
        """Find booking by ID."""
        try:
            return Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return None
    
    def find_by_reference(self, reference_number):
        """Find booking by reference number."""
        try:
            return Booking.objects.get(reference_number=reference_number)
        except Booking.DoesNotExist:
            return None
    
    def find_by_tenant(self, tenant_id):
        """Find all bookings for a tenant."""
        return Booking.objects.filter(tenant_id=tenant_id).select_related(
            'accommodation_property', 'room_type', 'unit_type', 'assigned_room'
        ).prefetch_related('timeline')
    
    def find_active_bookings(self, tenant_id):
        """Find active bookings for a tenant."""
        active_statuses = [
            'INITIATED', 'UNDER_REVIEW', 'ASSIGNED_AWAITING',
            'CONFIRMED_ASSIGNED', 'ACTIVE', 'WAITLISTED'
        ]
        return Booking.objects.filter(
            tenant_id=tenant_id,
            status__in=active_statuses
        ).select_related('accommodation_property', 'room_type', 'unit_type')
    
    def find_pending_consent(self, tenant_id):
        """Find bookings pending consent."""
        return Booking.objects.filter(
            tenant_id=tenant_id,
            status__in=['COMPATIBILITY_REVIEW', 'WAITING_CONSENT']
        ).select_related('accommodation_property')
    
    def find_by_property(self, property_id):
        """Find all bookings for a property."""
        return Booking.objects.filter(accommodation_property_id=property_id).select_related('tenant')
    
    def find_by_room(self, room_id):
        """Find all bookings for a specific room."""
        return Booking.objects.filter(assigned_room_id=room_id).select_related('tenant')
    
    def find_by_status(self, status):
        """Find all bookings with a specific status."""
        return Booking.objects.filter(status=status).select_related('tenant', 'accommodation_property')
    
    def save(self, booking):
        """Save a booking."""
        booking.save()
        return booking
    
    def delete(self, booking_id):
        """Delete a booking."""
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.delete()
            return True
        except Booking.DoesNotExist:
            return False
    
    def count_by_tenant(self, tenant_id):
        """Count bookings for a tenant."""
        return Booking.objects.filter(tenant_id=tenant_id).count()
    
    def count_by_status(self, status):
        """Count bookings by status."""
        return Booking.objects.filter(status=status).count()
    
    def get_billing_allocation(self, booking_id):
        """Get billing allocation for a booking."""
        try:
            return BillingAllocation.objects.get(booking_id=booking_id)
        except BillingAllocation.DoesNotExist:
            return None
    
    def get_room_allocation(self, booking_id):
        """Get room allocation for a booking."""
        try:
            return RoomAllocation.objects.get(booking_id=booking_id)
        except RoomAllocation.DoesNotExist:
            return None
    
    def get_consent_record(self, booking_id):
        """Get consent record for a booking."""
        try:
            return ConsentRecord.objects.get(booking_id=booking_id)
        except ConsentRecord.DoesNotExist:
            return None


class BookingDraftRepository:
    """Repository for booking draft data access."""
    
    def find_by_user(self, user_id):
        """Find all drafts for a user."""
        return BookingDraft.objects.filter(user_id=user_id).select_related('property')
    
    def find_active_draft(self, user_id, property_id):
        """Find active draft for user and property."""
        return BookingDraft.objects.filter(
            user_id=user_id,
            property_id=property_id,
            status='IN_PROGRESS'
        ).first()
    
    def find_by_id(self, draft_id):
        """Find draft by ID."""
        try:
            return BookingDraft.objects.get(id=draft_id)
        except BookingDraft.DoesNotExist:
            return None
    
    def save(self, draft):
        """Save a draft."""
        draft.save()
        return draft
    
    def delete(self, draft_id):
        """Delete a draft."""
        try:
            draft = BookingDraft.objects.get(id=draft_id)
            draft.delete()
            return True
        except BookingDraft.DoesNotExist:
            return False
    
    def mark_expired(self):
        """Mark all expired drafts as abandoned."""
        from django.utils import timezone
        BookingDraft.objects.filter(
            expires_at__lt=timezone.now(),
            status='IN_PROGRESS'
        ).update(status='ABANDONED')
    
    def cleanup_old_drafts(self, days=7):
        """Delete old abandoned drafts."""
        from django.utils import timezone
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        BookingDraft.objects.filter(
            updated_at__lt=cutoff_date,
            status__in=['ABANDONED', 'CONVERTED']
        ).delete()
