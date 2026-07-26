from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, DetailView
import json
from django.db.models import Q, Min, Max
from django.db.models.functions import Coalesce
from django.conf import settings
from properties.models import Property, PropertyImage, RoomType, RoomTypePricing, UnitTypePricing, Amenity
from feedback.views import get_property_reviews

class HomeView(TemplateView):
    template_name = 'landing/home.html'

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in HomeView.get: {e}")
            from django.http import HttpResponse
            return HttpResponse(f"Error loading page: {str(e)}", status=500)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Fetch featured/popular hostels
            context['category_hostels'] = Property.objects.filter(
                status='APPROVED', is_available=True, property_type='HOSTEL'
            ).prefetch_related('images', 'room_types__pricing_models')[:6]

            # Fetch featured/popular apartments
            context['category_apartments'] = Property.objects.filter(
                status='APPROVED', is_available=True, property_type='APARTMENT'
            ).prefetch_related('images', 'unit_types__pricing_models', 'amenities')[:6]

            from django.db.models import Avg
            # Fetch premium/featured listings (ordered by featured status & review rating)
            premium_listings = Property.objects.filter(
                status='APPROVED'
            ).annotate(
                avg_rating=Avg('reviews__rating')
            ).order_by('-is_featured', '-avg_rating', '-id').prefetch_related('images', 'room_types__pricing_models', 'unit_types__pricing_models', 'amenities')

            context['premium_listings'] = premium_listings[:6]
            context['featured_property'] = premium_listings.first()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching properties: {e}")
            context['category_hostels'] = []
            context['category_apartments'] = []
            context['premium_listings'] = []
            context['featured_property'] = None
        
        # Search Widget Data
        context['property_types'] = Property.PROPERTY_TYPE_CHOICES
        context['cities'] = Property.objects.filter(status='APPROVED', is_available=True).values_list('city', flat=True).order_by('city').distinct()
        context['price_ranges'] = [
            {'min': 0, 'max': 2000, 'label': 'Under GHC 2,000'},
            {'min': 2000, 'max': 5000, 'label': 'GHC 2,000 - 5,000'},
            {'min': 5000, 'max': 10000, 'label': 'GHC 5,000 - 10,000'},
            {'min': 10000, 'max': '', 'label': 'Above GHC 10,000'},
        ]
        from properties.models import RoomType, SavedProperty
        context['room_occupancy_types'] = RoomType.OCCUPANCY_TYPE_CHOICES
        if hasattr(self, 'request') and self.request and getattr(self.request, 'user', None) and self.request.user.is_authenticated:
            context['user_saved_property_ids'] = set(
                SavedProperty.objects.filter(user=self.request.user).values_list('property_id', flat=True)
            )
        else:
            context['user_saved_property_ids'] = set()
        context['tenant_types'] = [
            {'value': 'student', 'label': 'Student'},
            {'value': 'professional', 'label': 'Professional'},
            {'value': 'any', 'label': 'Any'},
        ]
        
        # Prepare map properties (first 20 to avoid slowing down homepage too much, or all featured)
        try:
            map_properties = []
            for prop in Property.objects.filter(status='APPROVED', is_available=True)[:20]:
                if prop.images.exists():
                    img_field = prop.images.first().image
                    img_url = str(img_field) if str(img_field).startswith('http') else img_field.url
                else:
                    img_url = '/static/images/placeholder.jpg'
                price = 0
                if prop.property_type == 'HOSTEL' and prop.room_types.exists():
                    rt = prop.room_types.first()
                    pm = rt.pricing_models.first()
                    if pm:
                        price = pm.monthly_price or pm.semester_price or pm.yearly_price or 0
                elif prop.property_type == 'APARTMENT' and prop.unit_types.exists():
                    ut = prop.unit_types.first()
                    pm = ut.pricing_models.first()
                    if pm:
                        price = pm.monthly_price or pm.semester_price or pm.yearly_price or 0

                map_properties.append({
                    'id': prop.id,
                    'title': prop.title,
                    'lat': float(prop.latitude) if prop.latitude is not None else 5.6037,
                    'lng': float(prop.longitude) if prop.longitude is not None else -0.1870,
                    'price': float(price) if price else 0,
                    'image': img_url,
                    'available_slots': sum(rt.available_slots for rt in prop.room_types.all()) + sum(ut.available_units for ut in prop.unit_types.all()) if prop.has_available_rooms else 0,
                    'type': prop.get_property_type_display(),
                    'is_verified': prop.is_verified,
                    'address': f"{prop.city}, {prop.region}"
                })

            context['map_properties_json'] = json.dumps(map_properties)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error preparing map properties: {e}")
            context['map_properties_json'] = json.dumps([])
        
        return context

class HostelsView(TemplateView):
    template_name = 'landing/hostels.html'

class HostelDetailsView(TemplateView):
    template_name = 'landing/hostel_details.html'

class ApartmentsView(TemplateView):
    template_name = 'landing/apartments.html'

class ApartmentDetailsView(TemplateView):
    template_name = 'landing/apartment_details.html'

class FeaturedView(TemplateView):
    template_name = 'landing/featured.html'

class PropertiesView(TemplateView):
    template_name = 'landing/properties.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            from django.http import JsonResponse
            html = render_to_string('landing/partials/property_cards.html', context, request=request)
            return JsonResponse({'html': html, 'count': context['total_count']})
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get query parameters
        location = self.request.GET.get('location', '')
        property_type = self.request.GET.get('property_type', '')
        min_price = self.request.GET.get('min_price', '')
        max_price = self.request.GET.get('max_price', '')
        min_bedrooms = self.request.GET.get('min_bedrooms', '')
        amenities = self.request.GET.getlist('amenities', [])
        superhost = self.request.GET.get('superhost', '')
        sort_by = self.request.GET.get('sort_by', 'recommended')
        
        # Base queryset
        properties = Property.objects.filter(
            status='APPROVED',
            is_available=True
        ).select_related('uploaded_by').prefetch_related(
            'images', 
            'amenities', 
            'room_types__pricing_models',
            'unit_types__pricing_models'
        )
        
        # Apply filters
        if location:
            properties = properties.filter(
                Q(city__icontains=location) | 
                Q(region__icontains=location) | 
                Q(title__icontains=location) |
                Q(country__icontains=location)
            )
        
        if property_type:
            properties = properties.filter(property_type=property_type)
        
        # Price filtering
        if min_price or max_price:
            price_filter = Q()
            if min_price:
                price_filter |= Q(room_types__pricing_models__monthly_price__gte=min_price)
                price_filter |= Q(room_types__pricing_models__semester_price__gte=min_price)
                price_filter |= Q(room_types__pricing_models__yearly_price__gte=min_price)
                price_filter |= Q(unit_types__pricing_models__monthly_price__gte=min_price)
                price_filter |= Q(unit_types__pricing_models__semester_price__gte=min_price)
                price_filter |= Q(unit_types__pricing_models__yearly_price__gte=min_price)
            if max_price:
                price_filter |= Q(room_types__pricing_models__monthly_price__lte=max_price)
                price_filter |= Q(room_types__pricing_models__semester_price__lte=max_price)
                price_filter |= Q(room_types__pricing_models__yearly_price__lte=max_price)
                price_filter |= Q(unit_types__pricing_models__monthly_price__lte=max_price)
                price_filter |= Q(unit_types__pricing_models__semester_price__lte=max_price)
                price_filter |= Q(unit_types__pricing_models__yearly_price__lte=max_price)
            properties = properties.filter(price_filter).distinct()
            
        # Bedroom filtering (Only applies to apartments with unit types)
        if min_bedrooms and min_bedrooms != '0':
            properties = properties.filter(unit_types__bedrooms__gte=int(min_bedrooms))
        
        # Amenities filtering
        if amenities:
            for amenity_id in amenities:
                properties = properties.filter(amenities__id=amenity_id)
        
        # Superhost filter
        if superhost == 'true':
            properties = properties.filter(is_verified=True)
        
        # Sorting
        if sort_by == 'price_low':
            properties = properties.annotate(
                min_price=Coalesce(
                    Min('room_types__pricing_models__monthly_price'),
                    Min('room_types__pricing_models__semester_price'),
                    Min('room_types__pricing_models__yearly_price'),
                    Min('unit_types__pricing_models__monthly_price'),
                    Min('unit_types__pricing_models__semester_price'),
                    Min('unit_types__pricing_models__yearly_price')
                )
            ).order_by('min_price')
        elif sort_by == 'price_high':
            properties = properties.annotate(
                max_price=Coalesce(
                    Max('room_types__pricing_models__monthly_price'),
                    Max('room_types__pricing_models__semester_price'),
                    Max('room_types__pricing_models__yearly_price'),
                    Max('unit_types__pricing_models__monthly_price'),
                    Max('unit_types__pricing_models__semester_price'),
                    Max('unit_types__pricing_models__yearly_price')
                )
            ).order_by('-max_price')
        elif sort_by == 'rating':
            properties = properties.order_by('-safety_score')
        elif sort_by == 'newest':
            properties = properties.order_by('-created_at')
        else:  # recommended
            properties = properties.order_by('-is_featured', '-safety_score')
        
        context['properties'] = properties
        context['total_count'] = properties.count()
        
        # Filter options
        context['all_amenities'] = Amenity.objects.all()
        context['property_types'] = Property.PROPERTY_TYPE_CHOICES
        if hasattr(self, 'request') and self.request and getattr(self.request, 'user', None) and self.request.user.is_authenticated:
            from properties.models import SavedProperty
            context['user_saved_property_ids'] = set(
                SavedProperty.objects.filter(user=self.request.user).values_list('property_id', flat=True)
            )
        else:
            context['user_saved_property_ids'] = set()
        
        # Current filter values
        context['current_filters'] = {
            'location': location,
            'property_type': property_type,
            'min_price': min_price,
            'max_price': max_price,
            'min_bedrooms': min_bedrooms,
            'amenities': [str(a) for a in amenities],
            'superhost': superhost,
            'sort_by': sort_by,
        }
        
        # Prepare JSON for Map
        map_properties = []
        for prop in properties:
            # get price
            price = "Contact"
            if prop.property_type == 'HOSTEL':
                room_pricing = prop.room_types.first().pricing_models.first() if prop.room_types.first() else None
                if room_pricing:
                    price = f"GH₵ {room_pricing.semester_price or room_pricing.monthly_price}/sem"
            else:
                unit_pricing = prop.unit_types.first().pricing_models.first() if prop.unit_types.first() else None
                if unit_pricing:
                    price = f"GH₵ {unit_pricing.monthly_price or unit_pricing.yearly_price}/mo"
                    
            # get image
            if prop.images.first():
                img_field = prop.images.first().image
                img_url = str(img_field) if str(img_field).startswith('http') else img_field.url
            else:
                img_url = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400&h=300&fit=crop"
            
            map_properties.append({
                'id': prop.id,
                'title': prop.title,
                'lat': float(prop.latitude) if prop.latitude is not None else 5.6037,
                'lng': float(prop.longitude) if prop.longitude is not None else -0.1870,
                'price': price,
                'image': img_url,
                'available_slots': sum(rt.available_slots for rt in prop.room_types.all()) + sum(ut.available_units for ut in prop.unit_types.all()) if prop.has_available_rooms else 0,
                'type': prop.get_property_type_display(),
                'is_verified': prop.is_verified,
                'address': f"{prop.city}, {prop.region}"
            })
        
        context['map_properties_json'] = json.dumps(map_properties)
        
        return context

class PropertyDetailView(DetailView):
    model = Property
    template_name = 'landing/property_detail.html'
    context_object_name = 'property'

    def get_queryset(self):
        return Property.objects.filter(
            status='APPROVED',
            is_available=True
        ).select_related('uploaded_by').prefetch_related(
            'images',
            'amenities',
            'room_types__pricing_models',
            'unit_types__pricing_models',
            'rental_durations',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_obj = self.object
        
        # Add Google Maps API key to context
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY

        # ── Reviews ────────────────────────────────────────────────────────────
        review_data = get_property_reviews(property_obj.id, status='APPROVED')
        context['reviews'] = review_data['reviews'][:6]
        context['reviews_count'] = review_data['aggregation']['total_reviews'] or 0
        context['average_rating'] = round(review_data['aggregation']['avg_rating'] or 0, 1)
        context['rating_distribution'] = review_data['rating_distribution']
        context['top_themes'] = review_data.get('top_themes', [])
        context['top_concerns'] = review_data.get('top_concerns', [])
        
        # Detailed category ratings
        context['category_ratings'] = {
            'cleanliness': round(review_data['aggregation']['avg_cleanliness'] or 0, 1),
            'location': round(review_data['aggregation']['avg_location'] or 0, 1),
            'amenities': round(review_data['aggregation']['avg_amenities'] or 0, 1),
            'communication': round(review_data['aggregation']['avg_communication'] or 0, 1),
            'value': round(review_data['aggregation']['avg_value'] or 0, 1),
        }

        # ── Amenities grouped by category ──────────────────────────────────────
        all_amenities = property_obj.amenities.all()
        amenity_groups = {}
        for amenity in all_amenities:
            cat = amenity.get_category_display()
            amenity_groups.setdefault(cat, []).append(amenity)
        context['amenity_groups'] = amenity_groups

        # ── Related properties ─────────────────────────────────────────────────
        related_properties = Property.objects.filter(
            status='APPROVED',
            is_available=True,
            city=property_obj.city
        ).exclude(id=property_obj.id).prefetch_related(
            'images',
            'room_types__pricing_models',
            'unit_types__pricing_models',
        )[:4]
        context['related_properties'] = related_properties

        # ── Minimum starting price calculation ─────────────────────────────────
        min_price = None
        for rt in property_obj.room_types.all():
            for pm in rt.pricing_models.all():
                p_val = pm.semester_price or pm.monthly_price or pm.yearly_price
                if p_val and (min_price is None or p_val < min_price):
                    min_price = p_val
        for ut in property_obj.unit_types.all():
            for pm in ut.pricing_models.all():
                p_val = pm.monthly_price or pm.yearly_price or pm.semester_price
                if p_val and (min_price is None or p_val < min_price):
                    min_price = p_val
        context['min_starting_price'] = min_price

        # ── Has shared rooms (for roommate matching section) ───────────────────
        context['has_shared_rooms'] = property_obj.room_types.exclude(
            occupancy_type='SINGLE'
        ).exists()

        # Increment view count
        Property.objects.filter(pk=property_obj.pk).update(
            views_count=property_obj.views_count + 1
        )
        
        # Check if property is saved by current user
        context['is_saved'] = False
        if self.request.user.is_authenticated:
            from properties.models import SavedProperty
            context['is_saved'] = SavedProperty.objects.filter(
                user=self.request.user, 
                property=property_obj
            ).exists()

        # ── Prepare image captions for lightbox ───────────────────────────────────
        image_captions = []
        for img in property_obj.images.all():
            caption = img.caption if img.caption else img.get_image_type_display()
            image_captions.append(caption)
        context['image_captions'] = image_captions

        # ── Proximity destinations for structured table ───────────────────────────
        context['proximity_destinations'] = property_obj.proximity_destinations.all()

        # ── Review eligibility for inline modal ────────────────────────────────
        context['user_can_review'] = False
        context['user_already_reviewed'] = False
        context['user_review'] = None
        if self.request.user.is_authenticated:
            from feedback.views import check_review_eligibility
            from feedback.models import Review
            ineligible, _ = check_review_eligibility(self.request.user, property_obj)
            context['user_can_review'] = not ineligible
            existing_review = Review.objects.filter(
                reviewer=self.request.user,
                accommodation_property=property_obj
            ).first()
            if existing_review:
                context['user_already_reviewed'] = True
                context['user_review'] = existing_review

        # ── Smart Location & Proximity Intelligence ───────────────────────────
        from bookings.services.ai_service import NvidiaAIService
        user_to_use = self.request.user if self.request.user.is_authenticated else None
        context['location_insights'] = NvidiaAIService.get_location_and_property_insights(
            user=user_to_use,
            search_location=getattr(property_obj, 'nearest_institution', '') or "University Campus",
            selected_city=getattr(property_obj, 'city', '') or "Accra",
            recommended_properties=[property_obj]
        )

        return context


class PropertyReviewsPartialView(TemplateView):
    template_name = 'landing/partials/review_cards.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_id = self.kwargs.get('pk')
        
        # Get base queryset
        from feedback.models import Review
        reviews = Review.objects.filter(
            accommodation_property_id=property_id,
            review_type='PROPERTY',
            status='APPROVED'
        ).select_related('reviewer', 'responded_by').prefetch_related('images')
        
        # Apply Filters
        rating = self.request.GET.get('rating')
        if rating:
            reviews = reviews.filter(rating__gte=int(rating))
            
        guest_type = self.request.GET.get('guest_type')
        if guest_type:
            reviews = reviews.filter(guest_type=guest_type)
            
        theme = self.request.GET.get('theme')
        if theme:
            # SQLite JSON field contains is not supported, filter in python
            filtered_reviews = []
            for rev in reviews:
                has_theme = False
                if isinstance(rev.aspects_highlighted, list) and theme in rev.aspects_highlighted:
                    has_theme = True
                elif isinstance(rev.concerns, list) and theme in rev.concerns:
                    has_theme = True
                if has_theme:
                    filtered_reviews.append(rev.id)
            reviews = reviews.filter(id__in=filtered_reviews)
            
        # Apply Sorting
        sort = self.request.GET.get('sort', '-helpful_count')
        if sort in ['-helpful_count', '-created_at', '-rating', 'rating']:
            reviews = reviews.order_by(sort)
            
        context['reviews'] = reviews
        return context


class PropertyMapView(TemplateView):
    template_name = 'landing/property_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get properties with coordinates
        properties = Property.objects.filter(
            status='APPROVED',
            is_available=True
        ).prefetch_related('images', 'room_types__pricing_models', 'unit_types__pricing_models', 'amenities')
        
        # Serialize properties for JavaScript
        import json
        properties_data = []
        for prop in properties:
            # get price
            price = "Contact"
            if prop.property_type == 'HOSTEL':
                room_pricing = prop.room_types.first().pricing_models.first() if prop.room_types.first() else None
                if room_pricing:
                    price = f"GH₵ {room_pricing.semester_price or room_pricing.monthly_price}/sem"
            else:
                unit_pricing = prop.unit_types.first().pricing_models.first() if prop.unit_types.first() else None
                if unit_pricing:
                    price = f"GH₵ {unit_pricing.monthly_price or unit_pricing.yearly_price}/mo"
                    
            # get image
            if prop.images.first():
                img_field = prop.images.first().image
                img_url = str(img_field) if str(img_field).startswith('http') else img_field.url
            else:
                img_url = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400&h=300&fit=crop"

            property_dict = {
                'id': prop.id,
                'title': prop.title,
                'address': prop.address,
                'city': prop.city,
                'region': prop.region,
                'latitude': float(prop.latitude) if prop.latitude is not None else 5.6037,
                'longitude': float(prop.longitude) if prop.longitude is not None else -0.1870,
                'property_type': prop.property_type,
                'price': price,
                'image': img_url,
                'room_types': [
                    {
                        'available_slots': rt.available_slots
                    } for rt in prop.room_types.all()
                ],
                'unit_types': [
                    {
                        'available_units': ut.available_units
                    } for ut in prop.unit_types.all()
                ]
            }
            properties_data.append(property_dict)
        
        context['properties'] = properties
        context['properties_json'] = json.dumps(properties_data)
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
        context['MAP_DEFAULT_CENTER'] = settings.MAP_DEFAULT_CENTER
        context['MAP_DEFAULT_ZOOM'] = settings.MAP_DEFAULT_ZOOM
        
        # Filter options
        context['property_types'] = Property.PROPERTY_TYPE_CHOICES
        context['cities'] = Property.objects.filter(
            status='APPROVED', is_available=True
        ).values_list('city', flat=True).order_by('city').distinct()
        
        return context
