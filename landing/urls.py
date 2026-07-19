from django.urls import path
from .views import HomeView, HostelsView, HostelDetailsView, ApartmentsView, ApartmentDetailsView, FeaturedView, PropertiesView, PropertyDetailView, PropertyReviewsPartialView, PropertyMapView

app_name = 'landing'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('hostels/', HostelsView.as_view(), name='hostels'),
    path('hostel-details/', HostelDetailsView.as_view(), name='hostel_details'),
    path('apartments/', ApartmentsView.as_view(), name='apartments'),
    path('apartment-details/', ApartmentDetailsView.as_view(), name='apartment_details'),
    path('featured/', FeaturedView.as_view(), name='featured'),
    path('properties/', PropertiesView.as_view(), name='properties'),
    path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property_detail'),
    path('properties/<int:pk>/reviews/', PropertyReviewsPartialView.as_view(), name='property_reviews_partial'),
    path('properties/map/', PropertyMapView.as_view(), name='property_map'),
]
