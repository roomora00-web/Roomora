from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    PropertyType, Amenity, Property, PropertyAmenity, PropertyImage, PropertyVideo, PropertyViewing,
    RoomType, RoomTypePricing, UnitType, UnitTypePricing, RentalDuration, SavedProperty
)
from .serializers import (
    PropertyTypeSerializer, AmenitySerializer, PropertySerializer,
    PropertyImageSerializer, PropertyVideoSerializer, PropertyViewingSerializer,
    RoomTypeSerializer, RoomTypePricingSerializer, UnitTypeSerializer, UnitTypePricingSerializer, RentalDurationSerializer
)
from .forms import PropertySearchForm
from django.core.paginator import Paginator


class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'category']
    filterset_fields = ['category']


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.select_related('uploaded_by').prefetch_related('images', 'room_types', 'unit_types', 'rental_durations').all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'description', 'address', 'city', 'property_code']
    filterset_fields = ['property_type', 'property_category', 'city', 'country', 'is_available', 'is_verified', 'is_featured', 'status']
    ordering_fields = ['created_at', 'views_count', 'saves_count']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def increment_views(self, request, pk=None):
        from bookings.models import RecentlyViewed
        from django.utils import timezone
        
        property = self.get_object()
        property.views_count += 1
        property.save()
        
        # Track recently viewed for authenticated users
        if request.user.is_authenticated:
            RecentlyViewed.objects.update_or_create(
                user=request.user,
                property=property,
                defaults={'viewed_at': timezone.now()}
            )
        
        return Response({'views_count': property.views_count})
    
    @action(detail=True, methods=['get'])
    def room_types(self, request, pk=None):
        property = self.get_object()
        room_types = property.room_types.filter(available_slots__gt=0)
        serializer = RoomTypeSerializer(room_types, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def unit_types(self, request, pk=None):
        property = self.get_object()
        unit_types = property.unit_types.filter(available_units__gt=0)
        serializer = UnitTypeSerializer(unit_types, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        property = self.get_object()
        images = property.images.all()
        serializer = PropertyImageSerializer(images, many=True)
        return Response(serializer.data)


class RoomTypeViewSet(viewsets.ModelViewSet):
    queryset = RoomType.objects.select_related('accommodation_property').prefetch_related('pricing_models').all()
    serializer_class = RoomTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'occupancy_type', 'gender_restriction', 'preferred_lifestyle']
    
    def perform_create(self, serializer):
        serializer.save()


class RoomTypePricingViewSet(viewsets.ModelViewSet):
    queryset = RoomTypePricing.objects.select_related('room_type').all()
    serializer_class = RoomTypePricingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room_type', 'payment_type']


class UnitTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitType.objects.select_related('accommodation_property').prefetch_related('pricing_models').all()
    serializer_class = UnitTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'furnished_status', 'shared_apartment_allowed']
    
    def perform_create(self, serializer):
        serializer.save()


class UnitTypePricingViewSet(viewsets.ModelViewSet):
    queryset = UnitTypePricing.objects.select_related('unit_type').all()
    serializer_class = UnitTypePricingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['unit_type', 'payment_type']


class RentalDurationViewSet(viewsets.ModelViewSet):
    queryset = RentalDuration.objects.select_related('accommodation_property').all()
    serializer_class = RentalDurationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'duration_type', 'required_advance']


class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.select_related('accommodation_property').all()
    serializer_class = PropertyImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'image_type']
    
    def perform_create(self, serializer):
        serializer.save()


class PropertyVideoViewSet(viewsets.ModelViewSet):
    queryset = PropertyVideo.objects.select_related('accommodation_property').all()
    serializer_class = PropertyVideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'is_virtual_tour']
    
    def perform_create(self, serializer):
        serializer.save()


class PropertyViewingViewSet(viewsets.ModelViewSet):
    queryset = PropertyViewing.objects.select_related('accommodation_property', 'user').all()
    serializer_class = PropertyViewingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['accommodation_property', 'user', 'status']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavedPropertyViewSet(viewsets.ModelViewSet):
    """API ViewSet for managing saved properties with AJAX support"""
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SavedProperty.objects.filter(user=self.request.user).select_related('property')
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_notes(self, request, pk=None):
        """Update notes for a saved property via AJAX"""
        try:
            saved_property = SavedProperty.objects.get(id=pk, user=request.user)
            saved_property.notes = request.data.get('notes', '')
            saved_property.save()
            return Response({'success': True, 'notes': saved_property.notes})
        except SavedProperty.DoesNotExist:
            return Response({'error': 'Saved property not found'}, status=404)


def property_search_view(request):
    """Property search view - Phase 3: Property Discovery and Search System"""
    from bookings.models import PropertySearch, RecentlyViewed
    from django.utils import timezone
    
    form = PropertySearchForm(request.GET or None)
    properties = Property.objects.filter(status='APPROVED', is_available=True)
    
    search_created = False
    
    # Apply filters
    if form.is_valid():
        cleaned_data = form.cleaned_data
        
        # Search query
        if cleaned_data.get('query'):
            query = cleaned_data['query']
            properties = properties.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(address__icontains=query) |
                Q(city__icontains=query) |
                Q(nearest_institution__icontains=query)
            )
        
        # Location filters
        if cleaned_data.get('city'):
            properties = properties.filter(city__icontains=cleaned_data['city'])
        
        if cleaned_data.get('nearest_institution'):
            properties = properties.filter(nearest_institution__icontains=cleaned_data['nearest_institution'])
        
        if cleaned_data.get('distance_to_campus'):
            properties = properties.filter(distance_to_campus__lte=cleaned_data['distance_to_campus'])
        
        # Property type filters
        property_types = cleaned_data.get('property_type', [])
        if property_types:
            properties = properties.filter(property_type__in=property_types)
        
        # Price range
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        if min_price or max_price:
            # Filter based on room type or unit type pricing
            # This is a simplified version - in production you'd need more complex logic
            pass
        
        # Availability
        if cleaned_data.get('show_available_only'):
            properties = properties.filter(is_available=True)
        
        # Target audience
        target_audience = cleaned_data.get('target_audience', [])
        if target_audience:
            audience_filters = Q()
            if 'students' in target_audience:
                audience_filters |= Q(suitable_for_students=True)
            if 'workers' in target_audience:
                audience_filters |= Q(suitable_for_workers=True)
            if 'families' in target_audience:
                audience_filters |= Q(suitable_for_families=True)
            if 'couples' in target_audience:
                audience_filters |= Q(suitable_for_couples=True)
            properties = properties.filter(audience_filters)
        
        # Sorting
        sort_by = cleaned_data.get('sort_by', 'relevance')
        if sort_by == 'price_low':
            properties = properties.order_by('room_types__pricing_models__monthly_price')
        elif sort_by == 'price_high':
            properties = properties.order_by('-room_types__pricing_models__monthly_price')
        elif sort_by == 'availability':
            properties = properties.order_by('-room_types__available_slots')
        elif sort_by == 'distance':
            properties = properties.order_by('distance_to_campus')
        else:
            properties = properties.order_by('-created_at')
        
        # Save search to history if user is authenticated
        if request.user.is_authenticated and (cleaned_data.get('city') or cleaned_data.get('nearest_institution') or cleaned_data.get('query')):
            PropertySearch.objects.create(
                user=request.user,
                city=cleaned_data.get('city', ''),
                institution=cleaned_data.get('nearest_institution', ''),
                room_type=cleaned_data.get('property_type', [None])[0] if cleaned_data.get('property_type') else '',
                min_price=min_price,
                max_price=max_price,
            )
            search_created = True
    
    # Get primary images for properties
    for property in properties:
        primary_image = property.images.filter(is_primary=True).first()
        property.primary_image = primary_image
    
    context = {
        'form': form,
        'properties': properties,
        'results_count': properties.count(),
        'search_created': search_created,
    }
    
    return render(request, 'properties/search.html', context)





@login_required
def property_comparison_view(request):
    """Property comparison view - Phase 4"""
    # Get properties to compare (from query params or session)
    property_ids = request.GET.getlist('properties')
    
    if not property_ids:
        # Try to get from comparison group
        comparison_group = request.GET.get('group')
        if comparison_group:
            saved_properties = SavedProperty.objects.filter(
                user=request.user,
                comparison_group=comparison_group
            )
            property_ids = [sp.property_id for sp in saved_properties]
    
    properties = Property.objects.filter(id__in=property_ids, status='APPROVED')
    
    # Get primary images and pricing
    for property in properties:
        primary_image = property.images.filter(is_primary=True).first()
        property.primary_image = primary_image
        
        # Get pricing
        if property.room_types.exists():
            property.pricing = property.room_types.first().pricing_models.first()
        elif property.unit_types.exists():
            property.pricing = property.unit_types.first().pricing_models.first()
        else:
            property.pricing = None
    
    context = {
        'properties': properties,
    }
    
    return render(request, 'properties/compare.html', context)


def property_autocomplete_view(request):
    """API endpoint for property search autocomplete - Phase 3"""
    from rest_framework.response import Response
    from django.http import JsonResponse
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = {
        'areas': [],
        'institutions': [],
        'properties': [],
    }
    
    # Search areas/cities
    cities = Property.objects.filter(
        city__icontains=query,
        status='APPROVED'
    ).values_list('city', flat=True).distinct()[:5]
    results['areas'] = list(cities)
    
    # Search institutions
    institutions = Property.objects.filter(
        nearest_institution__icontains=query,
        status='APPROVED'
    ).values_list('nearest_institution', flat=True).distinct()[:5]
    results['institutions'] = list(institutions)
    
    # Search property names
    properties = Property.objects.filter(
        Q(title__icontains=query) | Q(address__icontains=query),
        status='APPROVED'
    ).values('id', 'title')[:5]
    results['properties'] = list(properties)
    
    return JsonResponse(results)


@login_required
def saved_properties_view(request):
    """Display user's saved properties with filtering and sorting"""
    from django.db.models import Avg, Count
    # Get user's saved properties
    saved_properties = SavedProperty.objects.filter(
        user=request.user
    ).select_related('property').prefetch_related('property__images', 'property__room_types', 'property__unit_types')
    
    # Annotate with rating and reviews count
    saved_properties = saved_properties.annotate(
        annotated_rating=Avg('property__reviews__rating'),
        annotated_reviews_count=Count('property__reviews')
    )
    
    # Apply filters
    location_filter = request.GET.get('location')
    property_type_filter = request.GET.get('property_type')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    availability_filter = request.GET.get('availability')
    room_type_filter = request.GET.get('room_type')
    rating_filter = request.GET.get('rating')
    
    if location_filter and location_filter != 'all':
        saved_properties = saved_properties.filter(property__city__icontains=location_filter)
    
    if property_type_filter and property_type_filter != 'all':
        saved_properties = saved_properties.filter(property__property_type=property_type_filter)
    
    if price_min:
        saved_properties = saved_properties.filter(
            property__room_types__pricing_models__monthly_price__gte=float(price_min)
        )
    
    if price_max:
        saved_properties = saved_properties.filter(
            property__room_types__pricing_models__monthly_price__lte=float(price_max)
        )
    
    if availability_filter:
        if availability_filter == 'available':
            saved_properties = saved_properties.filter(
                Q(property__room_types__available_slots__gt=0) |
                Q(property__unit_types__available_units__gt=0)
            )
        elif availability_filter == 'sold_out':
            saved_properties = saved_properties.filter(
                Q(property__room_types__available_slots=0) &
                Q(property__unit_types__available_units=0)
            )
    
    if room_type_filter and room_type_filter != 'all':
        saved_properties = saved_properties.filter(
            property__room_types__occupancy_type=room_type_filter
        )
    
    if rating_filter:
        min_rating = float(rating_filter)
        saved_properties = saved_properties.filter(
            annotated_rating__gte=min_rating
        )
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'recent')
    if sort_by == 'recent':
        saved_properties = saved_properties.order_by('-created_at')
    elif sort_by == 'oldest':
        saved_properties = saved_properties.order_by('created_at')
    elif sort_by == 'price_high':
        saved_properties = saved_properties.order_by('-property__room_types__pricing_models__monthly_price')
    elif sort_by == 'price_low':
        saved_properties = saved_properties.order_by('property__room_types__pricing_models__monthly_price')
    elif sort_by == 'rating':
        saved_properties = saved_properties.order_by('-annotated_rating')
    elif sort_by == 'reviews':
        saved_properties = saved_properties.order_by('-annotated_reviews_count')
    
    # Pagination
    paginator = Paginator(saved_properties, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_saved = saved_properties.count()
    hostels_count = saved_properties.filter(property__property_type='HOSTEL').count()
    apartments_count = saved_properties.filter(property__property_type='APARTMENT').count()
    
    # Price range statistics
    prices = []
    for sp in saved_properties:
        pricing = None
        if sp.property.room_types.exists():
            pricing = sp.property.room_types.first().pricing_models.first()
        elif sp.property.unit_types.exists():
            pricing = sp.property.unit_types.first().pricing_models.first()
            
        if pricing:
            price_val = pricing.monthly_price or pricing.semester_price or pricing.yearly_price
            if price_val:
                prices.append(price_val)
    
    if prices:
        lowest_price = min(prices)
        highest_price = max(prices)
        avg_price = sum(prices) / len(prices)
    else:
        lowest_price = 0
        highest_price = 0
        avg_price = 0
    
    # Average rating
    ratings = [sp.property.average_rating for sp in saved_properties if sp.property.average_rating]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Get filter options
    locations = Property.objects.filter(
        saved_by__user=request.user
    ).values_list('city', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'total_saved': total_saved,
        'hostels_count': hostels_count,
        'apartments_count': apartments_count,
        'lowest_price': lowest_price,
        'highest_price': highest_price,
        'avg_price': avg_price,
        'avg_rating': avg_rating,
        'locations': locations,
        'current_filters': {
            'location': location_filter,
            'property_type': property_type_filter,
            'price_min': price_min,
            'price_max': price_max,
            'availability': availability_filter,
            'room_type': room_type_filter,
            'rating': rating_filter,
            'sort': sort_by,
        },
        'view_mode': request.GET.get('view', 'grid'),
    }
    
    return render(request, 'properties/saved_properties.html', context)


@login_required
def save_property_view(request, property_id):
    """Save a property to user's saved list"""
    property_obj = get_object_or_404(Property, id=property_id, status='APPROVED')
    
    saved_property, created = SavedProperty.objects.get_or_create(
        user=request.user,
        property=property_obj
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': 'saved' if created else 'already_saved',
            'message': 'Property saved successfully' if created else 'Property already saved'
        })
    
    return redirect('properties:saved_properties')


@login_required
def unsave_property_view(request, property_id):
    """Remove a property from user's saved list"""
    saved_property = get_object_or_404(
        SavedProperty,
        user=request.user,
        property_id=property_id
    )
    saved_property.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': 'unsaved',
            'message': 'Property removed from saved'
        })
    
    return redirect('properties:saved_properties')


@login_required
def update_property_note_view(request, property_id):
    """Update personal note on a saved property"""
    saved_property = get_object_or_404(
        SavedProperty,
        user=request.user,
        property_id=property_id
    )
    
    if request.method == 'POST':
        import json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                note = data.get('note', '')
            except json.JSONDecodeError:
                note = ''
        else:
            note = request.POST.get('note', '')
            
        saved_property.notes = note
        saved_property.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'note': note,
                'message': 'Note updated successfully'
            })
    
    return redirect('properties:saved_properties')
