"""
Queries - Query pattern for booking read operations.
Encapsulates booking queries as query objects.
"""

from dataclasses import dataclass
from typing import List, Optional
from django.db.models import Q, Count, Sum
from bookings.models import Booking, BookingStatusTimeline
from bookings.dto import BookingResponseDTO, PricingSummaryDTO, CompatibilityMatchDTO


@dataclass
class GetBookingDetailsQuery:
    """Query to get booking details."""
    booking_id: int
    tenant_id: Optional[int] = None
    
    def execute(self) -> dict:
        """Execute the query."""
        queryset = Booking.objects.select_related(
            'tenant', 'accommodation_property', 'room_type', 'unit_type', 'assigned_room'
        ).prefetch_related('timeline')
        
        if self.tenant_id:
            queryset = queryset.filter(tenant_id=self.tenant_id)
        
        booking = queryset.get(id=self.booking_id)
        
        # Get related data
        billing_allocation = booking.billing_allocation if hasattr(booking, 'billing_allocation') else None
        room_allocation = booking.room_allocation if hasattr(booking, 'room_allocation') else None
        consent_record = booking.consent_record if hasattr(booking, 'consent_record') else None
        
        return {
            'booking': booking,
            'billing_allocation': billing_allocation,
            'room_allocation': room_allocation,
            'consent_record': consent_record,
            'timeline': booking.timeline.all().order_by('-created_at'),
        }


@dataclass
class GetUserBookingsQuery:
    """Query to get user's bookings."""
    tenant_id: int
    status_filter: Optional[str] = None
    
    def execute(self) -> List[Booking]:
        """Execute the query."""
        queryset = Booking.objects.filter(tenant_id=self.tenant_id).select_related(
            'accommodation_property', 'room_type', 'unit_type', 'assigned_room'
        ).order_by('-created_at')
        
        if self.status_filter:
            queryset = queryset.filter(status=self.status_filter)
        
        return list(queryset)


@dataclass
class GetActiveBookingsQuery:
    """Query to get active bookings for a user."""
    tenant_id: int
    
    def execute(self) -> List[Booking]:
        """Execute the query."""
        active_statuses = [
            'INITIATED', 'UNDER_REVIEW', 'ASSIGNED_AWAITING',
            'CONFIRMED_ASSIGNED', 'ACTIVE', 'WAITLISTED'
        ]
        return list(Booking.objects.filter(
            tenant_id=self.tenant_id,
            status__in=active_statuses
        ).select_related('accommodation_property', 'room_type', 'unit_type'))


@dataclass
class GetBookingTimelineQuery:
    """Query to get booking timeline."""
    booking_id: int
    
    def execute(self) -> List[BookingStatusTimeline]:
        """Execute the query."""
        return list(BookingStatusTimeline.objects.filter(
            booking_id=self.booking_id
        ).select_related('triggered_by').order_by('-created_at'))


@dataclass
class GetPropertyBookingsQuery:
    """Query to get bookings for a property."""
    property_id: int
    status_filter: Optional[str] = None
    
    def execute(self) -> List[Booking]:
        """Execute the query."""
        queryset = Booking.objects.filter(
            accommodation_property_id=self.property_id
        ).select_related('tenant', 'room_type', 'unit_type').order_by('-created_at')
        
        if self.status_filter:
            queryset = queryset.filter(status=self.status_filter)
        
        return list(queryset)


@dataclass
class GetRoomBookingsQuery:
    """Query to get bookings for a specific room."""
    room_id: int
    
    def execute(self) -> List[Booking]:
        """Execute the query."""
        return list(Booking.objects.filter(
            assigned_room_id=self.room_id,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
        ).select_related('tenant'))


@dataclass
class GetBookingStatisticsQuery:
    """Query to get booking statistics."""
    property_id: Optional[int] = None
    tenant_id: Optional[int] = None
    
    def execute(self) -> dict:
        """Execute the query."""
        queryset = Booking.objects.all()
        
        if self.property_id:
            queryset = queryset.filter(accommodation_property_id=self.property_id)
        
        if self.tenant_id:
            queryset = queryset.filter(tenant_id=self.tenant_id)
        
        stats = queryset.aggregate(
            total_bookings=Count('id'),
            active_bookings=Count('id', filter=Q(status__in=['ACTIVE', 'CONFIRMED_ASSIGNED'])),
            pending_bookings=Count('id', filter=Q(status__in=['INITIATED', 'UNDER_REVIEW'])),
            cancelled_bookings=Count('id', filter=Q(status__in=['TEMPORARILY_CANCELLED', 'PERMANENTLY_CANCELLED'])),
            completed_bookings=Count('id', filter=Q(status='COMPLETED')),
            total_revenue=Sum('total_amount', filter=Q(status__in=['ACTIVE', 'COMPLETED']))
        )
        
        return stats


@dataclass
class GetPendingConsentQuery:
    """Query to get bookings pending consent."""
    tenant_id: int
    
    def execute(self) -> List[Booking]:
        """Execute the query."""
        return list(Booking.objects.filter(
            tenant_id=self.tenant_id,
            status__in=['COMPATIBILITY_REVIEW', 'WAITING_CONSENT']
        ).select_related('accommodation_property'))


@dataclass
class GetBookingDraftQuery:
    """Query to get booking draft."""
    user_id: int
    property_id: Optional[int] = None
    
    def execute(self):
        """Execute the query."""
        from bookings.models import BookingDraft
        
        queryset = BookingDraft.objects.filter(user_id=self.user_id, status='IN_PROGRESS')
        
        if self.property_id:
            queryset = queryset.filter(property_id=self.property_id)
        
        return queryset.select_related('property', 'room_type', 'unit_type').first()


@dataclass
class SearchBookingsQuery:
    """Query to search bookings."""
    search_term: str
    property_id: Optional[int] = None
    
    def execute(self) -> List[Booking]:
        """Execute the query."""
        queryset = Booking.objects.filter(
            Q(reference_number__icontains=self.search_term) |
            Q(tenant__email__icontains=self.search_term) |
            Q(tenant__first_name__icontains=self.search_term) |
            Q(tenant__last_name__icontains=self.search_term)
        ).select_related('tenant', 'accommodation_property')
        
        if self.property_id:
            queryset = queryset.filter(accommodation_property_id=self.property_id)
        
        return list(queryset[:50])  # Limit to 50 results
