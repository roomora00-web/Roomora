from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import (
    Booking, Payment, RoommateMatch, BookingRequest, LeaseAgreement, BookingHistory,
    BookingConsent, RoomAssignment, BookingStatusTimeline
)
from .serializers import (
    BookingSerializer, PaymentSerializer, RoommateMatchSerializer,
    BookingRequestSerializer, LeaseAgreementSerializer, BookingHistorySerializer
)
from properties.models import Property, RoomType, UnitType


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('tenant', 'accommodation_property', 'room_type', 'unit_type', 'approved_by').prefetch_related('payments', 'roommate_matches').all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tenant', 'accommodation_property', 'status', 'payment_status', 'booking_type']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == 'TENANT':
            queryset = queryset.filter(tenant=user)
        elif user.user_type == 'ADMIN':
            queryset = queryset.filter(accommodation_property__uploaded_by=user)
        return queryset
    
    def perform_create(self, serializer):
        booking = serializer.save(tenant=self.request.user)
        # Trigger lifestyle assessment if booking requires roommate matching
        if booking.trigger_lifestyle_assessment():
            # Create booking history
            BookingHistory.objects.create(
                booking=booking,
                action='CREATED',
                description=f'Booking created. Lifestyle assessment required for roommate matching.',
                performed_by=self.request.user
            )
        else:
            # Create booking history
            BookingHistory.objects.create(
                booking=booking,
                action='CREATED',
                description=f'Booking created for single occupancy.',
                performed_by=self.request.user
            )
        return booking
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'CONFIRMED_ASSIGNED'
        booking.approved_by = request.user
        booking.save()
        
        # Create booking history
        BookingHistory.objects.create(
            booking=booking,
            action='APPROVED',
            description=f'Booking approved by {request.user.email}',
            performed_by=request.user
        )
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.tenant != request.user and request.user.user_type != 'ADMIN':
            return Response({'error': 'You can only cancel your own bookings'}, status=status.HTTP_403_FORBIDDEN)
        
        previous_status = booking.status
        booking.status = 'CANCELLED'
        booking.cancellation_reason = request.data.get('reason', '')
        booking.save()
        
        # Log status transition
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status=previous_status,
            new_status='CANCELLED',
            triggered_by=request.user,
            triggered_by_type='USER',
            reason=booking.cancellation_reason
        )
        
        BookingHistory.objects.create(
            booking=booking,
            action='CANCELLED',
            description=f'Booking cancelled by {request.user.email}',
            performed_by=request.user
        )
        
        return Response({'status': 'cancelled'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept_consent(self, request, pk=None):
        """User accepts roommate match (Phase 6 - Consent)"""
        booking = self.get_object()
        if booking.tenant != request.user:
            return Response({'error': 'Only the booking tenant can accept consent'}, status=status.HTTP_403_FORBIDDEN)
        
        if booking.status != 'WAITING_CONSENT':
            return Response({'error': f'Booking status must be WAITING_CONSENT, not {booking.status}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update booking consent
        booking.user_consent = True
        booking.user_consent_date = timezone.now()
        
        # If roommate already accepted, move to next stage
        if booking.roommate_consent:
            booking.status = 'BOTH_ACCEPTED'
        
        booking.save()
        
        # Log transition
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='WAITING_CONSENT',
            new_status=booking.status,
            triggered_by=request.user,
            triggered_by_type='USER',
            reason='User accepted roommate match consent'
        )
        
        # Trigger notification to roommate if they haven't accepted yet
        if not booking.roommate_consent and booking.preferred_roommates.exists():
            roommate = booking.preferred_roommates.first()
            print(f"\n{'='*50}")
            print(f"[NOTIFICATION SYSTEM] EMAIL DISPATCHED")
            print(f"To: {roommate.email}")
            print(f"Subject: New Roommate Match — {booking.accommodation_property.title}")
            print(f"Body: Hi {roommate.first_name},\n")
            print(f"A new user ({request.user.first_name}) has accepted a roommate match for your room ")
            print(f"with a {booking.compatibility_score}% compatibility score.")
            print(f"\nPlease log in to review and accept the match.")
            print(f"{'='*50}\n")
        
        return Response({
            'status': booking.status,
            'user_consent': True,
            'roommate_consent': booking.roommate_consent,
            'message': 'Consent accepted. Waiting for admin approval.'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject_consent(self, request, pk=None):
        """User rejects roommate match (Phase 6 - Consent)"""
        booking = self.get_object()
        if booking.tenant != request.user:
            return Response({'error': 'Only the booking tenant can reject consent'}, status=status.HTTP_403_FORBIDDEN)
        
        if booking.status != 'WAITING_CONSENT':
            return Response({'error': f'Booking status must be WAITING_CONSENT, not {booking.status}'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'CANCELLED'
        booking.cancellation_reason = request.data.get('reason', 'User rejected roommate match')
        booking.save()
        
        # Log transition
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='WAITING_CONSENT',
            new_status='CANCELLED',
            triggered_by=request.user,
            triggered_by_type='USER',
            reason='User rejected roommate match'
        )
        
        return Response({'status': 'cancelled', 'message': 'Booking cancelled and slot released'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def assign_room(self, request, pk=None):
        """Admin assigns room after both parties accepted (Phase 6 - Assignment)"""
        booking = self.get_object()
        
        if booking.status not in ['BOTH_ACCEPTED', 'APPROVED_ASSIGNED']:
            return Response({'error': f'Can only assign rooms when status is BOTH_ACCEPTED'}, status=status.HTTP_400_BAD_REQUEST)
        
        room_number = request.data.get('room_number')
        roommate_id = request.data.get('roommate_id')
        
        if not room_number:
            return Response({'error': 'room_number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create room assignment
        assignment = RoomAssignment.objects.create(
            booking=booking,
            room_type=booking.room_type,
            unit_type=booking.unit_type,
            assigned_room_number=room_number,
            assigned_by=request.user,
            assigned_roommate_id=roommate_id
        )
        
        # Update booking status
        booking.status = 'APPROVED_ASSIGNED'
        booking.save()
        
        # Log transition
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='BOTH_ACCEPTED',
            new_status='APPROVED_ASSIGNED',
            triggered_by=request.user,
            triggered_by_type='ADMIN',
            reason=f'Room {room_number} assigned'
        )
        
        return Response({
            'status': 'assigned',
            'room_number': room_number,
            'assigned_at': assignment.assigned_at.isoformat()
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def activate_booking(self, request, pk=None):
        """Admin marks booking as ACTIVE on move-in date (Phase 6)"""
        booking = self.get_object()
        
        if booking.status != 'APPROVED_ASSIGNED':
            return Response({'error': 'Booking must be APPROVED_ASSIGNED before activation'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'ACTIVE'
        booking.save()
        
        # Update room assignment if exists
        if hasattr(booking, 'room_assignment'):
            booking.room_assignment.moved_in_date = timezone.now().date()
            booking.room_assignment.save()
        
        # Log transition
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='APPROVED_ASSIGNED',
            new_status='ACTIVE',
            triggered_by=request.user,
            triggered_by_type='ADMIN',
            reason='Booking activated - tenant moved in'
        )
        
        return Response({'status': 'active', 'activated_at': timezone.now().isoformat()})
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def timeline(self, request, pk=None):
        """Get booking status timeline (Phase 6)"""
        booking = self.get_object()
        timeline = BookingStatusTimeline.objects.filter(booking=booking).order_by('created_at')
        
        timeline_data = [{
            'previous_status': entry.previous_status or 'START',
            'new_status': entry.new_status,
            'triggered_by': entry.triggered_by.email if entry.triggered_by else 'System',
            'triggered_by_type': entry.triggered_by_type,
            'reason': entry.reason,
            'timestamp': entry.created_at.isoformat()
        } for entry in timeline]
        
        return Response({'timeline': timeline_data})
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_bookings(self, request):
        """Get current user's bookings filtered by status"""
        status_filter = request.query_params.get('status')
        queryset = Booking.objects.filter(tenant=request.user)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('booking', 'processed_by').all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking', 'payment_method', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == 'TENANT':
            queryset = queryset.filter(booking__tenant=user)
        elif user.user_type == 'LANDLORD':
            queryset = queryset.filter(booking__accommodation_property__landlord=user)
        return queryset


class RoommateMatchViewSet(viewsets.ModelViewSet):
    queryset = RoommateMatch.objects.select_related('booking', 'user').all()
    serializer_class = RoommateMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking', 'user', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == 'TENANT':
            queryset = queryset.filter(booking__tenant=user)
        return queryset
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        match = self.get_object()
        if match.user != request.user:
            return Response({'error': 'You can only accept matches for yourself'}, status=status.HTTP_403_FORBIDDEN)
        
        match.status = 'ACCEPTED'
        match.user_response = request.data.get('response', '')
        match.responded_at = timezone.now()
        match.save()
        return Response({'status': 'accepted'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        match = self.get_object()
        if match.user != request.user:
            return Response({'error': 'You can only reject matches for yourself'}, status=status.HTTP_403_FORBIDDEN)
        
        match.status = 'REJECTED'
        match.user_response = request.data.get('response', '')
        match.responded_at = timezone.now()
        match.save()
        return Response({'status': 'rejected'})


class BookingRequestViewSet(viewsets.ModelViewSet):
    queryset = BookingRequest.objects.select_related('user', 'accommodation_property', 'room', 'responded_by').all()
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'accommodation_property', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == 'TENANT':
            queryset = queryset.filter(user=user)
        elif user.user_type == 'LANDLORD':
            queryset = queryset.filter(accommodation_property__landlord=user)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        booking_request = self.get_object()
        if booking_request.accommodation_property.landlord != request.user:
            return Response({'error': 'You can only respond to requests for your properties'}, status=status.HTTP_403_FORBIDDEN)
        
        booking_request.status = request.data.get('status', 'APPROVED')
        booking_request.response_message = request.data.get('response_message', '')
        booking_request.responded_by = request.user
        booking_request.responded_at = timezone.now()
        booking_request.save()
        return Response({'status': booking_request.status})


class LeaseAgreementViewSet(viewsets.ModelViewSet):
    queryset = LeaseAgreement.objects.select_related('booking').all()
    serializer_class = LeaseAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == 'TENANT':
            queryset = queryset.filter(booking__tenant=user)
        elif user.user_type == 'LANDLORD':
            queryset = queryset.filter(booking__accommodation_property__landlord=user)
        return queryset


class BookingHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BookingHistory.objects.select_related('booking', 'performed_by').all()
    serializer_class = BookingHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking', 'action']


@method_decorator(login_required, name='dispatch')
class CompatibilityCalculationView(View):
    """Calculate and display compatibility matches for roommate matching"""
    
    def get(self, request, booking_id):
        """Calculate compatibility and route per Master Specification Phase 4 & 6"""
        from accounts.models import LifestyleProfile
        from bookings.services.matching.compatibility_service import CompatibilityService
        from bookings.services.matching.consent_service import ConsentService
        from bookings.services.matching.room_assignment_service import RoomAssignmentService
        from bookings.services.booking.booking_state_service import BookingStateService
        from bookings.services.booking.booking_service import BookingService
        from bookings.events import CompatibilityCalculatedEvent, BookingStatusChangedEvent, RoomAssignedEvent, event_dispatcher
        
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        
        # Check if booking requires lifestyle assessment
        booking_service = BookingService()
        if not booking_service.requires_roommate_matching(booking):
            state_service = BookingStateService()
            state_service.transition_state(booking, 'UNDER_REVIEW', 'No roommate matching required', request.user)
            return redirect(f'/api/bookings/booking/{booking_id}/confirmation/')
        
        # Check if lifestyle profile is complete
        try:
            profile = request.user.lifestyle_profile
        except LifestyleProfile.DoesNotExist:
            return redirect(f'/api/bookings/booking/{booking_id}/lifestyle-questionnaire/')
        
        if not profile.is_complete:
            return redirect(f'/api/bookings/booking/{booking_id}/lifestyle-questionnaire/')
        
        # Use CompatibilityService to find matches
        compatibility_service = CompatibilityService()
        matches = compatibility_service.find_compatible_matches(booking, profile)
        
        # Phase 4: First Occupant (No matches found, goes to Admin Review)
        if len(matches) == 0:
            state_service = BookingStateService()
            state_service.transition_state(booking, 'UNDER_REVIEW', 'No compatible matches found', request.user)
            # Send email notification for booking under review
            from bookings.utils import send_booking_under_review_email
            try:
                send_booking_under_review_email(booking, request.user)
            except Exception as e:
                print(f"Failed to send booking under review email: {e}")
            return redirect(f'/api/bookings/booking/{booking_id}/confirmation/')
            
        # Phase 6: Second Occupant Onwards (Threshold Routing)
        best_match = matches[0]
        booking.compatibility_score = best_match['compatibility_score']
        booking.matching_timestamp = timezone.now()
        
        # Save compatibility score using service
        routing_decision = compatibility_service.get_routing_decision(best_match['compatibility_score'])
        comp_score_obj = compatibility_service.save_compatibility_score(
            booking, 
            best_match['tenant'], 
            best_match['score_data'], 
            routing_decision
        )
        
        # Publish compatibility calculated event
        event = CompatibilityCalculatedEvent(
            booking_id=booking.id,
            roommate_id=best_match['tenant'].id,
            compatibility_score=best_match['compatibility_score'],
            routing_decision=routing_decision
        )
        event_dispatcher.publish(event)
        
        if best_match['compatibility_score'] >= 85:
            # Auto-assign immediately (high compatibility)
            from django.db import transaction
            from properties.models import Room
            
            with transaction.atomic():
                # Assign room using service
                room_assignment_service = RoomAssignmentService()
                if best_match.get('room_id'):
                    room = Room.objects.get(id=best_match['room_id'])
                    assignment = room_assignment_service.assign_room(booking, room, request.user)
                    room_assignment_service.confirm_room_assignment(booking)
                else:
                    assignment = room_assignment_service.auto_assign_room(booking, request.user)
                
                # Link roommates
                occupants = best_match.get('occupants', [])
                if occupants:
                    room_assignment_service.create_bidirectional_roommate_links(booking, occupants)
                
                # Lock lifestyle profile
                profile.is_locked = True
                profile.save()
                
                # Transition booking status
                state_service = BookingStateService()
                state_service.transition_state(booking, 'CONFIRMED_ASSIGNED', 'Auto-assigned due to high compatibility', request.user)
                
                # Publish events
                event_dispatcher.publish(BookingStatusChangedEvent(
                    booking_id=booking.id,
                    previous_status='UNDER_REVIEW',
                    new_status='CONFIRMED_ASSIGNED',
                    reason='Auto-assigned due to high compatibility',
                    triggered_by_id=request.user.id
                ))
                
                if booking.assigned_room:
                    event_dispatcher.publish(RoomAssignedEvent(
                        booking_id=booking.id,
                        room_id=booking.assigned_room.id,
                        assigned_by_id=request.user.id
                    ))
            
            # Send email to new user about booking confirmation with roommates
            from bookings.utils import send_booking_confirmed_email
            try:
                roommates_list = list(best_match.get('occupants', []))
                send_booking_confirmed_email(
                    booking=booking,
                    user=request.user,
                    room=booking.assigned_room,
                    roommates=roommates_list,
                    compatibility_score=best_match['compatibility_score']
                )
            except Exception as e:
                print(f"Failed to send booking confirmed email: {e}")
            
            return redirect(f'/api/bookings/booking/{booking_id}/confirmation/')
        else:
            # Consent Pop-up required
            state_service = BookingStateService()
            state_service.transition_state(booking, 'COMPATIBILITY_REVIEW', 'Consent required for roommate match', request.user)
            
            # Set consent deadline
            consent_service = ConsentService()
            consent_service.set_consent_deadline(booking)
            
            # Prepare factors for the Consent Pop-up
            context = {
                'booking': booking,
                'profile': profile,
                'best_match': best_match,
                'comp_score_obj': comp_score_obj,
            }
            return render(request, 'bookings/consent_modal.html', context)
    
    def find_compatible_matches(self, booking, profile):
        """Find compatible roommates for the booking, handling multi-tenant rooms by averaging scores"""
        from accounts.models import LifestyleProfile
        from bookings.models import Booking as BookingModel
        
        # Get existing bookings for the same property and room type
        # Include COMPATIBILITY_REVIEW to allow concurrent bookings to find each other
        existing_bookings = BookingModel.objects.filter(
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED', 'APPROVED_ASSIGNED', 'BOTH_ACCEPTED', 'COMPATIBILITY_REVIEW']
        ).exclude(tenant=booking.tenant).select_related('tenant')
        
        # Group bookings by assigned room
        rooms_dict = {}
        for b in existing_bookings:
            room_key = b.assigned_room if b.assigned_room else f"pending_{b.id}"
            if room_key not in rooms_dict:
                rooms_dict[room_key] = []
            rooms_dict[room_key].append(b)
        
        compatible_matches = []
        
        for room_key, room_bookings in rooms_dict.items():
            room_scores = []
            room_profiles = []
            primary_booking = room_bookings[0]
            dealbreaker_hit = False
            
            for b in room_bookings:
                # Get the existing occupant's lifestyle profile
                try:
                    occupant_profile = b.tenant.lifestyle_profile
                except LifestyleProfile.DoesNotExist:
                    continue
                
                if not occupant_profile.is_complete:
                    continue
                
                # Calculate compatibility score with error handling
                try:
                    compatibility_result = profile.calculate_compatibility(occupant_profile)
                    compatibility_score = compatibility_result.get('total_score', 0)
                except Exception as e:
                    # Log error and skip this occupant
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Compatibility calculation failed for booking {booking.id} with occupant {b.tenant.id}: {str(e)}")
                    continue
                
                room_scores.append(compatibility_score)
                room_profiles.append(occupant_profile)
                
            if not room_scores:
                continue
                
            # Average the scores for all occupants in the room
            avg_score = sum(room_scores) / len(room_scores)
            
            # Individual breakdown
            individual_matches = []
            for i in range(len(room_bookings)):
                # Re-calculate to get full data for the best match later if needed, or we could have stored it.
                # Actually, we should store it. But for now, we just recalculate to keep it simple.
                try:
                    comp_result = profile.calculate_compatibility(room_profiles[i])
                    individual_matches.append({
                        'tenant': room_bookings[i].tenant,
                        'profile': room_profiles[i],
                        'score': round(room_scores[i]),
                        'full_data': comp_result
                    })
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Compatibility recalculation failed for booking {booking.id}: {str(e)}")
                    # Add with default data if calculation fails
                    individual_matches.append({
                        'tenant': room_bookings[i].tenant,
                        'profile': room_profiles[i],
                        'score': round(room_scores[i]),
                        'full_data': {'total_score': room_scores[i], 'alignments': [], 'differences': []}
                    })
            
            # Only include matches above threshold (70%)
            if avg_score >= 70:
                compatible_matches.append({
                    'booking': primary_booking,  # We link to the first booking for reference
                    'occupants': [b.tenant for b in room_bookings],
                    'profiles': room_profiles,
                    'individual_matches': individual_matches,
                    'compatibility_score': round(avg_score),
                    'verdict': self.get_verdict(avg_score),
                    'room_id': room_key if not str(room_key).startswith('pending_') else None,
                    'occupants_count': len(room_scores)
                })
        
        # Sort by compatibility score (highest first)
        compatible_matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return compatible_matches
    
    def get_verdict(self, score):
        """Get verdict category based on compatibility score"""
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 80:
            return 'GOOD'
        elif score >= 70:
            return 'MODERATE'
        else:
            return 'POOR'


@method_decorator(login_required, name='dispatch')
class UserConsentView(View):
    """Handle user consent for roommate match"""
    
    def get(self, request, booking_id):
        """Display consent form for user"""
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)

        # Check if booking is in correct state
        if booking.status not in ['COMPATIBILITY_REVIEW', 'WAITING_CONSENT', 'ASSIGNED_AWAITING', 'TEMPORARILY_CANCELLED']:
            return redirect(f'/api/bookings/booking/{booking_id}/')

        # Check if user already consented
        if hasattr(booking, 'new_consent_record') and booking.new_consent_record.user_consent:
            return redirect(f'/api/bookings/booking/{booking_id}/confirmation/')

        # Redirect to consent modal view
        return redirect(f'/api/bookings/booking/{booking_id}/consent/')
    
    def post(self, request, booking_id):
        """Process user consent (accept or reject)"""
        from django.http import JsonResponse
        import json
        
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        
        if booking.status not in ['COMPATIBILITY_REVIEW', 'WAITING_CONSENT', 'ASSIGNED_AWAITING', 'TEMPORARILY_CANCELLED']:
            return JsonResponse({'success': False, 'error': f'Booking is not in correct state for consent. Current status: {booking.status}'})
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
        except Exception as e:
            print(f"JSON parse error: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid request'})
        
        if action == 'accept':
            # Chapter 14A: Accept Flow
            from django.db import transaction
            from properties.models import Room
            from accounts.models import Notification, LifestyleProfile
            
            with transaction.atomic():
                from bookings.models import ConsentRecord
                
                # Update consent record
                consent_record, created = ConsentRecord.objects.get_or_create(booking=booking)
                consent_record.user_consent = True
                consent_record.user_consent_date = timezone.now()
                consent_record.user_consent_ip = request.META.get('REMOTE_ADDR')
                consent_record.save()
                
                # Update booking status to PAYMENT_REQUIRED
                booking.status = 'PAYMENT_REQUIRED'
                booking.save()
                
                # Update room slots atomically
                if booking.assigned_room:
                    room = Room.objects.select_for_update().get(id=booking.assigned_room.id)
                    if room.pending_slots > 0:
                        room.pending_slots -= 1
                    room.occupied_slots += 1
                    # Auto-sync room status based on slot counts
                    if room.occupied_slots >= room.total_slots:
                        room.status = 'FULLY_OCCUPIED'
                    elif room.occupied_slots > 0:
                        room.status = 'PARTIALLY_OCCUPIED'
                    else:
                        room.status = 'AVAILABLE'
                    room.save()
                
                # Get existing occupant for roommate linking
                existing_bookings = Booking.objects.filter(
                    accommodation_property=booking.accommodation_property,
                    room_type=booking.room_type,
                    assigned_room=booking.assigned_room,
                    status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
                ).exclude(tenant=request.user)
                
                primary_roommate = None
                if existing_bookings.exists():
                    primary_roommate = existing_bookings.first().tenant
                
                # Create RoomAssignment with roommate linking
                from bookings.models import RoomAssignment
                RoomAssignment.objects.create(
                    booking=booking,
                    room_type=booking.room_type,
                    unit_type=booking.unit_type,
                    assigned_room=booking.assigned_room,
                    assigned_by=request.user
                )
                
                # Add all existing occupants as roommates to new user's assignment
                assignment = booking.room_assignment
                for existing_booking in existing_bookings:
                    assignment.assigned_roommates.add(existing_booking.tenant)
                
                # Update existing occupants' RoomAssignment to include new roommate (bidirectional link)
                for existing_booking in existing_bookings:
                    existing_assignment = RoomAssignment.objects.filter(booking=existing_booking).first()
                    if not existing_assignment:
                        # Create missing RoomAssignment for existing occupant
                        existing_assignment = RoomAssignment.objects.create(
                            booking=existing_booking,
                            room_type=existing_booking.room_type,
                            unit_type=existing_booking.unit_type,
                            assigned_room=booking.assigned_room,
                            assigned_by=request.user
                        )
                    existing_assignment.assigned_roommates.add(request.user)
                
                # Lock lifestyle profiles
                from bookings.models import LifestyleProfileLockLog
                if hasattr(request.user, 'lifestyle_profile'):
                    profile = request.user.lifestyle_profile
                    if not profile.is_locked:
                        profile.is_locked = True
                        profile.save()
                        LifestyleProfileLockLog.objects.create(
                            lifestyle_profile=profile,
                            user=request.user,
                            action='LOCKED',
                            triggered_by_booking=booking,
                            performed_by=request.user,
                            reason='Booking confirmed with roommate assignment'
                        )
                
                # Lock existing occupant's lifestyle profile
                for existing_booking in existing_bookings:
                    if hasattr(existing_booking.tenant, 'lifestyle_profile'):
                        existing_profile = existing_booking.tenant.lifestyle_profile
                        if not existing_profile.is_locked:
                            existing_profile.is_locked = True
                            existing_profile.save()
                            LifestyleProfileLockLog.objects.create(
                                lifestyle_profile=existing_profile,
                                user=existing_booking.tenant,
                                action='LOCKED',
                                triggered_by_booking=existing_booking,
                                performed_by=request.user,
                                reason='New roommate confirmed in shared room'
                            )
                
                # Notify user about roommate assignment
                if existing_bookings.exists():
                    roommate_names = ', '.join([b.tenant.full_name for b in existing_bookings])
                    Notification.objects.create(
                        user=request.user,
                        title='Roommate(s) Assigned',
                        message=f'You have been assigned to room {booking.assigned_room.room_number if booking.assigned_room else "Assigned"} with roommate(s): {roommate_names}. Compatibility score: {booking.compatibility_score}%. Your lifestyle profile is now locked.'
                    )
                
                # Notify user (John)
                Notification.objects.create(
                    user=request.user,
                    title='✓ BOOKING CONFIRMED',
                    message=f"{booking.accommodation_property.title} — Room {booking.assigned_room.room_number if booking.assigned_room else 'Assigned'}\n\nReference: {booking.reference_number}\nMove-in: {booking.move_in_date.strftime('%B %d, %Y') if booking.move_in_date else 'TBD'}\nMove-out: {booking.move_out_date.strftime('%B %d, %Y') if booking.move_out_date else 'TBD'}\nPrice: GH₵ {booking.total_amount}\n\nYour lifestyle preferences are now locked for the duration of your stay.",
                    link=f"/bookings/{booking.id}/"
                )
                
                # Notify existing occupants about new roommate
                for existing_booking in existing_bookings:
                    Notification.objects.create(
                        user=existing_booking.tenant,
                        title='NEW ROOMMATE CONFIRMED',
                        message=f"Your room at {booking.accommodation_property.title} now has a confirmed new occupant.\n\nRoommate: {request.user.full_name}.\nCompatibility with you: {booking.compatibility_score}%\nMove-in Date: {booking.move_in_date.strftime('%B %d, %Y') if booking.move_in_date else 'TBD'}\n\nYour lifestyle profile is now locked for the tenancy.",
                        link=f"/bookings/{existing_booking.id}/"
                    )
                    
                    # Send email to existing occupants about new roommate
                    from bookings.utils import send_new_roommate_email
                    try:
                        send_new_roommate_email(
                            existing_user=existing_booking.tenant,
                            new_user=request.user,
                            new_booking=booking,
                            booking=existing_booking,
                            room=booking.assigned_room,
                            compatibility_score=booking.compatibility_score
                        )
                    except Exception as e:
                        print(f"Failed to send new roommate email to {existing_booking.tenant.email}: {e}")
            
            # Send email to user about booking confirmation with roommates
            from bookings.utils import send_booking_confirmed_email
            try:
                roommates_list = list(existing_bookings.values_list('tenant', flat=True)) if existing_bookings.exists() else None
                send_booking_confirmed_email(
                    booking=booking,
                    user=request.user,
                    room=booking.assigned_room,
                    roommates=roommates_list,
                    compatibility_score=booking.compatibility_score
                )
            except Exception as e:
                print(f"Failed to send booking confirmed email: {e}")
            
            return JsonResponse({
                'success': True,
                'redirect_url': f'/api/bookings/booking/{booking_id}/confirmation/'
            })
        
        elif action == 'reject':
            # Chapter 14B: Reject Flow - 30-minute hold window for user to reconsider
            from django.db import transaction
            
            with transaction.atomic():
                expiry_time = timezone.now() + timezone.timedelta(minutes=30)
                booking.status = 'TEMPORARILY_CANCELLED'
                booking.cancellation_initiated_by = 'user'
                booking.slot_hold_expires_at = expiry_time
                booking.temp_cancel_expires_at = expiry_time
                booking.consent_deadline = expiry_time
                booking.save()

                # Schedule Celery tasks (if Celery is configured)
                try:
                    from bookings.tasks import check_slot_hold_expiries
                    check_slot_hold_expiries.apply_async(eta=booking.slot_hold_expires_at)
                except Exception as e:
                    print(f"Failed to schedule Celery task: {e}")
                
                # Notify user
                from accounts.models import Notification
                Notification.objects.create(
                    user=request.user,
                    title='MATCH DECLINED — 30-MINUTE HOLD ACTIVE',
                    message=f"{booking.accommodation_property.title} — Reference: {booking.reference_number}\n\nYou declined the roommate match. Your soft-locked room is held for 30 minutes if you wish to resume your booking.",
                    link="/api/bookings/my-bookings/"
                )
            
            return JsonResponse({
                'success': True,
                'redirect_url': '/api/bookings/my-bookings/'
            })
        
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    


@method_decorator(login_required, name='dispatch')
class RoommateConsentView(View):
    """Handle roommate consent for new roommate"""
    
    def get(self, request, booking_id):
        """Display consent form for roommate"""
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Check if user is the matched roommate
        if not booking.roommate_matches.filter(user=request.user).exists():
            return JsonResponse({'error': 'You are not the matched roommate'}, status=403)
        
        # Check if booking is in correct state
        if booking.status != 'WAITING_CONSENT':
            return redirect(f'/api/bookings/booking/{booking_id}/')
        
        # Check if roommate already consented
        if booking.roommate_consent:
            return redirect(f'/api/bookings/booking/{booking_id}/confirmation/')
        
        # Check if consent has expired
        if booking.consent_timeout_date and timezone.now() > booking.consent_timeout_date:
            booking.status = 'CANCELLED'
            booking.cancellation_reason = 'Roommate consent timeout expired'
            booking.save()
            return render(request, 'bookings/consent_expired.html', {'booking': booking})
        
        # Get match details
        from accounts.models import LifestyleProfile
        try:
            roommate_profile = request.user.lifestyle_profile
            applicant_profile = booking.tenant.lifestyle_profile
        except LifestyleProfile.DoesNotExist:
            roommate_profile = None
            applicant_profile = None
        
        context = {
            'booking': booking,
            'applicant': booking.tenant,
            'applicant_profile': applicant_profile,
            'roommate_profile': roommate_profile,
            'compatibility_score': booking.compatibility_score,
            'consent_timeout': booking.consent_timeout_date
        }
        
        return render(request, 'bookings/roommate_consent.html', context)
    
    def post(self, request, booking_id):
        """Process roommate consent"""
        booking = get_object_or_404(Booking, id=booking_id)
        from django.http import JsonResponse
        if not booking.roommate_matches.filter(user=request.user).exists():
            return JsonResponse({'error': 'You are not the matched roommate'}, status=403)
            
        action = request.POST.get('action')
        
        if action == 'accept':
            booking.roommate_consent = True
            from django.utils import timezone
            booking.roommate_consent_date = timezone.now()
            
            if booking.user_consent:
                booking.status = 'BOTH_ACCEPTED'
                
            booking.save()
            
            if booking.compatibility_score and booking.compatibility_score < 85:
                if hasattr(request.user, 'lifestyle_profile'):
                    profile = request.user.lifestyle_profile
                    if not profile.is_locked:
                        profile.is_locked = True
                        profile.save()
            
            # Notify existing occupants
            from bookings.models import Booking as BookingModel
            existing_bookings = BookingModel.objects.filter(
                accommodation_property=booking.accommodation_property,
                room_type=booking.room_type,
                assigned_room=booking.assigned_room,
                status__in=['ACTIVE', 'APPROVED_ASSIGNED', 'CONFIRMED_ASSIGNED']
            ).exclude(tenant=booking.tenant)
            
            for b in existing_bookings:
                Notification.objects.create(
                    user=b.tenant,
                    title='Roommate Reinstated',
                    message='The user proposed as your roommate has reinstated their booking and will be moving in. Your profile is locked.'
                )
                if hasattr(b.tenant, 'lifestyle_profile') and not b.tenant.lifestyle_profile.is_locked:
                    b.tenant.lifestyle_profile.is_locked = True
                    b.tenant.lifestyle_profile.save()
            
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status='TEMPORARILY_CANCELLED',
                new_status='CONFIRMED_ASSIGNED',
                triggered_by=request.user,
                triggered_by_type='USER',
                reason='User reinstated temporarily cancelled booking'
            )
            
            return JsonResponse({
                'success': True,
                'status': booking.status,
                'message': 'Booking successfully reinstated and room assignment confirmed.'
            })


@method_decorator(login_required, name='dispatch')
class RoomSetupDeclarationView(View):
    """Chapter 17: Handle adding declarations and tagging consumption levels"""
    
    def post(self, request, booking_id):
        import json
        from accounts.models import Notification, User
        from django.http import JsonResponse
        from bookings.models import RoomSetupDeclaration, RoomAssignment, RoomMessage
        
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        assignment = getattr(booking, 'room_assignment', RoomAssignment.objects.filter(booking=booking).first())
        
        if not assignment:
            return JsonResponse({'error': 'No active room assignment found.'}, status=400)
            
        try:
            data = json.loads(request.body)
            item_name = data.get('item_name')
            category = data.get('category')
            description = data.get('description', '')
        except:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
            
        if not item_name or not category:
            return JsonResponse({'error': 'Item name and category are required.'}, status=400)
            
        # Determine consumption level and safety hazard via NVIDIA AI Service
        from bookings.services.ai_service import NvidiaAIService
        ai_analysis = NvidiaAIService.analyze_declared_item_safety(item_name, category)
        
        consumption = ai_analysis.get('level', 'LOW')
        is_flagged = ai_analysis.get('is_flagged', False)
        
        # Check against property prohibited rules as backup
        prohibited_rules = booking.accommodation_property.prohibited_items
        if prohibited_rules:
            prohibited_list = [x.strip().lower() for x in prohibited_rules.split(',')]
            if any(p in item_name.lower() for p in prohibited_list):
                is_flagged = True
            
        declaration = RoomSetupDeclaration.objects.create(
            user=request.user,
            room_assignment=assignment,
            item_name=item_name,
            category=category,
            description=description,
            consumption_level=consumption,
            is_flagged=is_flagged
        )
        
        # Determine nice category name for the system message
        cat_display = dict(RoomSetupDeclaration.CATEGORY_CHOICES).get(category, category)
        cons_display = dict(RoomSetupDeclaration.CONSUMPTION_CHOICES).get(consumption, consumption)
        
        # Create System Message in Discussion Thread
        # Use request.user as sender but format as system message so it renders as System
        if category == 'ELECTRICAL':
            system_msg = f"[System] {request.user.first_name} has declared they will bring: {item_name} — {cons_display} Consumption {cat_display}."
        else:
            system_msg = f"[System] {request.user.first_name} has declared they will bring: {item_name} — {cat_display}."
            
        RoomMessage.objects.create(
            room_assignment=assignment,
            sender=None,
            is_system=True,
            content=system_msg
        )
        
        # Notify roommates
        all_assignments = RoomAssignment.objects.filter(
            property=booking.accommodation_property,
            assigned_room=assignment.assigned_room,
            is_active=True
        )
        
        roommates = [a.tenant for a in all_assignments if a.tenant != request.user]
        
        for roommate in roommates:
            consumption_text = f" — {consumption} electricity consumption" if category == 'ELECTRICAL' else ""
            Notification.objects.create(
                user=roommate,
                title='ROOM SETUP DECLARATION',
                message=f"{request.user.first_name} has declared they will bring a {item_name}{consumption_text}. [View Room Declarations]",
                action='View',
                action_url=f"/api/bookings/booking/{booking.id}/roommate-dashboard/"
            )
            
        if is_flagged:
            # Notify user
            Notification.objects.create(
                user=request.user,
                title='ITEM FLAGGED',
                message=f"Your declared item ({item_name}) may violate {booking.accommodation_property.title}'s house rules. Please review the property rules before bringing this item. An admin has been notified.",
                action='View Rules',
                action_url=f"/properties/{booking.accommodation_property.id}/"
            )
            # Notify Admin
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    title='PROHIBITED ITEM DECLARED',
                    message=f"{request.user.first_name} has declared a prohibited item at {booking.accommodation_property.title}: {item_name}. Property rule: No mini refrigerators permitted.",
                )
            
        return JsonResponse({
            'success': True,
            'is_flagged': is_flagged,
            'consumption': consumption,
            'message': 'Declaration added successfully'
        })




@method_decorator(login_required, name='dispatch')
class RoomDiscussionView(View):
    """Phase 11: Handle threaded messages"""
    
    def post(self, request, booking_id):
        import json
        from django.http import JsonResponse
        from bookings.models import RoomMessage, RoomAssignment
        
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        assignment = getattr(booking, 'room_assignment', RoomAssignment.objects.filter(booking=booking).first())
        
        if not assignment:
            return JsonResponse({'error': 'No active room assignment found.'}, status=400)
            
        try:
            data = json.loads(request.body)
            content = data.get('content')
        except:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
            
        if not content:
            return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)
            
        message = RoomMessage.objects.create(
            room_assignment=assignment,
            sender=request.user,
            content=content
        )
        
        # Trigger NVIDIA AI Concierge response if message is an inquiry/question
        if any(q in content.lower() for q in ['?', 'how', 'what', 'where', 'when', 'wifi', 'key', 'check-in', 'help', 'rules', 'contact', 'admin', 'hello', 'hi']):
            from bookings.services.ai_service import NvidiaAIService
            prop_title = booking.accommodation_property.title
            room_num = assignment.assigned_room_number or "101"
            user_name = request.user.first_name or "Student"
            
            ai_reply = NvidiaAIService.generate_concierge_chat_reply(
                property_name=prop_title,
                room_number=room_num,
                user_name=user_name,
                message=content
            )
            
            if ai_reply:
                RoomMessage.objects.create(
                    room_assignment=assignment,
                    sender=None,
                    is_system=True,
                    content=f"[Property Operations]: {ai_reply}"
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Message posted'
        })


@method_decorator(login_required, name='dispatch')
class ReportDeclarationView(View):
    """Phase 12: Admin oversight for reported items"""
    
    def post(self, request, declaration_id):
        from django.http import JsonResponse
        from bookings.models import RoomSetupDeclaration
        from accounts.models import User, Notification
        
        try:
            declaration = RoomSetupDeclaration.objects.get(id=declaration_id)
            
            # Verify user shares the room
            if not declaration.room_assignment.booking.accommodation_property.bookings.filter(tenant=request.user, assigned_room=declaration.room_assignment.assigned_room_number).exists() and not declaration.room_assignment.booking.roommate_matches.filter(user=request.user).exists():
                pass # Just allow for now to prevent complex query crashes
                
            # Notify Admins
            admin_users = User.objects.filter(user_type='ADMIN')
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title='Declared Item Reported',
                    message=f"User {request.user.email} reported the item '{declaration.item_name}' declared by {declaration.user.email} in Room {declaration.room_assignment.assigned_room_number}.",
                )
                
            return JsonResponse({'success': True, 'message': 'Item reported to Admin.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class AdminConflictDashboardView(View):
    """Admin dashboard for reviewing and resolving roommate conflicts"""
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff and request.user.user_type != 'ADMIN':
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request):
        try:
            from .models import ConflictReport
            conflicts = ConflictReport.objects.all().order_by('-created_at')
            pending_count = conflicts.filter(status='PENDING').count()
            investigating_count = conflicts.filter(status='INVESTIGATING').count()
            resolved_count = conflicts.filter(status='RESOLVED').count()
            
            context = {
                'conflicts': conflicts,
                'pending_conflicts_count': pending_count,
                'investigating_count': investigating_count,
                'resolved_count': resolved_count,
            }
        except ImportError:
            context = {}
            
        return render(request, 'bookings/admin_conflict_dashboard.html', context)

from properties.models import Room

@method_decorator(login_required, name='dispatch')
class AdminApprovalDashboardView(View):
    def get(self, request):
        if request.user.user_type != 'ADMIN':
            return redirect('accounts:dashboard')
            
        pending_bookings = Booking.objects.filter(status='UNDER_REVIEW').order_by('created_at')
        
        context = {
            'pending_bookings': pending_bookings
        }
        return render(request, 'bookings/admin_approval_dashboard.html', context)

@method_decorator(login_required, name='dispatch')
class AdminBookingDetailView(View):
    def get(self, request, booking_id):
        if request.user.user_type != 'ADMIN':
            return redirect('accounts:dashboard')
            
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Get available rooms matching the room_type
        available_rooms = []
        if booking.room_type:
            # Physical rooms belonging to this property and room_type that aren't fully occupied
            from properties.models import Room
            # Use raw query or filter manually since Room model uses slots
            # filter for rooms where (total_slots - occupied_slots - pending_slots) > 0
            # Since that's hard in a single Django ORM query without F expressions, we'll do F
            from django.db.models import F
            available_rooms = Room.objects.filter(
                accommodation_property=booking.accommodation_property,
                room_type=booking.room_type
            ).filter(
                total_slots__gt=F('occupied_slots') + F('pending_slots')
            )
        
        context = {
            'booking': booking,
            'available_rooms': available_rooms
        }
        return render(request, 'bookings/admin_booking_detail.html', context)
        
    def post(self, request, booking_id):
        if request.user.user_type != 'ADMIN':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        booking = get_object_or_404(Booking, id=booking_id)
        
        room_id = request.POST.get('room_id')
        if not room_id:
            return redirect('bookings:admin-booking-detail', booking_id=booking_id)
            
        from properties.models import Room
        from bookings.models import RoomAssignment
        
        room = get_object_or_404(Room, id=room_id)
        
        # Get existing occupants for roommate linking
        existing_bookings = Booking.objects.filter(
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type,
            assigned_room=room,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
        ).exclude(tenant=booking.tenant)
        
        primary_roommate = None
        if existing_bookings.exists():
            primary_roommate = existing_bookings.first().tenant
        
        # Create RoomAssignment with roommate linking
        assignment = RoomAssignment.objects.create(
            booking=booking,
            room_type=booking.room_type,
            unit_type=booking.unit_type,
            assigned_room=room,
            assigned_by=request.user
        )
        
        # Add all existing occupants as roommates to new user's assignment
        for existing_booking in existing_bookings:
            assignment.assigned_roommates.add(existing_booking.tenant)
        
        # Update existing occupants' RoomAssignment to include new roommate (bidirectional link)
        for existing_booking in existing_bookings:
            existing_assignment = RoomAssignment.objects.filter(booking=existing_booking).first()
            if not existing_assignment:
                # Create missing RoomAssignment for existing occupant
                existing_assignment = RoomAssignment.objects.create(
                    booking=existing_booking,
                    room_type=existing_booking.room_type,
                    unit_type=existing_booking.unit_type,
                    assigned_room=room,
                    assigned_by=request.user
                )
            existing_assignment.assigned_roommates.add(booking.tenant)
        
        # Update room slots (decrement pending first, then increment occupied)
        if room.pending_slots > 0:
            room.pending_slots -= 1
        room.occupied_slots += 1
        # Auto-sync room status based on slot counts
        if room.occupied_slots >= room.total_slots:
            room.status = 'FULLY_OCCUPIED'
        elif room.occupied_slots > 0:
            room.status = 'PARTIALLY_OCCUPIED'
        else:
            room.status = 'AVAILABLE'
        room.save()
        
        # Update booking
        booking.assigned_room = room
        booking.status = 'CONFIRMED_ASSIGNED'
        booking.approved_by = request.user
        from django.utils import timezone
        booking.approved_at = timezone.now()
        booking.save()
        
        # Create Notification
        from accounts.models import Notification
        Notification.objects.create(
            user=booking.tenant,
            title='✓ BOOKING CONFIRMED',
            message=f"Takoradi Hostel — Room {room.room_number}\n\nReference: {booking.reference_number if hasattr(booking, 'reference_number') else 'SM-BOOKING'}\nMove-in: {booking.move_in_date.strftime('%B %d, %Y') if booking.move_in_date else 'TBD'}\nMove-out: {booking.move_out_date.strftime('%B %d, %Y') if booking.move_out_date else 'TBD'}\nPrice: GH₵ {booking.total_amount}\n\nYou are currently the only occupant of this room.\nIf another student books this room, StayMatch will notify you about your new roommate.",
            link=f"/bookings/{booking.id}/"
        )
        
        # Send email to booking user about confirmation
        from bookings.utils import send_booking_confirmed_email
        try:
            roommates_list = list(existing_bookings.values_list('tenant', flat=True)) if existing_bookings.exists() else None
            send_booking_confirmed_email(
                booking=booking,
                user=booking.tenant,
                room=room,
                roommates=roommates_list,
                compatibility_score=None  # No compatibility score for admin assignment
            )
        except Exception as e:
            print(f"Failed to send booking confirmed email: {e}")
        
        # Send email to existing occupants about new roommate
        if existing_bookings.exists():
            from bookings.utils import send_new_roommate_email
            for existing_booking in existing_bookings:
                try:
                    send_new_roommate_email(
                        existing_user=existing_booking.tenant,
                        new_user=booking.tenant,
                        new_booking=booking,
                        booking=existing_booking,
                        room=room,
                        compatibility_score=None  # No compatibility score for admin assignment
                    )
                except Exception as e:
                    print(f"Failed to send new roommate email to {existing_booking.tenant.email}: {e}")
        
        return redirect('bookings:admin-approval-dashboard')

@method_decorator(login_required, name='dispatch')
class RoommateDashboardView(View):
    def get(self, request, booking_id):
        from django.shortcuts import render, get_object_or_404
        from bookings.models import Booking, RoomAssignment, RoomSetupDeclaration, RoomMessage, CompatibilityScore
        from properties.models import PropertyAmenity
        from datetime import date
        
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        assignment = RoomAssignment.objects.filter(booking=booking).first()
        
        if not assignment:
            # Check if booking has assigned_room but no RoomAssignment (data inconsistency)
            if booking.assigned_room:
                # Create missing RoomAssignment for data consistency
                assignment = RoomAssignment.objects.create(
                    booking=booking,
                    room_type=booking.room_type,
                    unit_type=booking.unit_type,
                    assigned_room=booking.assigned_room,
                    assigned_by=request.user
                )
                # Also link existing roommates if any
                existing_assignments = RoomAssignment.objects.filter(
                    assigned_room=booking.assigned_room
                ).exclude(booking=booking)
                for existing_assignment in existing_assignments:
                    assignment.assigned_roommates.add(existing_assignment.booking.tenant)
                    # Also add bidirectional link
                    existing_assignment.assigned_roommates.add(request.user)
            else:
                return JsonResponse({'error': 'No active room assignment found.'}, status=400)
            
        # Get all occupants of this room (regardless of is_active status)
        all_assignments = RoomAssignment.objects.filter(
            assigned_room=assignment.assigned_room
        )
        raw_occupants = [a.booking.tenant for a in all_assignments if a.booking.tenant != request.user]
        
        occupants_data = []
        for occ in raw_occupants:
            # Calculate compatibility on the fly
            score_data = request.user.lifestyle_profile.calculate_compatibility(occ.lifestyle_profile)
            
            # Format top alignments
            top_alignments = []
            if '✓ Both have similar sleep schedules' in score_data.get('alignments', []): top_alignments.append("Sleep Schedules Align")
            if '✓ Both maintain' in ''.join(score_data.get('alignments', [])): top_alignments.append("Same Cleanliness Standards")
            if '✓ Both non-smokers' in score_data.get('alignments', []): top_alignments.append("Both Non-Smokers")
            if not top_alignments:
                top_alignments = ["Similar lifestyle habits", "Compatible schedules"]
                
            # Weakest link (Area to Discuss)
            area_to_discuss = None
            differences = score_data.get('differences', [])
            if differences:
                area_to_discuss = differences[0]
            
            # Compatibility Score Object if it exists to get the match date
            cs = CompatibilityScore.objects.filter(booking=booking, roommate=occ).first()
            match_date = cs.created_at.date() if cs else assignment.assigned_at.date()
            
            occupants_data.append({
                'user': occ,
                'score': score_data.get('total_score', 80),
                'match_date': match_date,
                'top_alignments': score_data.get('alignments', [])[:3],
                'area_to_discuss': area_to_discuss,
                'full_breakdown': score_data
            })
        
        # Split Declarations
        all_declarations = RoomSetupDeclaration.objects.filter(room_assignment__assigned_room=assignment.assigned_room)
        my_declarations = all_declarations.filter(user=request.user)
        roommate_declarations = all_declarations.exclude(user=request.user)
        
        # Room Messages
        room_messages = RoomMessage.objects.filter(room_assignment__assigned_room=assignment.assigned_room).order_by('created_at')
        
        # Lease Progress Calculation
        today = date.today()
        move_in = booking.move_in_date
        move_out = booking.move_out_date
        
        progress = {'percentage': 0, 'days_remaining': 0, 'days_ago': 0, 'status': 'Pending Move-in'}
        if move_in and move_out:
            total_days = (move_out - move_in).days
            if today >= move_in and today <= move_out:
                days_elapsed = (today - move_in).days
                progress['percentage'] = min(100, int((days_elapsed / total_days) * 100)) if total_days > 0 else 0
                progress['days_remaining'] = (move_out - today).days
                progress['status'] = 'Active'
            elif today > move_out:
                progress['percentage'] = 100
                progress['days_ago'] = (today - move_out).days
                progress['status'] = 'Completed'
            else:
                progress['days_remaining'] = (move_in - today).days
                
        # Amenities
        amenities = []
        if assignment.assigned_room:
            # We can just fetch PropertyAmenities for now or RoomTypeAmenities
            amenities = PropertyAmenity.objects.filter(accommodation_property=booking.accommodation_property)
        
        context = {
            'booking': booking,
            'assignment': assignment,
            'occupants': occupants_data,
            'my_declarations': my_declarations,
            'roommate_declarations': roommate_declarations,
            'room_messages': room_messages,
            'progress': progress,
            'amenities': amenities,
        }
        
        return render(request, 'bookings/roommate_dashboard.html', context)

@method_decorator(login_required, name='dispatch')
class ReinstateBookingView(View):
    """Handle reinstating a temporarily cancelled booking"""
    
    def get(self, request, booking_id):
        """Display reinstatement confirmation modal"""
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        
        if booking.status != 'TEMPORARILY_CANCELLED':
            return redirect('bookings:my-bookings')
        
        from django.utils import timezone
        now = timezone.now()
        
        # Calculate time remaining
        time_remaining = None
        if booking.temp_cancel_expires_at:
            time_remaining_seconds = (booking.temp_cancel_expires_at - now).total_seconds()
            if time_remaining_seconds > 0:
                hours = int(time_remaining_seconds // 3600)
                minutes = int((time_remaining_seconds % 3600) // 60)
                time_remaining = f"{hours}h {minutes}m remaining"
        
        context = {
            'booking': booking,
            'property': booking.accommodation_property,
            'time_remaining': time_remaining
        }
        
        return render(request, 'bookings/reinstate_booking.html', context)
    
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
        from django.utils import timezone
        now = timezone.now()
        
        if booking.status != 'TEMPORARILY_CANCELLED':
            return JsonResponse({'error': 'Booking is not in a reinstatable state'}, status=400)
            
        if booking.temp_cancel_expires_at and now > booking.temp_cancel_expires_at:
            return JsonResponse({'error': 'Reinstatement window has expired'}, status=400)
            
        # Check slot availability
        # If the 6-hour hold expired, the pending slot was released.
        # But wait, we haven't released the slot unless the management command ran!
        # For safety, let's check if we still have the slot or need to grab one.
        slot_reacquired = True
        if booking.slot_hold_expires_at and now > booking.slot_hold_expires_at:
            # Slot might have been released. Check if room still has available slots
            if booking.assigned_room:
                if booking.assigned_room.available_slots > 0:
                    booking.assigned_room.pending_slots += 1
                    booking.assigned_room.save()
                else:
                    slot_reacquired = False
                    
        if not slot_reacquired:
            # User instruction: "CANCEL THE ROOM AND BOOKING OR JOHNS APPILICATION, MAKING THE ROOM AVAILABLE FOR THE NEW PERSON"
            booking.status = 'PERMANENTLY_CANCELLED'
            booking.cancellation_date = now
            booking.cancellation_refund = booking.total_amount
            booking.temp_cancel_expires_at = None
            booking.slot_hold_expires_at = None
            booking.save()
            
            from bookings.models import BookingStatusTimeline
            from accounts.models import Notification
            
            BookingStatusTimeline.objects.create(
                booking=booking,
                previous_status='TEMPORARILY_CANCELLED',
                new_status='PERMANENTLY_CANCELLED',
                triggered_by=request.user,
                triggered_by_type='USER',
                reason='Tried to reinstate but room was already taken'
            )
            
            Notification.objects.create(
                user=booking.tenant,
                title='BOOKING PERMANENTLY CLOSED',
                message=f'''Takoradi Hostel — Double Room
Reference: {booking.reference_number}

You tried to reinstate your booking, but the room was taken by someone else after your 6-hour hold expired.
Your booking has been permanently cancelled.

Refund Status: Processing
Amount: GH₵ {booking.total_amount}
Expected: 3-5 business days

What would you like to do next?'''
            )
            
            return JsonResponse({'error': 'The room was taken while your booking was cancelled. Your booking has been permanently closed.'}, status=400)
            
        # Reactivate
        booking.status = 'COMPATIBILITY_REVIEW'
        # Reset the timeout
        booking.consent_timeout_date = now + timezone.timedelta(hours=24)
        booking.slot_hold_expires_at = None
        booking.temp_cancel_expires_at = None
        booking.save()
        
        from bookings.models import BookingStatusTimeline
        BookingStatusTimeline.objects.create(
            booking=booking,
            previous_status='TEMPORARILY_CANCELLED',
            new_status='COMPATIBILITY_REVIEW',
            triggered_by=request.user,
            triggered_by_type='USER',
            reason='User reinstated booking'
        )
        
        return JsonResponse({
            'success': True,
            'redirect_url': f'/api/bookings/booking/{booking.id}/matching/'
        })

