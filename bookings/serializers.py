from rest_framework import serializers
from .models import (
    Booking, Payment, RoommateMatch, BookingRequest, LeaseAgreement, BookingHistory,
    BookingConsent, RoomAssignment, BookingStatusTimeline
)
from .constants import BillingModel, SemesterStructure


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'booking', 'payment_method', 'amount', 'status', 'transaction_id',
                  'payment_date', 'receipt_number', 'notes', 'processed_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoommateMatchSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    tenant_name = serializers.ReadOnlyField(source='booking.tenant.full_name')
    
    class Meta:
        model = RoommateMatch
        fields = ['id', 'booking', 'user', 'user_name', 'tenant_name', 'status', 'compatibility_score',
                  'lifestyle_match', 'schedule_match', 'budget_match', 'user_response',
                  'landlord_response', 'responded_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    tenant_name = serializers.ReadOnlyField(source='tenant.full_name')
    property_title = serializers.ReadOnlyField(source='accommodation_property.title')
    assigned_room_number = serializers.ReadOnlyField(source='room_assignment.assigned_room_number')
    is_active = serializers.ReadOnlyField()
    remaining_balance = serializers.ReadOnlyField()
    payments = PaymentSerializer(many=True, read_only=True)
    roommate_matches = RoommateMatchSerializer(many=True, read_only=True)
    
    # Billing model fields
    billing_model_display = serializers.CharField(source='get_billing_model_display', read_only=True)
    stay_structure_display = serializers.CharField(source='get_stay_structure_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'tenant', 'tenant_name', 'reference_number', 'accommodation_property', 'property_title', 'assigned_room_number',
                  'booking_type', 'status', 'payment_status', 'move_in_date', 'move_out_date',
                  'duration_months', 'monthly_rent', 'security_deposit', 'booking_fee', 'total_amount',
                  'amount_paid', 'preferred_roommates', 'compatibility_score', 'special_requests',
                  'cancellation_reason', 'rejection_reason', 'approved_by', 'approved_at',
                  'is_active', 'remaining_balance', 'payments', 'roommate_matches', 'created_at', 'updated_at',
                  'billing_model', 'billing_model_display', 'semesters_selected', 'months_selected', 'years_selected',
                  'stay_structure', 'stay_structure_display', 'vacation_reserve_start', 'vacation_reserve_end']
        read_only_fields = ['id', 'tenant', 'reference_number', 'is_active', 'remaining_balance', 'created_at', 'updated_at']


class BookingRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    property_title = serializers.ReadOnlyField(source='accommodation_property.title')
    room_number = serializers.ReadOnlyField(source='room.room_number')
    
    class Meta:
        model = BookingRequest
        fields = ['id', 'user', 'user_name', 'accommodation_property', 'property_title', 'room', 'room_number',
                  'status', 'preferred_move_in_date', 'preferred_duration_months', 'message',
                  'response_message', 'responded_by', 'responded_at', 'converted_to_booking',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'responded_at', 'converted_to_booking', 'created_at', 'updated_at']


class LeaseAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseAgreement
        fields = ['id', 'booking', 'status', 'start_date', 'end_date', 'monthly_rent',
                  'security_deposit', 'agreement_document', 'digital_signature', 'tenant_signed',
                  'tenant_signed_at', 'landlord_signed', 'landlord_signed_at', 'special_terms',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookingHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.ReadOnlyField(source='performed_by.full_name')
    
    class Meta:
        model = BookingHistory
        fields = ['id', 'booking', 'action', 'description', 'performed_by', 'performed_by_name',
                  'previous_values', 'new_values', 'created_at']
        read_only_fields = ['id', 'created_at']


class BookingConsentSerializer(serializers.ModelSerializer):
    """Serializer for BookingConsent model (Phase 6)"""
    class Meta:
        model = BookingConsent
        fields = ['id', 'booking', 'user_status', 'user_responded_at', 'roommate_status',
                  'roommate_responded_at', 'created_at', 'expires_at', 'both_accepted', 'is_expired']
        read_only_fields = ['id', 'created_at', 'both_accepted', 'is_expired']


class RoomAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for RoomAssignment model (Phase 6)"""
    roommate_name = serializers.ReadOnlyField(source='assigned_roommate.first_name')
    
    class Meta:
        model = RoomAssignment
        fields = ['id', 'booking', 'assigned_room_number', 'assigned_roommate', 'roommate_name',
                  'assigned_at', 'assigned_by', 'is_active', 'moved_in_date', 'moved_out_date']
        read_only_fields = ['id', 'assigned_at', 'assigned_by']


class BookingStatusTimelineSerializer(serializers.ModelSerializer):
    """Serializer for BookingStatusTimeline model (Phase 6)"""
    triggered_by_name = serializers.ReadOnlyField(source='triggered_by.full_name')
    
    class Meta:
        model = BookingStatusTimeline
        fields = ['id', 'booking', 'previous_status', 'new_status', 'triggered_by', 'triggered_by_name',
                  'triggered_by_type', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']
