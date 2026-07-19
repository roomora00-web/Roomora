"""
Domain Events - Event-driven architecture for booking operations.
Defines domain events that occur during booking lifecycle.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_type: str
    occurred_at: datetime
    data: Dict[str, Any]
    
    def to_dict(self):
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'data': self.data,
        }


@dataclass
class BookingCreatedEvent(DomainEvent):
    """Event fired when a booking is created."""
    
    def __init__(self, booking_id: int, tenant_id: int, property_id: int, booking_type: str):
        super().__init__(
            event_type='BOOKING_CREATED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'tenant_id': tenant_id,
                'property_id': property_id,
                'booking_type': booking_type,
            }
        )


@dataclass
class BookingStatusChangedEvent(DomainEvent):
    """Event fired when booking status changes."""
    
    def __init__(self, booking_id: int, previous_status: str, new_status: str, reason: str, triggered_by_id: Optional[int] = None):
        super().__init__(
            event_type='BOOKING_STATUS_CHANGED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'previous_status': previous_status,
                'new_status': new_status,
                'reason': reason,
                'triggered_by_id': triggered_by_id,
            }
        )


@dataclass
class BookingCancelledEvent(DomainEvent):
    """Event fired when a booking is cancelled."""
    
    def __init__(self, booking_id: int, cancellation_type: str, reason: str, triggered_by_id: Optional[int] = None):
        super().__init__(
            event_type='BOOKING_CANCELLED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'cancellation_type': cancellation_type,  # 'TEMPORARY' or 'PERMANENT'
                'reason': reason,
                'triggered_by_id': triggered_by_id,
            }
        )


@dataclass
class BookingReinstatedEvent(DomainEvent):
    """Event fired when a booking is reinstated."""
    
    def __init__(self, booking_id: int, triggered_by_id: Optional[int] = None):
        super().__init__(
            event_type='BOOKING_REINSTATED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'triggered_by_id': triggered_by_id,
            }
        )


@dataclass
class SlotReservedEvent(DomainEvent):
    """Event fired when a slot is reserved."""
    
    def __init__(self, booking_id: int, room_type_id: Optional[int] = None, unit_type_id: Optional[int] = None):
        super().__init__(
            event_type='SLOT_RESERVED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'room_type_id': room_type_id,
                'unit_type_id': unit_type_id,
            }
        )


@dataclass
class SlotReleasedEvent(DomainEvent):
    """Event fired when a slot is released."""
    
    def __init__(self, booking_id: int, reason: str):
        super().__init__(
            event_type='SLOT_RELEASED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'reason': reason,
            }
        )


@dataclass
class RoomAssignedEvent(DomainEvent):
    """Event fired when a room is assigned to a booking."""
    
    def __init__(self, booking_id: int, room_id: int, assigned_by_id: int):
        super().__init__(
            event_type='ROOM_ASSIGNED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'room_id': room_id,
                'assigned_by_id': assigned_by_id,
            }
        )


@dataclass
class ConsentGivenEvent(DomainEvent):
    """Event fired when consent is given."""
    
    def __init__(self, booking_id: int, consent_type: str, user_id: int):
        super().__init__(
            event_type='CONSENT_GIVEN',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'consent_type': consent_type,  # 'user' or 'roommate'
                'user_id': user_id,
            }
        )


@dataclass
class CompatibilityCalculatedEvent(DomainEvent):
    """Event fired when compatibility is calculated."""
    
    def __init__(self, booking_id: int, roommate_id: int, compatibility_score: float, routing_decision: str):
        super().__init__(
            event_type='COMPATIBILITY_CALCULATED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'roommate_id': roommate_id,
                'compatibility_score': compatibility_score,
                'routing_decision': routing_decision,
            }
        )


@dataclass
class BookingActivatedEvent(DomainEvent):
    """Event fired when a booking becomes active."""
    
    def __init__(self, booking_id: int, activated_by_id: Optional[int] = None):
        super().__init__(
            event_type='BOOKING_ACTIVATED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'activated_by_id': activated_by_id,
            }
        )


@dataclass
class BookingCompletedEvent(DomainEvent):
    """Event fired when a booking is completed."""
    
    def __init__(self, booking_id: int):
        super().__init__(
            event_type='BOOKING_COMPLETED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
            }
        )


@dataclass
class PaymentReceivedEvent(DomainEvent):
    """Event fired when a payment is received."""
    
    def __init__(self, booking_id: int, amount: float, payment_type: str):
        super().__init__(
            event_type='PAYMENT_RECEIVED',
            occurred_at=datetime.utcnow(),
            data={
                'booking_id': booking_id,
                'amount': amount,
                'payment_type': payment_type,
            }
        )


class EventDispatcher:
    """Dispatcher for domain events."""
    
    def __init__(self):
        self._handlers = {}
    
    def subscribe(self, event_type: str, handler):
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        """Publish an event to all subscribed handlers."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't fail the event publishing
                print(f"Error in event handler: {e}")


# Global event dispatcher instance
event_dispatcher = EventDispatcher()
