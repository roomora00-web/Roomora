"""
Comprehensive tests for Phase 6: Bookings Management System

Tests cover:
- Booking creation and status transitions
- Consent handling (tenant + roommate)
- Room assignment workflow
- Timeline audit trail
- Cancellation flows
- Admin operations
"""

from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
import json

from accounts.models import User, UserProfile, LifestyleProfile
from bookings.models import (
    Booking, BookingConsent, RoomAssignment, BookingStatusTimeline, 
    BookingHistory, RoommateMatch
)
from properties.models import Property as PropertyModel


class BookingModelTests(TestCase):
    """Test Booking model functionality"""
    
    def setUp(self):
        """Create test users and property"""
        self.tenant = User.objects.create_user(
            email='tenant@test.com',
            first_name='John',
            last_name='Doe',
            phone_number='+233123456789',
            user_type='STUDENT',
            password='testpass123'
        )
        self.roommate = User.objects.create_user(
            email='roommate@test.com',
            first_name='Jane',
            last_name='Smith',
            phone_number='+233987654321',
            user_type='STUDENT',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            phone_number='+233111111111',
            user_type='ADMIN',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.property = PropertyModel.objects.create(
            title='Royal Heights Hostel',
            description='A safe and comfortable student hostel close to campus.',
            address='Kumasi, Ghana',
            city='Kumasi',
            country='Ghana',
            property_category='STUDENT_HOUSING',
            property_type='HOSTEL',
            total_area=120.00,
            status='APPROVED',
            is_available=True,
            uploaded_by=self.admin,
        )
    
    def test_booking_creation(self):
        """Test booking can be created with required fields"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            duration_months=4,
            monthly_rent=6000.00,
            total_amount=24000.00,
            booking_type='ROOMMATE_MATCH'
        )
        
        self.assertEqual(booking.tenant, self.tenant)
        # Default booking status is INITIATED (the soft-lock / pending state)
        self.assertEqual(booking.status, 'INITIATED')
        self.assertIsNotNone(booking.reference_number)
        self.assertTrue(booking.reference_number.startswith('SM-'))
    
    def test_booking_status_transition(self):
        """Test set_status method creates timeline entry"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
        )
        
        # Transition to UNDER_REVIEW
        booking.set_status('UNDER_REVIEW', changed_by=self.admin, note='Admin review')
        
        self.assertEqual(booking.status, 'UNDER_REVIEW')
        timeline_entry = BookingStatusTimeline.objects.filter(booking=booking).first()
        self.assertIsNotNone(timeline_entry)
        # Previous status is INITIATED (the model's default)
        self.assertEqual(timeline_entry.previous_status, 'INITIATED')
        self.assertEqual(timeline_entry.new_status, 'UNDER_REVIEW')
        self.assertEqual(timeline_entry.triggered_by, self.admin)
    
    def test_reference_number_uniqueness(self):
        """Test reference numbers are unique"""
        booking1 = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
        )
        
        booking2 = Booking.objects.create(
            tenant=self.roommate,
            accommodation_property=self.property,
            move_in_date='2026-09-15',
            move_out_date='2027-01-15',
            monthly_rent=6000.00,
            total_amount=24000.00,
        )
        
        self.assertNotEqual(booking1.reference_number, booking2.reference_number)


class BookingAPITests(APITestCase):
    """Test Booking API endpoints"""
    
    def setUp(self):
        """Create test users and authenticate"""
        self.tenant = User.objects.create_user(
            email='tenant@test.com',
            first_name='John',
            last_name='Doe',
            phone_number='+233123456789',
            user_type='STUDENT',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            phone_number='+233111111111',
            user_type='ADMIN',
            password='testpass123',
            is_staff=True
        )
        self.property = PropertyModel.objects.create(
            title='Test Property',
            description='A convenient property for student living.',
            address='Kumasi',
            city='Kumasi',
            country='Ghana',
            property_category='STUDENT_HOUSING',
            property_type='HOSTEL',
            total_area=80.00,
            status='APPROVED',
            is_available=True,
            uploaded_by=self.admin,
        )
        
        self.client = APIClient()
    
    def test_create_booking(self):
        """Test creating a booking via API"""
        self.client.force_authenticate(user=self.tenant)
        
        url = reverse('bookings:booking-list')
        data = {
            'accommodation_property': self.property.id,
            'move_in_date': '2026-09-01',
            'move_out_date': '2026-12-31',
            'duration_months': 4,
            'monthly_rent': '6000.00',
            'total_amount': '24000.00',
            'booking_type': 'ROOMMATE_MATCH',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('reference_number', response.data)
        self.assertEqual(response.data['tenant'], self.tenant.id)
        # Default status for a new booking is INITIATED
        self.assertEqual(response.data['status'], 'INITIATED')
    
    def test_list_user_bookings(self):
        """Test listing user's own bookings"""
        # Create bookings
        Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
        )
        
        self.client.force_authenticate(user=self.tenant)
        url = reverse('bookings:booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_accept_consent(self):
        """Test tenant accepting roommate match"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
            status='WAITING_CONSENT',
            user_consent=False,
            roommate_consent=True,
        )
        
        self.client.force_authenticate(user=self.tenant)
        url = reverse('bookings:booking-accept-consent', args=[booking.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.user_consent, True)
        self.assertEqual(booking.status, 'BOTH_ACCEPTED')
    
    def test_cancel_booking(self):
        """Test cancelling a booking"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
            status='SUBMITTED',
        )
        
        self.client.force_authenticate(user=self.tenant)
        url = reverse('bookings:booking-cancel', args=[booking.id])
        data = {'reason': 'Found elsewhere'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(booking.cancellation_reason, 'Found elsewhere')
    
    def test_assign_room_requires_admin(self):
        """Test room assignment requires admin permission"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
            status='BOTH_ACCEPTED',
        )
        
        # Try as tenant - should fail with 403
        self.client.force_authenticate(user=self.tenant)
        url = reverse('bookings:booking-assign-room', args=[booking.id])
        data = {'room_number': 'D-204'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_booking_timeline(self):
        """Test retrieving booking status timeline"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
            status='SUBMITTED',
        )
        
        # Add some transitions
        booking.set_status('UNDER_REVIEW', changed_by=self.admin)
        
        self.client.force_authenticate(user=self.tenant)
        url = reverse('bookings:booking-timeline', args=[booking.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('timeline', response.data)
        self.assertGreater(len(response.data['timeline']), 0)


class RoomAssignmentTests(TestCase):
    """Test room assignment workflow"""
    
    def setUp(self):
        """Create test data"""
        self.tenant = User.objects.create_user(
            email='tenant@test.com',
            first_name='John',
            last_name='Doe',
            phone_number='+233123456789',
            user_type='STUDENT',
            password='testpass123'
        )
        self.roommate = User.objects.create_user(
            email='roommate@test.com',
            first_name='Jane',
            last_name='Smith',
            phone_number='+233987654321',
            user_type='STUDENT',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            phone_number='+233111111111',
            user_type='ADMIN',
            password='testpass123',
            is_staff=True
        )
        self.property = PropertyModel.objects.create(
            title='Test Property',
            description='A convenient property for student living.',
            address='Kumasi',
            city='Kumasi',
            country='Ghana',
            property_category='STUDENT_HOUSING',
            property_type='HOSTEL',
            total_area=80.00,
            status='APPROVED',
            is_available=True,
            uploaded_by=self.admin,
        )
    
    def test_create_room_assignment(self):
        """Test creating room assignment"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
            status='BOTH_ACCEPTED',
        )
        
        from properties.models import Room
        room = Room.objects.create(
            accommodation_property=self.property,
            room_number='D-204',
            total_slots=2,
        )
        assignment = RoomAssignment.objects.create(
            booking=booking,
            assigned_room=room,
            assigned_by=self.admin,
        )
        # Add roommate via M2M (current API after Phase 18 migration)
        assignment.assigned_roommates.add(self.roommate)
        
        self.assertEqual(assignment.booking, booking)
        self.assertEqual(assignment.assigned_room.room_number, 'D-204')
        self.assertEqual(assignment.assigned_by, self.admin)
        self.assertIsNotNone(assignment.assigned_at)


class BookingStatusTransitionTests(TestCase):
    """Test booking status state machine"""
    
    def setUp(self):
        self.tenant = User.objects.create_user(
            email='tenant@test.com',
            phone_number='+233123456789',
            user_type='STUDENT',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            phone_number='+233111111111',
            user_type='ADMIN',
            password='testpass123',
            is_staff=True
        )
        self.property = PropertyModel.objects.create(
            title='Test Property',
            description='A convenient property for student living.',
            address='Kumasi',
            city='Kumasi',
            country='Ghana',
            property_category='STUDENT_HOUSING',
            property_type='HOSTEL',
            total_area=80.00,
            status='APPROVED',
            is_available=True,
            uploaded_by=self.admin,
        )
    
    def test_valid_transition_submitted_to_under_review(self):
        """Test valid transition: SUBMITTED -> UNDER_REVIEW"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
        )
        
        # Default status is INITIATED (booking just created, soft lock placed)
        self.assertEqual(booking.status, 'INITIATED')
        booking.set_status('UNDER_REVIEW', changed_by=self.admin)
        self.assertEqual(booking.status, 'UNDER_REVIEW')
    
    def test_status_transitions_create_timeline(self):
        """Test each status transition creates timeline entry"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            move_in_date='2026-09-01',
            move_out_date='2026-12-31',
            monthly_rent=6000.00,
            total_amount=24000.00,
        )
        
        transitions = [
            'UNDER_REVIEW',
            'COMPATIBILITY_REVIEW',
            'WAITING_CONSENT',
            'BOTH_ACCEPTED',
            'APPROVED_ASSIGNED',
            'ACTIVE',
            'COMPLETED'
        ]
        
        for new_status in transitions:
            booking.set_status(new_status, changed_by=self.admin)
        
        timeline_count = BookingStatusTimeline.objects.filter(booking=booking).count()
        # Should have entries for all transitions
        self.assertGreaterEqual(timeline_count, len(transitions))


class BookingFlowSequenceTests(TestCase):
    """Test the adjusted booking flow sequence redirection logic"""
    
    def setUp(self):
        from properties.models import RoomType
        self.tenant = User.objects.create_user(
            email='tenant@test.com',
            phone_number='+233123456789',
            user_type='STUDENT',
            password='testpass123'
        )
        # Mark email verified as required by BookingPageView.post
        self.tenant.email_verified = True
        self.tenant.save()
        
        self.admin = User.objects.create_user(
            email='admin@test.com',
            phone_number='+233111111111',
            user_type='ADMIN',
            password='testpass123',
            is_staff=True
        )
        self.property = PropertyModel.objects.create(
            title='Test Property',
            description='A convenient property for student living.',
            address='Kumasi',
            city='Kumasi',
            country='Ghana',
            property_category='STUDENT_HOUSING',
            property_type='HOSTEL',
            total_area=80.00,
            status='APPROVED',
            is_available=True,
            uploaded_by=self.admin,
        )
        self.room_type = RoomType.objects.create(
            accommodation_property=self.property,
            room_type_name='Double Room',
            occupancy_type='DOUBLE',
            available_slots=5,
            total_capacity=5,
        )
        # Create pricing model
        from properties.models import RoomTypePricing
        RoomTypePricing.objects.create(
            room_type=self.room_type,
            semester_price=3500.00,
            security_deposit=500.00,
        )
        self.client = Client()
        self.client.login(email='tenant@test.com', password='testpass123')

    def test_booking_initiation_redirects_to_duration_selection(self):
        """Test that BookingPageView redirects to duration selection on post"""
        url = reverse('bookings:booking-page', kwargs={'property_id': self.property.id}) + f'?room_type={self.room_type.id}'
        response = self.client.post(url, {
            'understand_pricing': 'on',
            'complete_profile': 'on',
            'accept_match': 'on',
            'acknowledge_rules': 'on',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        booking = Booking.objects.get(tenant=self.tenant)
        self.assertEqual(booking.status, 'INITIATED')
        expected_url = reverse('bookings:duration-selection', kwargs={'booking_id': booking.id})
        self.assertEqual(data['redirect_url'], expected_url)

    def test_submit_booking_redirects_to_lifestyle_questionnaire_if_matching_needed(self):
        """Test that submit_booking_view redirects to lifestyle questionnaire for shared rooms"""
        booking = Booking.objects.create(
            tenant=self.tenant,
            accommodation_property=self.property,
            room_type=self.room_type,
            move_in_date='2026-09-01',
            monthly_rent=6000.00,
            total_amount=24000.00,
            status='INITIATED',
            booking_type='ROOMMATE_MATCH',
        )
        
        # Populate session for submit_booking_view
        session = self.client.session
        session['booking_billing_model'] = 'SEMESTER_BASED'
        session['booking_num_semesters'] = 1
        session['booking_move_in'] = '2026-09-01'
        session.save()
        
        url = reverse('bookings:submit-booking', kwargs={'booking_id': booking.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('bookings:lifestyle-questionnaire', kwargs={'booking_id': booking.id})
        self.assertRedirects(response, expected_url)
