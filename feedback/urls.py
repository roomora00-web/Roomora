from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReviewViewSet, ReviewImageViewSet, ReviewHelpfulViewSet,
    ComplaintViewSet, PropertyReportViewSet, UserFeedbackViewSet,
    write_review
)

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'review-images', ReviewImageViewSet, basename='reviewimage')
router.register(r'review-helpful', ReviewHelpfulViewSet, basename='reviewhelpful')
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'property-reports', PropertyReportViewSet, basename='propertyreport')
router.register(r'user-feedback', UserFeedbackViewSet, basename='userfeedback')

urlpatterns = [
    path('', include(router.urls)),
    path('write-review/<int:property_id>/', write_review, name='write_review'),
]
