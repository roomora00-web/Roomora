from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    REVIEW_TYPE_CHOICES = [
        ('PROPERTY', 'Property Review'),
        ('LANDLORD', 'Landlord Review'),
        ('ROOMMATE', 'Roommate Review'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged'),
    ]
    
    GUEST_TYPE_CHOICES = [
        ('STUDENT', 'Student'),
        ('WORKER', 'Worker'),
        ('FAMILY', 'Family'),
        ('OTHER', 'Other'),
    ]
    
    RECOMMENDATION_CHOICES = [
        ('DEFINITELY', 'Yes, definitely'),
        ('MAYBE', 'Maybe'),
        ('NO', 'No, not recommended'),
    ]
    
    WOULD_STAY_AGAIN_CHOICES = [
        ('ALREADY_BOOKED', 'Already booked next semester'),
        ('DEFINITELY', 'Definitely'),
        ('MAYBE', 'Maybe'),
        ('NO', 'No, looking elsewhere'),
    ]
    
    VERIFICATION_LEVEL_CHOICES = [
        ('VERIFIED_GUEST', 'Verified Guest'),
        ('VERIFIED_THIRD_PARTY', 'Verified via Third Party'),
        ('UNVERIFIED', 'Unverified'),
    ]
    
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_reviews')
    accommodation_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES, default='PROPERTY')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Rating (1-5)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    
    # Detailed ratings
    cleanliness_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    location_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    amenities_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    communication_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Content
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Additional review fields from specification
    guest_type = models.CharField(max_length=20, choices=GUEST_TYPE_CHOICES, null=True, blank=True)
    stay_start_date = models.DateField(null=True, blank=True)
    stay_end_date = models.DateField(null=True, blank=True)
    
    # Aspects highlighted (JSON array of strings)
    aspects_highlighted = models.JSONField(default=list, blank=True)
    # Concerns (JSON array of strings)
    concerns = models.JSONField(default=list, blank=True)
    
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, null=True, blank=True)
    would_stay_again = models.CharField(max_length=30, choices=WOULD_STAY_AGAIN_CHOICES, null=True, blank=True)
    
    # Response
    response = models.TextField(blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_reviews')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Moderation
    is_verified = models.BooleanField(default=False)  # Verified purchase/stay
    verification_level = models.CharField(max_length=30, choices=VERIFICATION_LEVEL_CHOICES, default='UNVERIFIED')
    is_featured = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)
    trust_score = models.PositiveIntegerField(default=0)  # 0-100
    
    # Metadata
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)
    report_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['reviewer', 'booking']  # One review per booking
    
    def __str__(self):
        return f"Review by {self.reviewer.email} - {self.rating}/5"
    
    @property
    def average_rating(self):
        ratings = [self.rating]
        if self.cleanliness_rating:
            ratings.append(self.cleanliness_rating)
        if self.location_rating:
            ratings.append(self.location_rating)
        if self.amenities_rating:
            ratings.append(self.amenities_rating)
        if self.communication_rating:
            ratings.append(self.communication_rating)
        if self.value_rating:
            ratings.append(self.value_rating)
        return sum(ratings) / len(ratings)


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_images'
        verbose_name = 'Review Image'
        verbose_name_plural = 'Review Images'
    
    def __str__(self):
        return f"Image for review {self.review.id}"


class ReviewHelpful(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpful'
        verbose_name = 'Review Helpful Vote'
        verbose_name_plural = 'Review Helpful Votes'
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.email} found review {self.review.id} helpful"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('PROPERTY', 'Property Issue'),
        ('LANDLORD', 'Landlord Issue'),
        ('ROOMMATE', 'Roommate Issue'),
        ('PAYMENT', 'Payment Issue'),
        ('SAFETY', 'Safety Concern'),
        ('FRAUD', 'Fraud Report'),
        ('OTHER', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    accommodation_property = models.ForeignKey('properties.Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Details
    subject = models.CharField(max_length=200)
    description = models.TextField()
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_complaints')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Attachments
    attachment = models.FileField(upload_to='complaint_attachments/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'complaints'
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Complaint: {self.subject} - {self.status}"


class PropertyReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('FAKE_LISTING', 'Fake Listing'),
        ('INACCURATE_INFO', 'Inaccurate Information'),
        ('SCAM', 'Scam'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWING', 'Reviewing'),
        ('ACTION_TAKEN', 'Action Taken'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_reports')
    accommodation_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='reports')
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    description = models.TextField()
    evidence = models.TextField(blank=True)  # Links, screenshots, etc.
    
    # Admin response
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_reports'
        verbose_name = 'Property Report'
        verbose_name_plural = 'Property Reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report on {self.accommodation_property.title} - {self.report_type}"


class UserFeedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('GENERAL', 'General Feedback'),
        ('BUG_REPORT', 'Bug Report'),
        ('FEATURE_REQUEST', 'Feature Request'),
        ('COMPLIMENT', 'Compliment'),
        ('COMPLAINT', 'Complaint'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='GENERAL')
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # System info (optional)
    page_url = models.URLField(blank=True)
    browser_info = models.CharField(max_length=200, blank=True)
    
    # Response
    response = models.TextField(blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_feedback')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_feedback'
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback: {self.subject}"
