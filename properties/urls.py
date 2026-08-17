from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PropertyTypeViewSet, AmenityViewSet, PropertyViewSet,
    RoomTypeViewSet, RoomTypePricingViewSet, UnitTypeViewSet, UnitTypePricingViewSet, RentalDurationViewSet,
    PropertyImageViewSet, PropertyVideoViewSet, PropertyViewingViewSet, property_search_view,
    saved_properties_view, save_property_view, unsave_property_view, property_comparison_view,
    property_autocomplete_view, SavedPropertyViewSet, update_property_note_view
)

app_name = 'properties'

router = DefaultRouter()
router.register(r'property-types', PropertyTypeViewSet, basename='propertytype')
router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'room-types', RoomTypeViewSet, basename='roomtype')
router.register(r'room-type-pricing', RoomTypePricingViewSet, basename='roomtypepricing')
router.register(r'unit-types', UnitTypeViewSet, basename='unittype')
router.register(r'unit-type-pricing', UnitTypePricingViewSet, basename='unittypepricing')
router.register(r'rental-durations', RentalDurationViewSet, basename='rentalduration')
router.register(r'property-images', PropertyImageViewSet, basename='propertyimage')
router.register(r'property-videos', PropertyVideoViewSet, basename='propertyvideo')
router.register(r'property-viewings', PropertyViewingViewSet, basename='propertyviewing')
router.register(r'saved-properties', SavedPropertyViewSet, basename='saved-property')

urlpatterns = [
    path('search/', property_search_view, name='property-search'),
    path('autocomplete/', property_autocomplete_view, name='property-autocomplete'),
    path('saved/', saved_properties_view, name='saved-properties'),
    path('save/<int:property_id>/', save_property_view, name='save-property'),
    path('unsave/<int:property_id>/', unsave_property_view, name='unsave-property'),
    path('update-note/<int:property_id>/', update_property_note_view, name='update-property-note'),
    path('compare/', property_comparison_view, name='property-compare'),
    path('', include(router.urls)),
]
