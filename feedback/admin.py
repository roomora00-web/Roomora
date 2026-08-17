from django.contrib import admin
from .models import Review, ReviewImage, ReviewHelpful, Complaint, PropertyReport, UserFeedback


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'reviewer', 'accommodation_property', 'rating', 'status', 'trust_score', 'verification_level', 'created_at']
    list_filter = ['status', 'verification_level', 'is_verified', 'rating', 'created_at']
    search_fields = ['reviewer__email', 'accommodation_property__title', 'title', 'content']
    ordering = ['status', '-created_at']  # Show PENDING first
    readonly_fields = ['trust_score']
    
    fieldsets = (
        ('Basic Info', {'fields': ('reviewer', 'accommodation_property', 'booking', 'review_type', 'status')}),
        ('Ratings', {'fields': ('rating', 'cleanliness_rating', 'location_rating', 'amenities_rating', 'communication_rating', 'value_rating')}),
        ('Content', {'fields': ('title', 'content', 'guest_type', 'recommendation', 'would_stay_again', 'aspects_highlighted', 'concerns')}),
        ('Response', {'fields': ('response', 'responded_by', 'responded_at')}),
        ('Moderation & Trust', {'fields': ('trust_score', 'verification_level', 'is_verified', 'is_featured', 'flag_reason')}),
        ('Metadata', {'fields': ('helpful_count',)}),
    )
    
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='APPROVED')
        self.message_user(request, f'{updated} reviews successfully marked as APPROVED.')
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='REJECTED')
        self.message_user(request, f'{updated} reviews successfully marked as REJECTED.')
    reject_reviews.short_description = "Reject selected reviews"
    
    inlines = [ReviewImageInline]


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['review', 'caption', 'uploaded_at']
    search_fields = ['review__title', 'caption']
    ordering = ['-uploaded_at']


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__title', 'user__email']
    ordering = ['-created_at']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['id', 'reporter', 'category', 'priority', 'status', 'subject', 'created_at']
    list_filter = ['category', 'priority', 'status', 'created_at']
    search_fields = ['reporter__email', 'subject', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('reporter', 'accommodation_property', 'booking', 'category', 'priority', 'status')}),
        ('Details', {'fields': ('subject', 'description', 'attachment')}),
        ('Resolution', {'fields': ('resolution_notes', 'resolved_by', 'resolved_at')}),
    )


@admin.register(PropertyReport)
class PropertyReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'reporter', 'accommodation_property', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['reporter__email', 'accommodation_property__title', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('reporter', 'accommodation_property', 'report_type', 'status')}),
        ('Details', {'fields': ('description', 'evidence')}),
        ('Admin Response', {'fields': ('admin_notes', 'reviewed_by', 'reviewed_at')}),
    )


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'feedback_type', 'subject', 'responded_at', 'created_at']
    list_filter = ['feedback_type', 'created_at', 'responded_at']
    search_fields = ['user__email', 'subject', 'message']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'feedback_type', 'subject', 'message')}),
        ('System Info', {'fields': ('page_url', 'browser_info')}),
        ('Response', {'fields': ('response', 'responded_by', 'responded_at')}),
    )
