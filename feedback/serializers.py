from rest_framework import serializers
from .models import Review, ReviewImage, ReviewHelpful, Complaint, PropertyReport, UserFeedback


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.ReadOnlyField(source='reviewer.full_name')
    property_title = serializers.ReadOnlyField(source='accommodation_property.title')
    average_rating = serializers.ReadOnlyField()
    images = ReviewImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'reviewer_name', 'accommodation_property', 'property_title', 'booking', 'review_type',
                  'status', 'rating', 'cleanliness_rating', 'location_rating', 'amenities_rating',
                  'communication_rating', 'value_rating', 'title', 'content', 'response', 'responded_by',
                  'responded_at', 'is_verified', 'is_featured', 'flag_reason', 'helpful_count',
                  'average_rating', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'helpful_count', 'average_rating', 'created_at', 'updated_at']


class ReviewHelpfulSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    
    class Meta:
        model = ReviewHelpful
        fields = ['id', 'review', 'user', 'user_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ComplaintSerializer(serializers.ModelSerializer):
    reporter_name = serializers.ReadOnlyField(source='reporter.full_name')
    property_title = serializers.ReadOnlyField(source='accommodation_property.title')
    resolved_by_name = serializers.ReadOnlyField(source='resolved_by.full_name')
    
    class Meta:
        model = Complaint
        fields = ['id', 'reporter', 'reporter_name', 'accommodation_property', 'property_title', 'booking',
                  'category', 'priority', 'status', 'subject', 'description', 'resolution_notes',
                  'resolved_by', 'resolved_by_name', 'resolved_at', 'attachment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'resolved_at', 'created_at', 'updated_at']


class PropertyReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.ReadOnlyField(source='reporter.full_name')
    property_title = serializers.ReadOnlyField(source='accommodation_property.title')
    reviewed_by_name = serializers.ReadOnlyField(source='reviewed_by.full_name')
    
    class Meta:
        model = PropertyReport
        fields = ['id', 'reporter', 'reporter_name', 'accommodation_property', 'property_title', 'report_type',
                  'status', 'description', 'evidence', 'admin_notes', 'reviewed_by', 'reviewed_by_name',
                  'reviewed_at', 'created_at']
        read_only_fields = ['id', 'reviewed_at', 'created_at']


class UserFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    responded_by_name = serializers.ReadOnlyField(source='responded_by.full_name')
    
    class Meta:
        model = UserFeedback
        fields = ['id', 'user', 'user_name', 'feedback_type', 'subject', 'message', 'page_url',
                  'browser_info', 'response', 'responded_by', 'responded_by_name', 'responded_at',
                  'created_at']
        read_only_fields = ['id', 'responded_at', 'created_at']
