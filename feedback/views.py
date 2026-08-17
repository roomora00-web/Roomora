from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Avg, Count, Q
from properties.models import Property
from bookings.models import Booking
from .models import Review, ReviewImage, ReviewHelpful, Complaint, PropertyReport, UserFeedback
from .serializers import (
    ReviewSerializer, ReviewImageSerializer, ReviewHelpfulSerializer,
    ComplaintSerializer, PropertyReportSerializer, UserFeedbackSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('reviewer', 'accommodation_property', 'booking', 'responded_by').prefetch_related('images').all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'review_type', 'status', 'rating']
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        review = self.get_object()
        helpful_vote, created = ReviewHelpful.objects.get_or_create(
            review=review,
            user=request.user
        )
        if created:
            review.helpful_count += 1
            review.save()
            return Response({'status': 'marked as helpful'})
        return Response({'status': 'already marked'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def respond(self, request, pk=None):
        review = self.get_object()
        if review.accommodation_property.landlord != request.user and request.user.user_type != 'ADMIN':
            return Response({'error': 'You can only respond to reviews for your properties'}, status=status.HTTP_403_FORBIDDEN)
        
        review.response = request.data.get('response', '')
        review.responded_by = request.user
        review.responded_at = timezone.now()
        review.save()
        return Response({'status': 'response added'})


class ReviewImageViewSet(viewsets.ModelViewSet):
    queryset = ReviewImage.objects.select_related('review').all()
    serializer_class = ReviewImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['review']


class ReviewHelpfulViewSet(viewsets.ModelViewSet):
    queryset = ReviewHelpful.objects.select_related('review', 'user').all()
    serializer_class = ReviewHelpfulSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['review', 'user']


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.select_related('reporter', 'accommodation_property', 'booking', 'resolved_by').all()
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reporter', 'accommodation_property', 'category', 'priority', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == 'TENANT':
            queryset = queryset.filter(reporter=user)
        elif user.user_type == 'LANDLORD':
            queryset = queryset.filter(accommodation_property__landlord=user)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def resolve(self, request, pk=None):
        complaint = self.get_object()
        complaint.status = 'RESOLVED'
        complaint.resolution_notes = request.data.get('resolution_notes', '')
        complaint.resolved_by = request.user
        complaint.resolved_at = timezone.now()
        complaint.save()
        return Response({'status': 'resolved'})


class PropertyReportViewSet(viewsets.ModelViewSet):
    queryset = PropertyReport.objects.select_related('reporter', 'accommodation_property', 'reviewed_by').all()
    serializer_class = PropertyReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'report_type', 'status']
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def review(self, request, pk=None):
        report = self.get_object()
        report.status = request.data.get('status', 'ACTION_TAKEN')
        report.admin_notes = request.data.get('admin_notes', '')
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.save()
        return Response({'status': report.status})


class UserFeedbackViewSet(viewsets.ModelViewSet):
    queryset = UserFeedback.objects.select_related('user', 'responded_by').all()
    serializer_class = UserFeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['feedback_type']
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)


# Django Views for Review System

@login_required
def write_review(request, property_id):
    """View for writing a review for a property"""
    property = get_object_or_404(Property, id=property_id, status='APPROVED')
    
    # Check eligibility
    ineligible, ineligible_message = check_review_eligibility(request.user, property)
    if ineligible:
        return render(request, 'feedback/review_form.html', {
            'property': property,
            'ineligible': True,
            'ineligible_message': ineligible_message
        })
    
    # Check if user already reviewed this property
    existing_review = Review.objects.filter(
        reviewer=request.user,
        accommodation_property=property
    ).first()
    
    if request.method == 'POST':
        # Process form submission
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        content = request.POST.get('content')
        cleanliness_rating = request.POST.get('cleanliness_rating')
        location_rating = request.POST.get('location_rating')
        amenities_rating = request.POST.get('amenities_rating')
        communication_rating = request.POST.get('communication_rating')
        value_rating = request.POST.get('value_rating')
        guest_type = request.POST.get('guest_type')
        recommendation = request.POST.get('recommendation')
        would_stay_again = request.POST.get('would_stay_again')
        aspects = request.POST.getlist('aspects')
        concerns = request.POST.getlist('concerns')
        
        # Get the user's booking for this property (any eligible status)
        booking = Booking.objects.filter(
            tenant=request.user,
            accommodation_property=property,
            status__in=[
                'CONFIRMED', 'CONFIRMED_ASSIGNED', 'ACTIVE', 'COMPLETED',
                'PAYMENT_COMPLETE', 'PAYMENT_REQUIRED', 'UNDER_REVIEW',
                'ASSIGNED_AWAITING', 'ADMIN_PENDING', 'REINSTATED'
            ]
        ).order_by('-created_at').first()
        
        # Calculate trust score
        trust_score = calculate_trust_score(request.user, booking, content)
        
        # Create review
        review = Review.objects.create(
            reviewer=request.user,
            accommodation_property=property,
            booking=booking,
            review_type='PROPERTY',
            status='PENDING',  # Requires moderation
            rating=int(rating),
            title=title,
            content=content,
            cleanliness_rating=int(cleanliness_rating) if cleanliness_rating else None,
            location_rating=int(location_rating) if location_rating else None,
            amenities_rating=int(amenities_rating) if amenities_rating else None,
            communication_rating=int(communication_rating) if communication_rating else None,
            value_rating=int(value_rating) if value_rating else None,
            guest_type=guest_type,
            recommendation=recommendation,
            would_stay_again=would_stay_again,
            aspects_highlighted=aspects,
            concerns=concerns,
            is_verified=True if booking else False,
            verification_level='VERIFIED_GUEST' if booking else 'UNVERIFIED',
            trust_score=trust_score
        )
        
        # Handle photo uploads
        photos = request.FILES.getlist('photos')
        for photo in photos[:3]:  # Max 3 photos
            ReviewImage.objects.create(review=review, image=photo)
        
        return redirect(f'/properties/{property.id}/?review_submitted=true')
    
    return render(request, 'feedback/review_form.html', {
        'property': property,
        'existing_review': existing_review,
        'ineligible': False
    })


def check_review_eligibility(user, property):
    """
    Check if user is eligible to review a property.
    Returns (ineligible: bool, message: str)
    """
    if not user.is_authenticated:
        return True, "You must be logged in to write a review."
    
    # Allow review once any confirmed or active booking exists at this property.
    # We do NOT restrict to only COMPLETED stays — users who have paid and are
    # currently staying (or have a confirmed booking) should be able to review.
    eligible_statuses = [
        'CONFIRMED', 'CONFIRMED_ASSIGNED', 'ACTIVE', 'COMPLETED',
        'PAYMENT_COMPLETE', 'PAYMENT_REQUIRED', 'UNDER_REVIEW',
        'ASSIGNED_AWAITING', 'ADMIN_PENDING', 'REINSTATED'
    ]
    has_eligible_booking = Booking.objects.filter(
        tenant=user,
        accommodation_property=property,
        status__in=eligible_statuses
    ).exists()
    
    if not has_eligible_booking:
        return True, "You can only review properties where you have a confirmed booking. Complete your booking payment first."
    
    # Check if user already reviewed this property
    has_reviewed = Review.objects.filter(
        reviewer=user,
        accommodation_property=property
    ).exists()
    
    if has_reviewed:
        return True, "You've already reviewed this property. You can edit your existing review instead."
    
    return False, ""


def calculate_trust_score(user, booking, content):
    """
    Calculate trust score for a review (0-100).
    Higher score = more trustworthy review.
    """
    score = 50  # Base score
    
    # Verified guest bonus
    if booking:
        score += 30
    
    # Account age bonus (account created > 14 days ago)
    if (timezone.now() - user.date_joined).days > 14:
        score += 10
    
    # Content length bonus (detailed reviews)
    if len(content) >= 200:
        score += 5
    elif len(content) >= 100:
        score += 2
    
    # Check for specific details (simple heuristic)
    specific_keywords = ['location', 'clean', 'staff', 'room', 'security', 'wifi', 'kitchen']
    keyword_count = sum(1 for keyword in specific_keywords if keyword.lower() in content.lower())
    score += min(keyword_count * 2, 5)
    
    return min(score, 100)


def get_property_reviews(property_id, status='APPROVED'):
    """
    Get reviews for a property with aggregation data.
    """
    reviews = Review.objects.filter(
        accommodation_property_id=property_id,
        review_type='PROPERTY',
        status=status
    ).select_related('reviewer', 'responded_by').prefetch_related('images')
    
    # Calculate aggregation
    aggregation = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id'),
        avg_cleanliness=Avg('cleanliness_rating'),
        avg_location=Avg('location_rating'),
        avg_amenities=Avg('amenities_rating'),
        avg_communication=Avg('communication_rating'),
        avg_value=Avg('value_rating')
    )
    
    # Rating distribution
    rating_distribution = {}
    for star in range(5, 0, -1):
        count = reviews.filter(rating=star).count()
        percentage = int((count / aggregation['total_reviews'] * 100)) if aggregation['total_reviews'] > 0 else 0
        rating_distribution[star] = {
            'count': count,
            'percentage': percentage
        }
    
    # Extract Themes (What Guests Love & Things to Note)
    themes_count = {}
    concerns_count = {}
    for review in reviews:
        if isinstance(review.aspects_highlighted, list):
            for aspect in review.aspects_highlighted:
                themes_count[aspect] = themes_count.get(aspect, 0) + 1
        if isinstance(review.concerns, list):
            for concern in review.concerns:
                concerns_count[concern] = concerns_count.get(concern, 0) + 1
                
    # Sort by frequency descending
    top_themes = sorted([{'name': k, 'count': v} for k, v in themes_count.items()], key=lambda x: x['count'], reverse=True)[:5]
    top_concerns = sorted([{'name': k, 'count': v} for k, v in concerns_count.items()], key=lambda x: x['count'], reverse=True)[:5]
    
    return {
        'reviews': reviews,
        'aggregation': aggregation,
        'rating_distribution': rating_distribution,
        'top_themes': top_themes,
        'top_concerns': top_concerns
    }
