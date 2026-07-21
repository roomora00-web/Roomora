from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from properties.models import (
    Property, PropertyAmenity, Amenity, RoomType, RoomTypePricing,
    UnitType, UnitTypePricing, Room, PropertyImage, ProximityDestination
)
from accounts.models import User
from feedback.models import Review
import random


class Command(BaseCommand):
    help = 'Populate the database with 48 properties (3 per Ghana region) with authentic Ghanaian data'

    def handle(self, *args, **options):
        self.stdout.write('Starting Ghana property population...')
        
        admin_user = User.objects.filter(user_type='ADMIN').first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email='admin@staymatch.com',
                password='admin123',
                first_name='Kwame',
                last_name='Mensa',
                user_type='ADMIN'
            )
        
        self.stdout.write('Clearing existing properties...')
        Property.objects.all().delete()
        self.create_amenities()
        properties_data = self.get_all_ghana_properties()
        
        with transaction.atomic():
            for prop_data in properties_data:
                self.create_property(prop_data, admin_user)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(properties_data)} properties'))

    def create_amenities(self):
        amenities = [
            ('24/7 Security', 'GENERAL', 'shield'),
            ('Free WiFi', 'INTERNET', 'wifi'),
            ('Shared Kitchen', 'KITCHEN', 'chef-hat'),
            ('Study Room', 'STUDY', 'book'),
            ('Laundry Service', 'LAUNDRY', 'tshirt'),
            ('Elevator', 'GENERAL', 'arrow-up-circle'),
            ('Parking', 'GENERAL', 'car'),
            ('Garden', 'OUTDOOR', 'flower'),
            ('Library', 'STUDY', 'library'),
            ('Generator Backup', 'UTILITIES', 'power'),
            ('Swimming Pool', 'OUTDOOR', 'droplet'),
            ('Gym', 'GENERAL', 'dumbbell'),
            ('Air Conditioning', 'UTILITIES', 'snowflake'),
            ('Water Heater', 'BATHROOM', 'thermometer'),
            ('Refrigerator', 'KITCHEN', 'box'),
            ('Television', 'GENERAL', 'tv'),
            ('Balcony', 'OUTDOOR', 'sun'),
            ('Private Bathroom', 'BATHROOM', 'bath'),
            ('Wardrobe', 'BEDROOM', 'hanger'),
            ('Study Desk', 'STUDY', 'desk'),
            ('Ceiling Fan', 'UTILITIES', 'fan'),
            ('CCTV', 'SAFETY', 'camera'),
            ('Fire Extinguisher', 'SAFETY', 'fire'),
            ('First Aid Kit', 'SAFETY', 'plus'),
            ('Mosquito Nets', 'SAFETY', 'shield'),
            ('Solar Power', 'UTILITIES', 'sun'),
            ('Water Storage', 'UTILITIES', 'droplet'),
        ]
        
        for name, category, icon in amenities:
            Amenity.objects.get_or_create(
                name=name,
                defaults={'category': category, 'icon': icon}
            )
        
        self.stdout.write('Created amenities')

    def create_property(self, prop_data, admin_user):
        property_code = prop_data['property_code']
        if Property.objects.filter(property_code=property_code).exists():
            self.stdout.write(f'Property already exists: {prop_data["title"]} ({property_code})')
            return
        
        property_obj = Property.objects.create(
            uploaded_by=admin_user,
            property_code=prop_data['property_code'],
            property_type=prop_data['property_type'],
            property_category=prop_data['property_category'],
            title=prop_data['title'],
            description=prop_data['description'],
            address=prop_data['address'],
            city=prop_data['city'],
            region=prop_data['region'],
            country='Ghana',
            postal_code=prop_data.get('postal_code', ''),
            digital_address=prop_data.get('digital_address', ''),
            latitude=prop_data.get('latitude'),
            longitude=prop_data.get('longitude'),
            nearest_institution=prop_data.get('nearest_institution', ''),
            distance_to_campus=prop_data.get('distance_to_campus'),
            walking_time_estimate=prop_data.get('walking_time_estimate'),
            nearby_landmarks=prop_data.get('nearby_landmarks', ''),
            suitable_for_students=prop_data.get('suitable_for_students', True),
            suitable_for_workers=prop_data.get('suitable_for_workers', True),
            suitable_for_families=prop_data.get('suitable_for_families', False),
            suitable_for_couples=prop_data.get('suitable_for_couples', False),
            suitable_for_single_professionals=prop_data.get('suitable_for_single_professionals', False),
            suitable_for_national_service=prop_data.get('suitable_for_national_service', False),
            suitable_for_expatriates=prop_data.get('suitable_for_expatriates', False),
            suitable_for_short_stay=prop_data.get('suitable_for_short_stay', False),
            hostel_type=prop_data.get('hostel_type', ''),
            ownership_type=prop_data.get('ownership_type', ''),
            total_area=prop_data['total_area'],
            floor_number=prop_data.get('floor_number'),
            total_floors=prop_data.get('total_floors'),
            is_available=True,
            house_rules=prop_data.get('house_rules', ''),
            prohibited_items=prop_data.get('prohibited_items', ''),
            cancellation_policy=prop_data.get('cancellation_policy', ''),
            smoking_allowed=prop_data.get('smoking_allowed', False),
            pets_allowed=prop_data.get('pets_allowed', False),
            guests_allowed=prop_data.get('guests_allowed', True),
            maximum_guests=prop_data.get('maximum_guests', 1),
            curfew_time=prop_data.get('curfew_time'),
            visitor_policy=prop_data.get('visitor_policy', ''),
            is_verified=True,
            safety_score=prop_data.get('safety_score', 8),
            fire_safety_compliance=prop_data.get('fire_safety_compliance', True),
            is_featured=prop_data.get('is_featured', False),
            status='APPROVED',
            security_personnel=prop_data.get('security_personnel', True),
            cctv=prop_data.get('cctv', True),
            gated_community=prop_data.get('gated_community', True),
            emergency_contacts=prop_data.get('emergency_contacts', ''),
            water_availability=prop_data.get('water_availability', '24/7'),
            electricity_stability=prop_data.get('electricity_stability', 'Stable'),
            internet_availability=prop_data.get('internet_availability', 'High-speed'),
            utility_billing_method=prop_data.get('utility_billing_method', 'INCLUDED_IN_RENT')
        )
        
        for amenity_name in prop_data.get('amenities', []):
            try:
                amenity = Amenity.objects.get(name=amenity_name)
                PropertyAmenity.objects.get_or_create(
                    accommodation_property=property_obj,
                    amenity=amenity,
                    defaults={'is_included': True}
                )
            except Amenity.DoesNotExist:
                continue
        
        if property_obj.property_type in ['HOSTEL', 'STUDENT_APARTMENT']:
            self.create_room_types(property_obj, prop_data)
        else:
            self.create_unit_types(property_obj, prop_data)
        
        self.create_proximity_destinations(property_obj, prop_data)
        
        # Add property images (placeholder - user should replace with real images)
        self.create_property_images(property_obj, prop_data)
        
        # Add 5-star reviews for premium properties
        if prop_data.get('is_premium', False):
            self.create_premium_reviews(property_obj, admin_user)
        
        self.stdout.write(f'Created property: {property_obj.title} - {property_obj.region}')

    def create_room_types(self, property_obj, prop_data):
        for room_type_data in prop_data.get('room_types', []):
            room_type = RoomType.objects.create(
                accommodation_property=property_obj,
                room_type_name=room_type_data['name'],
                billing_model=room_type_data['billing_model'],
                occupancy_type=room_type_data['occupancy_type'],
                total_rooms=room_type_data['total_rooms'],
                beds_per_room=room_type_data['beds_per_room'],
                total_capacity=room_type_data['total_capacity'],
                available_slots=room_type_data['total_capacity'],
                occupied_slots=0,
                waiting_list_enabled=room_type_data.get('waiting_list_enabled', False),
                bed_type=room_type_data.get('bed_type', 'SINGLE'),
                study_desk_available=room_type_data.get('study_desk_available', True),
                wardrobe_available=room_type_data.get('wardrobe_available', True),
                air_conditioning=room_type_data.get('air_conditioning', False),
                fan=room_type_data.get('fan', True),
                wifi_available=room_type_data.get('wifi_available', True),
                private_bathroom=room_type_data.get('private_bathroom', False),
                shared_bathroom_ratio=room_type_data.get('shared_bathroom_ratio', ''),
                balcony=room_type_data.get('balcony', False),
                electricity_backup=room_type_data.get('electricity_backup', False),
                gender_restriction=room_type_data.get('gender_restriction', 'ANY'),
                preferred_lifestyle=room_type_data.get('preferred_lifestyle', 'BALANCED'),
                study_environment_rating=room_type_data.get('study_environment_rating', 4)
            )
            
            for pricing_data in room_type_data.get('pricing', []):
                RoomTypePricing.objects.create(
                    room_type=room_type,
                    payment_type=pricing_data['payment_type'],
                    monthly_price=pricing_data.get('monthly_price'),
                    semester_price=pricing_data.get('semester_price'),
                    yearly_price=pricing_data.get('yearly_price'),
                    daily_price=pricing_data.get('daily_price'),
                    weekly_price=pricing_data.get('weekly_price'),
                    academic_year_price=pricing_data.get('academic_year_price'),
                    two_years_price=pricing_data.get('two_years_price'),
                    max_semesters=pricing_data.get('max_semesters', 3),
                    min_months=pricing_data.get('min_months', 1),
                    max_months=pricing_data.get('max_months', 12),
                    allow_two_year_advance=pricing_data.get('allow_two_year_advance', False),
                    early_checkout_allowed=pricing_data.get('early_checkout_allowed', True),
                    early_checkout_penalty=pricing_data.get('early_checkout_penalty'),
                    grace_period_days=pricing_data.get('grace_period_days', 7),
                    overstay_multiplier=pricing_data.get('overstay_multiplier', Decimal('1.5')),
                    allow_monthly_extensions=pricing_data.get('allow_monthly_extensions', False),
                    monthly_extension_rate=pricing_data.get('monthly_extension_rate'),
                    security_deposit=pricing_data.get('security_deposit'),
                    maintenance_fee=pricing_data.get('maintenance_fee'),
                    registration_fee=pricing_data.get('registration_fee'),
                    utility_fee=pricing_data.get('utility_fee'),
                    currency='GHS'
                )
            
            self.create_physical_rooms(property_obj, room_type, room_type_data)

    def create_unit_types(self, property_obj, prop_data):
        for unit_type_data in prop_data.get('unit_types', []):
            unit_type = UnitType.objects.create(
                accommodation_property=property_obj,
                unit_name=unit_type_data['name'],
                billing_model=unit_type_data['billing_model'],
                number_of_units=unit_type_data['number_of_units'],
                bedrooms=unit_type_data['bedrooms'],
                bathrooms=unit_type_data['bathrooms'],
                kitchen=unit_type_data['kitchen'],
                balcony=unit_type_data.get('balcony', False),
                total_units=unit_type_data['number_of_units'],
                occupied_units=0,
                available_units=unit_type_data['number_of_units'],
                furnished_status=unit_type_data.get('furnished_status', 'UNFURNISHED'),
                air_conditioning=unit_type_data.get('air_conditioning', False),
                fan=unit_type_data.get('fan', True),
                water_heater=unit_type_data.get('water_heater', False),
                refrigerator=unit_type_data.get('refrigerator', False),
                washing_machine=unit_type_data.get('washing_machine', False),
                television=unit_type_data.get('television', False),
                generator=unit_type_data.get('generator', False),
                internet=unit_type_data.get('internet', True),
                shared_apartment_allowed=unit_type_data.get('shared_apartment_allowed', False),
                roommate_matching_enabled=unit_type_data.get('roommate_matching_enabled', False)
            )
            
            for pricing_data in unit_type_data.get('pricing', []):
                UnitTypePricing.objects.create(
                    unit_type=unit_type,
                    payment_type=pricing_data['payment_type'],
                    monthly_price=pricing_data.get('monthly_price'),
                    semester_price=pricing_data.get('semester_price'),
                    yearly_price=pricing_data.get('yearly_price'),
                    two_years_price=pricing_data.get('two_years_price'),
                    three_years_price=pricing_data.get('three_years_price'),
                    daily_price=pricing_data.get('daily_price'),
                    weekly_price=pricing_data.get('weekly_price'),
                    academic_year_price=pricing_data.get('academic_year_price'),
                    max_semesters=pricing_data.get('max_semesters', 3),
                    min_months=pricing_data.get('min_months', 1),
                    max_months=pricing_data.get('max_months', 12),
                    allow_two_year_advance=pricing_data.get('allow_two_year_advance', False),
                    early_checkout_allowed=pricing_data.get('early_checkout_allowed', True),
                    early_checkout_penalty=pricing_data.get('early_checkout_penalty'),
                    grace_period_days=pricing_data.get('grace_period_days', 7),
                    overstay_multiplier=pricing_data.get('overstay_multiplier', Decimal('1.5')),
                    allow_monthly_extensions=pricing_data.get('allow_monthly_extensions', False),
                    monthly_extension_rate=pricing_data.get('monthly_extension_rate'),
                    security_deposit=pricing_data.get('security_deposit'),
                    maintenance_fee=pricing_data.get('maintenance_fee'),
                    registration_fee=pricing_data.get('registration_fee'),
                    utility_fee=pricing_data.get('utility_fee'),
                    currency='GHS'
                )

    def create_physical_rooms(self, property_obj, room_type, room_type_data):
        total_rooms = room_type_data['total_rooms']
        floor_count = property_obj.total_floors or 1
        rooms_per_floor = total_rooms // floor_count
        
        existing_numbers = set(Room.objects.filter(
            accommodation_property=property_obj
        ).values_list('room_number', flat=True))
        
        room_counter = 1
        for floor in range(1, floor_count + 1):
            for room_num in range(1, rooms_per_floor + 1):
                while True:
                    room_number = f"{floor}{room_num:02d}"
                    if room_number not in existing_numbers:
                        break
                    room_num += 1
                
                Room.objects.create(
                    accommodation_property=property_obj,
                    room_type=room_type,
                    room_number=room_number,
                    floor=str(floor),
                    total_slots=room_type.beds_per_room,
                    occupied_slots=0,
                    pending_slots=0,
                    status='AVAILABLE'
                )
                existing_numbers.add(room_number)

    def create_proximity_destinations(self, property_obj, prop_data):
        for dest_data in prop_data.get('proximity_destinations', []):
            ProximityDestination.objects.create(
                accommodation_property=property_obj,
                destination_name=dest_data['name'],
                destination_type=dest_data['type'],
                distance_km=dest_data.get('distance_km'),
                travel_time_minutes=dest_data.get('travel_time_minutes'),
                travel_mode=dest_data.get('travel_mode', 'WALK'),
                notes=dest_data.get('notes', ''),
                order=dest_data.get('order', 0)
            )

    def create_property_images(self, property_obj, prop_data):
        # Create unique images for each property using Unsplash source URLs
        image_types = ['EXTERIOR', 'INTERIOR', 'ROOM', 'KITCHEN', 'BATHROOM', 'AMENITY']
        
        # Generate unique keywords based on property type and region
        keywords = self.get_image_keywords(property_obj, prop_data)
        
        for i, image_type in enumerate(image_types[:4]):  # At least 4 images
            keyword = keywords[i % len(keywords)]
            # Use unique identifier to ensure different images
            unique_id = f"{property_obj.property_code}_{i}"
            
            # Use picsum.photos for reliable placeholder images
            image_url = f"https://picsum.photos/seed/{unique_id}/800/600"
            
            PropertyImage.objects.create(
                accommodation_property=property_obj,
                image=image_url,  # Using URL instead of local file
                image_type=image_type,
                caption=f'{image_type} view of {property_obj.title} - {keyword}',
                is_primary=(i == 0),
                order=i
            )

    def get_image_keywords(self, property_obj, prop_data):
        """Generate relevant image keywords based on property type and region"""
        property_type = property_obj.property_type.lower()
        region = property_obj.region.lower()
        
        # Base keywords by property type
        type_keywords = {
            'hostel': ['ghana-hostel', 'student-dormitory', 'shared-room', 'bunk-bed'],
            'apartment': ['ghana-apartment', 'modern-apartment', 'luxury-apartment', 'city-apartment'],
            'student_apartment': ['student-housing', 'student-apartment', 'campus-housing', 'dorm-room'],
            'flat': ['ghana-flat', 'apartment-flat', 'residential-flat'],
            'compound_house': ['ghana-compound-house', 'african-house', 'family-home'],
            'townhouse': ['ghana-townhouse', 'modern-townhouse'],
            'duplex': ['ghana-duplex', 'luxury-duplex'],
            'villa': ['ghana-villa', 'luxury-villa', 'estate-home'],
            'studio': ['studio-apartment', 'small-apartment', 'compact-living'],
        }
        
        # Region-specific keywords
        region_keywords = {
            'ashanti': ['kumasi', 'ashanti-region', 'ghana-city'],
            'brong-ahafo': ['sunyani', 'brong-ahafo', 'ghana-town'],
            'central': ['cape-coast', 'central-region', 'ghana-coast'],
            'eastern': ['koforidua', 'eastern-region', 'ghana-hills'],
            'greater accra': ['accra', 'ghana-capital', 'modern-africa'],
            'northern': ['tamale', 'northern-ghana', 'savanna'],
            'upper east': ['bolgatanga', 'upper-east-ghana'],
            'upper west': ['wa', 'upper-west-ghana'],
            'volta': ['ho', 'volta-region', 'ghana-lake'],
            'western': ['takoradi', 'western-ghana', 'ghana-harbour'],
            'ahafo': ['mim', 'ahafo-region'],
            'bono east': ['techiman', 'bono-east'],
            'north east': ['nalerigu', 'north-east-ghana'],
            'oti': ['dambai', 'oti-region'],
            'savannah': ['damongo', 'savannah-ghana'],
            'western north': ['sefwi-wiawso', 'western-north'],
        }
        
        # Get appropriate keywords
        type_list = type_keywords.get(property_type, ['ghana-housing', 'african-home'])
        region_list = region_keywords.get(region, ['ghana', 'africa'])
        
        # Combine and return unique keywords
        combined = type_list + region_list
        # Add some general housing keywords
        combined.extend(['building', 'architecture', 'real-estate'])
        
        return combined[:6]  # Return up to 6 unique keywords

    def create_premium_reviews(self, property_obj, admin_user):
        # Create 5-star reviews for premium properties
        ghanaian_names = [
            ('Kwame', 'Asante'), ('Ama', 'Mensa'), ('Kojo', 'Owusu'), 
            ('Abena', 'Ofori'), ('Kofi', 'Ansah'), ('Yaa', 'Boateng'),
            ('Kwesi', 'Prempeh'), ('Akosua', 'Mills')
        ]
        
        for first_name, last_name in random.sample(ghanaian_names, 3):
            reviewer, created = User.objects.get_or_create(
                email=f'{first_name.lower()}.{last_name.lower()}@example.com',
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': 'STUDENT'
                }
            )
            
            Review.objects.create(
                reviewer=reviewer,
                accommodation_property=property_obj,
                review_type='PROPERTY',
                status='APPROVED',
                rating=5,
                cleanliness_rating=5,
                location_rating=5,
                amenities_rating=5,
                communication_rating=5,
                value_rating=5,
                title=f'Excellent accommodation at {property_obj.title}',
                content=f'I had an amazing stay at {property_obj.title}. The facilities are top-notch and the staff are very helpful. Highly recommended for anyone looking for quality accommodation in {property_obj.city}.',
                guest_type='STUDENT',
                recommendation='DEFINITELY',
                would_stay_again='DEFINITELY',
                is_verified=True,
                verification_level='VERIFIED_GUEST',
                trust_score=95
            )

    def get_all_ghana_properties(self):
        """Generate exactly 20 properties"""
        all_properties = []
        
        all_properties.extend(self.generate_greater_accra_properties()[:3])
        all_properties.extend(self.generate_ashanti_properties()[:2])
        all_properties.extend(self.generate_central_properties()[:2])
        
        # 1 each for the other 13 regions
        all_properties.extend(self.generate_brong_ahafo_properties()[:1])
        all_properties.extend(self.generate_eastern_properties()[:1])
        all_properties.extend(self.generate_northern_properties()[:1])
        all_properties.extend(self.generate_upper_east_properties()[:1])
        all_properties.extend(self.generate_upper_west_properties()[:1])
        all_properties.extend(self.generate_volta_properties()[:1])
        all_properties.extend(self.generate_western_properties()[:1])
        all_properties.extend(self.generate_ahafo_properties()[:1])
        all_properties.extend(self.generate_bono_east_properties()[:1])
        all_properties.extend(self.generate_north_east_properties()[:1])
        all_properties.extend(self.generate_oti_properties()[:1])
        all_properties.extend(self.generate_savannah_properties()[:1])
        all_properties.extend(self.generate_western_north_properties()[:1])
        
        return all_properties

    def generate_ashanti_properties(self):
        base = {
            'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room', 'Generator Backup'],
            'ownership_type': 'PRIVATE',
            'property_category': 'STUDENT_HOUSING',
            'description': 'Modern accommodation in the heart of Kumasi with excellent facilities for students and professionals.'
        }
        
        return [
            {**base, 'property_code': 'ASH-001', 'property_type': 'HOSTEL', 'title': 'Adom Hall Hostel', 'address': 'Adom Road, Kumasi', 'latitude': Decimal('6.6885'), 'longitude': Decimal('-1.6244'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('2.5'), 'walking_time_estimate': 20, 'hostel_type': 'MIXED', 'total_area': Decimal('3200.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Laundry Service', 'Elevator', 'Parking', 'Library'], 'room_types': [{'name': 'Premium Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 25, 'beds_per_room': 1, 'total_capacity': 25, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('4200.00'), 'security_deposit': Decimal('600.00')}]}], 'proximity_destinations': [{'name': 'KNUST Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('2.5'), 'travel_time_minutes': 20}], 'is_premium': True, 'is_featured': True, 'safety_score': 9},
            {**base, 'property_code': 'ASH-002', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Kejetia Executive Apartments', 'address': 'Kejetia Market Area, Kumasi', 'latitude': Decimal('6.6910'), 'longitude': Decimal('-1.6280'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2800.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool', 'Gym'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 10, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('3500.00'), 'security_deposit': Decimal('7000.00')}]}], 'proximity_destinations': [{'name': 'Kejetia Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'ASH-003', 'property_type': 'STUDENT_APARTMENT', 'title': 'Kumasi Student Village', 'address': 'KNUST Annex, Kumasi', 'latitude': Decimal('6.6743'), 'longitude': Decimal('-1.5715'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('0.8'), 'walking_time_estimate': 8, 'total_area': Decimal('1800.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 15, 'beds_per_room': 1, 'total_capacity': 15, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1200.00'), 'security_deposit': Decimal('1500.00')}]}], 'proximity_destinations': [{'name': 'KNUST Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.8'), 'travel_time_minutes': 8}]},
        ]

    def generate_brong_ahafo_properties(self):
        base = {
            'city': 'Sunyani', 'region': 'Brong-Ahafo', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen'],
            'ownership_type': 'PRIVATE',
            'property_category': 'STUDENT_HOUSING',
            'description': 'Affordable student accommodation in Sunyani with basic amenities.'
        }
        
        return [
            {**base, 'property_code': 'BA-001', 'property_type': 'HOSTEL', 'title': 'Sunyani Technical University Hostel', 'address': 'STU Campus, Sunyani', 'latitude': Decimal('7.3384'), 'longitude': Decimal('-2.3295'), 'nearest_institution': 'Sunyani Technical University', 'distance_to_campus': Decimal('0.5'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'total_area': Decimal('2200.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Study Room', 'Laundry Service'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 20, 'beds_per_room': 1, 'total_capacity': 20, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2800.00'), 'security_deposit': Decimal('400.00')}]}], 'proximity_destinations': [{'name': 'STU Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'BA-002', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Sunyani Residential Complex', 'address': 'Sunyani Township', 'latitude': Decimal('7.3400'), 'longitude': Decimal('-2.3300'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2500.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Generator Backup'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 3, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2800.00'), 'security_deposit': Decimal('5600.00')}]}], 'proximity_destinations': [{'name': 'Sunyani Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}]},
            {**base, 'property_code': 'BA-003', 'property_type': 'HOSTEL', 'title': 'Catholic University Hostel', 'address': 'CUC Campus, Sunyani', 'latitude': Decimal('7.3350'), 'longitude': Decimal('-2.3250'), 'nearest_institution': 'Catholic University of Ghana', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Library', 'Study Room'], 'room_types': [{'name': 'Double Sharing Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'DOUBLE', 'total_rooms': 15, 'beds_per_room': 2, 'total_capacity': 30, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2200.00'), 'security_deposit': Decimal('350.00')}]}], 'proximity_destinations': [{'name': 'CUC Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}], 'is_premium': True, 'is_featured': True, 'safety_score': 9},
        ]

    def generate_central_properties(self):
        base = {
            'city': 'Cape Coast', 'region': 'Central', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room'],
            'ownership_type': 'INSTITUTION_AFFILIATED',
            'property_category': 'STUDENT_HOUSING',
            'description': 'Quality student accommodation near UCC with modern amenities.'
        }
        
        return [
            {**base, 'property_code': 'CEN-001', 'property_type': 'HOSTEL', 'title': 'Atlantic Hall Annex', 'address': 'UCC Campus, Cape Coast', 'latitude': Decimal('5.1020'), 'longitude': Decimal('-1.2480'), 'nearest_institution': 'University of Cape Coast', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'BOYS_ONLY', 'total_area': Decimal('2500.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Laundry Service', 'Elevator', 'Library'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 20, 'beds_per_room': 1, 'total_capacity': 20, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3800.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'CEN-002', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Cape Coast Beach Apartments', 'address': 'Near Cape Coast Castle', 'latitude': Decimal('5.1050'), 'longitude': Decimal('-1.2500'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('3000.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool', 'Garden'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('4000.00'), 'security_deposit': Decimal('8000.00')}]}], 'proximity_destinations': [{'name': 'Cape Coast Castle', 'type': 'TOURIST', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}], 'is_premium': True, 'is_featured': True, 'safety_score': 10},
            {**base, 'property_code': 'CEN-003', 'property_type': 'STUDENT_APARTMENT', 'title': 'UCC Student Village', 'address': 'Near UCC Campus', 'latitude': Decimal('5.1030'), 'longitude': Decimal('-1.2490'), 'nearest_institution': 'University of Cape Coast', 'distance_to_campus': Decimal('0.8'), 'walking_time_estimate': 10, 'ownership_type': 'PRIVATE', 'total_area': Decimal('1400.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 10, 'beds_per_room': 1, 'total_capacity': 10, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1600.00'), 'security_deposit': Decimal('2000.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.8'), 'travel_time_minutes': 10}]},
        ]

    def generate_eastern_properties(self):
        base = {
            'city': 'Koforidua', 'region': 'Eastern', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Modern residential accommodation in Koforidua.'
        }
        
        return [
            {**base, 'property_code': 'EAS-001', 'property_type': 'APARTMENT', 'title': 'Koforidua Gardens Apartments', 'address': 'Koforidua Township', 'latitude': Decimal('6.0833'), 'longitude': Decimal('-0.2567'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2600.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Garden'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 12, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2200.00'), 'security_deposit': Decimal('4400.00')}]}], 'proximity_destinations': [{'name': 'Koforidua Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}]},
            {**base, 'property_code': 'EAS-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'All Nations University Hostel', 'address': 'ANUC Campus, Koforidua', 'latitude': Decimal('6.0800'), 'longitude': Decimal('-0.2600'), 'nearest_institution': 'All Nations University', 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room', 'Library'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 18, 'beds_per_room': 1, 'total_capacity': 18, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3200.00'), 'security_deposit': Decimal('450.00')}]}], 'proximity_destinations': [{'name': 'ANUC Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'EAS-003', 'property_type': 'APARTMENT', 'property_category': 'EXECUTIVE_HOUSING', 'title': 'Eastern Executive Suites', 'address': 'Koforidua', 'latitude': Decimal('6.0850'), 'longitude': Decimal('-0.2550'), 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('3200.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool', 'Gym', 'Generator Backup'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 3, 'bathrooms': 3, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('4500.00'), 'security_deposit': Decimal('9000.00')}]}], 'proximity_destinations': [{'name': 'Koforidua Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.8'), 'travel_time_minutes': 8}], 'is_premium': True, 'is_featured': True, 'safety_score': 9},
        ]

    def generate_greater_accra_properties(self):
        base = {
            'city': 'Accra', 'region': 'Greater Accra', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi', 'Generator Backup'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Premium residential accommodation in prime Accra locations.'
        }
        
        return [
            {**base, 'property_code': 'ACC-001', 'property_type': 'APARTMENT', 'title': 'Airport Residential Apartments', 'address': 'Airport Residential Area', 'latitude': Decimal('5.5600'), 'longitude': Decimal('-0.2050'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('3500.00'), 'total_floors': 6, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool', 'Gym', 'Garden'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 3, 'bathrooms': 3, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('5500.00'), 'security_deposit': Decimal('11000.00')}]}], 'proximity_destinations': [{'name': 'Kotoka Airport', 'type': 'TRANSPORT', 'distance_km': Decimal('2.0'), 'travel_time_minutes': 5}], 'is_premium': True, 'is_featured': True, 'safety_score': 10},
            {**base, 'property_code': 'ACC-002', 'property_type': 'APARTMENT', 'title': 'East Legon Executive Apartments', 'address': 'East Legon', 'latitude': Decimal('5.6300'), 'longitude': Decimal('-0.1500'), 'nearest_institution': 'University of Ghana', 'distance_to_campus': Decimal('5.0'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('3000.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 10, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('3800.00'), 'security_deposit': Decimal('7600.00')}]}], 'proximity_destinations': [{'name': 'University of Ghana', 'type': 'INSTITUTION', 'distance_km': Decimal('5.0'), 'travel_time_minutes': 15}]},
            {**base, 'property_code': 'ACC-003', 'property_type': 'STUDENT_APARTMENT', 'property_category': 'STUDENT_HOUSING', 'title': 'Legon Student Village', 'address': 'Legon', 'latitude': Decimal('5.6500'), 'longitude': Decimal('-0.1800'), 'nearest_institution': 'University of Ghana', 'distance_to_campus': Decimal('1.5'), 'walking_time_estimate': 15, 'total_area': Decimal('2000.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Parking', 'Study Room'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 15, 'beds_per_room': 1, 'total_capacity': 15, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1500.00'), 'security_deposit': Decimal('1800.00')}]}], 'proximity_destinations': [{'name': 'University of Ghana', 'type': 'INSTITUTION', 'distance_km': Decimal('1.5'), 'travel_time_minutes': 15}]},
        ]

    def generate_northern_properties(self):
        base = {
            'city': 'Tamale', 'region': 'Northern', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi', 'Generator Backup'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Modern accommodation in Tamale with essential amenities.'
        }
        
        return [
            {**base, 'property_code': 'NOR-001', 'property_type': 'APARTMENT', 'title': 'Tamale City Apartments', 'address': 'Tamale Township', 'latitude': Decimal('9.4000'), 'longitude': Decimal('-0.8373'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2400.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2000.00'), 'security_deposit': Decimal('4000.00')}]}], 'proximity_destinations': [{'name': 'Tamale Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}]},
            {**base, 'property_code': 'NOR-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'UDS Hostel Tamale', 'address': 'UDS Campus, Tamale', 'latitude': Decimal('9.4050'), 'longitude': Decimal('-0.8400'), 'nearest_institution': 'University for Development Studies', 'distance_to_campus': Decimal('0.5'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2200.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 18, 'beds_per_room': 1, 'total_capacity': 18, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2500.00'), 'security_deposit': Decimal('400.00')}]}], 'proximity_destinations': [{'name': 'UDS Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'NOR-003', 'property_type': 'APARTMENT', 'property_category': 'EXECUTIVE_HOUSING', 'title': 'Northern Executive Suites', 'address': 'Tamale', 'latitude': Decimal('9.4100'), 'longitude': Decimal('-0.8350'), 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('2800.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Generator Backup', 'Solar Power'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 5, 'bedrooms': 3, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('3500.00'), 'security_deposit': Decimal('7000.00')}]}], 'proximity_destinations': [{'name': 'Tamale Airport', 'type': 'TRANSPORT', 'distance_km': Decimal('3.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 8},
        ]

    def generate_upper_east_properties(self):
        base = {
            'city': 'Bolgatanga', 'region': 'Upper East', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Affordable accommodation in Bolgatanga.'
        }
        
        return [
            {**base, 'property_code': 'UE-001', 'property_type': 'APARTMENT', 'title': 'Bolga Residential Apartments', 'address': 'Bolgatanga Township', 'latitude': Decimal('10.7833'), 'longitude': Decimal('-0.8500'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1200.00'), 'security_deposit': Decimal('2400.00')}]}], 'proximity_destinations': [{'name': 'Bolga Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'UE-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Bolgatanga Polytechnic Hostel', 'address': 'Bolgatanga Polytechnic Campus', 'latitude': Decimal('10.7800'), 'longitude': Decimal('-0.8550'), 'nearest_institution': 'Bolgatanga Technical University', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1800.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 15, 'beds_per_room': 1, 'total_capacity': 15, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2000.00'), 'security_deposit': Decimal('300.00')}]}], 'proximity_destinations': [{'name': 'BTU Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'UE-003', 'property_type': 'APARTMENT', 'title': 'Upper East Executive Apartments', 'address': 'Bolgatanga', 'latitude': Decimal('10.7850'), 'longitude': Decimal('-0.8450'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2200.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Generator Backup', 'Solar Power'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 5, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2500.00'), 'security_deposit': Decimal('5000.00')}]}], 'proximity_destinations': [{'name': 'Bolga Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 8},
        ]

    def generate_upper_west_properties(self):
        base = {
            'city': 'Wa', 'region': 'Upper West', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Basic accommodation in Wa with essential amenities.'
        }
        
        return [
            {**base, 'property_code': 'UW-001', 'property_type': 'APARTMENT', 'title': 'Wa City Apartments', 'address': 'Wa Township', 'latitude': Decimal('10.0667'), 'longitude': Decimal('-2.3000'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1800.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1000.00'), 'security_deposit': Decimal('2000.00')}]}], 'proximity_destinations': [{'name': 'Wa Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'UW-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Wa Polytechnic Hostel', 'address': 'Wa Polytechnic Campus', 'latitude': Decimal('10.0700'), 'longitude': Decimal('-2.3050'), 'nearest_institution': 'Wa Technical University', 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1600.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('1800.00'), 'security_deposit': Decimal('300.00')}]}], 'proximity_destinations': [{'name': 'WTU Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
            {**base, 'property_code': 'UW-003', 'property_type': 'APARTMENT', 'title': 'Upper West Executive Suites', 'address': 'Wa', 'latitude': Decimal('10.0750'), 'longitude': Decimal('-2.2950'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Generator Backup', 'Solar Power'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 4, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2200.00'), 'security_deposit': Decimal('4400.00')}]}], 'proximity_destinations': [{'name': 'Wa Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 8},
        ]

    def generate_volta_properties(self):
        base = {
            'city': 'Ho', 'region': 'Volta', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Modern accommodation in Ho with good amenities.'
        }
        
        return [
            {**base, 'property_code': 'VOL-001', 'property_type': 'APARTMENT', 'title': 'Ho City Apartments', 'address': 'Ho Township', 'latitude': Decimal('6.6000'), 'longitude': Decimal('0.4667'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2200.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1800.00'), 'security_deposit': Decimal('3600.00')}]}], 'proximity_destinations': [{'name': 'Ho Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'VOL-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Ho Technical University Hostel', 'address': 'HTU Campus, Ho', 'latitude': Decimal('6.6050'), 'longitude': Decimal('0.4700'), 'nearest_institution': 'Ho Technical University', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room', 'Library'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 18, 'beds_per_room': 1, 'total_capacity': 18, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2800.00'), 'security_deposit': Decimal('400.00')}]}], 'proximity_destinations': [{'name': 'HTU Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'VOL-003', 'property_type': 'APARTMENT', 'property_category': 'EXECUTIVE_HOUSING', 'title': 'Volta Executive Suites', 'address': 'Ho', 'latitude': Decimal('6.6100'), 'longitude': Decimal('0.4600'), 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('2800.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool', 'Generator Backup'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 3, 'bathrooms': 3, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('3800.00'), 'security_deposit': Decimal('7600.00')}]}], 'proximity_destinations': [{'name': 'Ho Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.8'), 'travel_time_minutes': 8}], 'is_premium': True, 'is_featured': True, 'safety_score': 9},
        ]

    def generate_western_properties(self):
        base = {
            'city': 'Takoradi', 'region': 'Western', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Quality accommodation in Takoradi near the harbour.'
        }
        
        return [
            {**base, 'property_code': 'WES-001', 'property_type': 'APARTMENT', 'title': 'Takoradi Harbour Apartments', 'address': 'Near Takoradi Harbour', 'latitude': Decimal('4.8750'), 'longitude': Decimal('-1.7450'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2500.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2500.00'), 'security_deposit': Decimal('5000.00')}]}], 'proximity_destinations': [{'name': 'Takoradi Harbour', 'type': 'TRANSPORT', 'distance_km': Decimal('1.5'), 'travel_time_minutes': 15}]},
            {**base, 'property_code': 'WES-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Takoradi Technical University Hostel', 'address': 'TTU Campus, Takoradi', 'latitude': Decimal('4.8800'), 'longitude': Decimal('-1.7500'), 'nearest_institution': 'Takoradi Technical University', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2200.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room', 'Laundry Service'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 20, 'beds_per_room': 1, 'total_capacity': 20, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3000.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'TTU Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'WES-003', 'property_type': 'APARTMENT', 'property_category': 'EXECUTIVE_HOUSING', 'title': 'Western Executive Suites', 'address': 'Takoradi', 'latitude': Decimal('4.8850'), 'longitude': Decimal('-1.7400'), 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('3000.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Swimming Pool', 'Gym', 'Generator Backup'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 3, 'bathrooms': 3, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('4500.00'), 'security_deposit': Decimal('9000.00')}]}], 'proximity_destinations': [{'name': 'Takoradi Harbour', 'type': 'TRANSPORT', 'distance_km': Decimal('2.0'), 'travel_time_minutes': 20}], 'is_premium': True, 'is_featured': True, 'safety_score': 9},
        ]

    def generate_ahafo_properties(self):
        base = {
            'city': 'Mim', 'region': 'Ahafo', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Affordable accommodation in Mim with basic amenities.'
        }
        
        return [
            {**base, 'property_code': 'AH-001', 'property_type': 'APARTMENT', 'title': 'Mim Residential Apartments', 'address': 'Mim Township', 'latitude': Decimal('7.0500'), 'longitude': Decimal('-2.3500'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1800.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('900.00'), 'security_deposit': Decimal('1800.00')}]}], 'proximity_destinations': [{'name': 'Mim Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'AH-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Ahafo Technical Institute Hostel', 'address': 'Mim', 'latitude': Decimal('7.0550'), 'longitude': Decimal('-2.3550'), 'nearest_institution': 'Ahafo Technical Institute', 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1600.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('1800.00'), 'security_deposit': Decimal('300.00')}]}], 'proximity_destinations': [{'name': 'ATI Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
            {**base, 'property_code': 'AH-003', 'property_type': 'APARTMENT', 'title': 'Ahafo Executive Apartments', 'address': 'Mim', 'latitude': Decimal('7.0600'), 'longitude': Decimal('-2.3450'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 4, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2000.00'), 'security_deposit': Decimal('4000.00')}]}], 'proximity_destinations': [{'name': 'Mim Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 8},
        ]

    def generate_bono_east_properties(self):
        base = {
            'city': 'Techiman', 'region': 'Bono East', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Modern accommodation in Techiman with essential amenities.'
        }
        
        return [
            {**base, 'property_code': 'BE-001', 'property_type': 'APARTMENT', 'title': 'Techiman City Apartments', 'address': 'Techiman Township', 'latitude': Decimal('7.5833'), 'longitude': Decimal('-1.9333'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1100.00'), 'security_deposit': Decimal('2200.00')}]}], 'proximity_destinations': [{'name': 'Techiman Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'BE-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Techiman Campus Hostel', 'address': 'Techiman', 'latitude': Decimal('7.5800'), 'longitude': Decimal('-1.9300'), 'nearest_institution': 'Techiman Campus of UENR', 'distance_to_campus': Decimal('0.5'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1800.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 15, 'beds_per_room': 1, 'total_capacity': 15, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2200.00'), 'security_deposit': Decimal('350.00')}]}], 'proximity_destinations': [{'name': 'UENR Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'BE-003', 'property_type': 'APARTMENT', 'title': 'Bono East Executive Suites', 'address': 'Techiman', 'latitude': Decimal('7.5850'), 'longitude': Decimal('-1.9250'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2200.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 5, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2300.00'), 'security_deposit': Decimal('4600.00')}]}], 'proximity_destinations': [{'name': 'Techiman Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 8},
        ]

    def generate_north_east_properties(self):
        base = {
            'city': 'Nalerigu', 'region': 'North East', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Basic accommodation in Nalerigu with essential amenities.'
        }
        
        return [
            {**base, 'property_code': 'NE-001', 'property_type': 'APARTMENT', 'title': 'Nalerigu Residential Apartments', 'address': 'Nalerigu Township', 'latitude': Decimal('10.4167'), 'longitude': Decimal('-0.4167'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1600.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 5, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('800.00'), 'security_deposit': Decimal('1600.00')}]}], 'proximity_destinations': [{'name': 'Nalerigu Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'NE-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Nalerigu Campus Hostel', 'address': 'Nalerigu', 'latitude': Decimal('10.4200'), 'longitude': Decimal('-0.4200'), 'nearest_institution': 'Nalerigu Campus', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1400.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 10, 'beds_per_room': 1, 'total_capacity': 10, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('1600.00'), 'security_deposit': Decimal('250.00')}]}], 'proximity_destinations': [{'name': 'Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'NE-003', 'property_type': 'APARTMENT', 'title': 'North East Executive Apartments', 'address': 'Nalerigu', 'latitude': Decimal('10.4250'), 'longitude': Decimal('-0.4150'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1800.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Generator Backup', 'Solar Power'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 3, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1800.00'), 'security_deposit': Decimal('3600.00')}]}], 'proximity_destinations': [{'name': 'Nalerigu Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 7},
        ]

    def generate_oti_properties(self):
        base = {
            'city': 'Dambai', 'region': 'Oti', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Affordable accommodation in Dambai with basic amenities.'
        }
        
        return [
            {**base, 'property_code': 'OTI-001', 'property_type': 'APARTMENT', 'title': 'Dambai Residential Apartments', 'address': 'Dambai Township', 'latitude': Decimal('8.0667'), 'longitude': Decimal('0.1667'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1700.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('850.00'), 'security_deposit': Decimal('1700.00')}]}], 'proximity_destinations': [{'name': 'Dambai Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'OTI-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Dambai Campus Hostel', 'address': 'Dambai', 'latitude': Decimal('8.0700'), 'longitude': Decimal('0.1700'), 'nearest_institution': 'Dambai Campus', 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1500.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('1700.00'), 'security_deposit': Decimal('300.00')}]}], 'proximity_destinations': [{'name': 'Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
            {**base, 'property_code': 'OTI-003', 'property_type': 'APARTMENT', 'title': 'Oti Executive Suites', 'address': 'Dambai', 'latitude': Decimal('8.0750'), 'longitude': Decimal('0.1650'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1900.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 4, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1900.00'), 'security_deposit': Decimal('3800.00')}]}], 'proximity_destinations': [{'name': 'Dambai Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 7},
        ]

    def generate_savannah_properties(self):
        base = {
            'city': 'Damongo', 'region': 'Savannah', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Basic accommodation in Damongo with essential amenities.'
        }
        
        return [
            {**base, 'property_code': 'SAV-001', 'property_type': 'APARTMENT', 'title': 'Damongo Residential Apartments', 'address': 'Damongo Township', 'latitude': Decimal('9.0667'), 'longitude': Decimal('-1.8000'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1600.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 5, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('750.00'), 'security_deposit': Decimal('1500.00')}]}], 'proximity_destinations': [{'name': 'Damongo Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'SAV-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Damongo Campus Hostel', 'address': 'Damongo', 'latitude': Decimal('9.0700'), 'longitude': Decimal('-1.8050'), 'nearest_institution': 'Damongo Campus', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1400.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 10, 'beds_per_room': 1, 'total_capacity': 10, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('1500.00'), 'security_deposit': Decimal('250.00')}]}], 'proximity_destinations': [{'name': 'Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'SAV-003', 'property_type': 'APARTMENT', 'title': 'Savannah Executive Apartments', 'address': 'Damongo', 'latitude': Decimal('9.0750'), 'longitude': Decimal('-1.7950'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1800.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Generator Backup', 'Solar Power'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 3, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1700.00'), 'security_deposit': Decimal('3400.00')}]}], 'proximity_destinations': [{'name': 'Damongo Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 7},
        ]

    def generate_western_north_properties(self):
        base = {
            'city': 'Sefwi Wiawso', 'region': 'Western North', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'property_category': 'RESIDENTIAL',
            'description': 'Affordable accommodation in Sefwi Wiawso with basic amenities.'
        }
        
        return [
            {**base, 'property_code': 'WN-001', 'property_type': 'APARTMENT', 'title': 'Sefwi Wiawso Apartments', 'address': 'Sefwi Wiawso Township', 'latitude': Decimal('6.1667'), 'longitude': Decimal('-2.4167'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1700.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Water Storage'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('900.00'), 'security_deposit': Decimal('1800.00')}]}], 'proximity_destinations': [{'name': 'Sefwi Wiawso Market', 'type': 'SHOPPING', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'WN-002', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Sefwi Wiawso Campus Hostel', 'address': 'Sefwi Wiawso', 'latitude': Decimal('6.1700'), 'longitude': Decimal('-2.4200'), 'nearest_institution': 'Sefwi Wiawso Campus', 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1500.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('1800.00'), 'security_deposit': Decimal('300.00')}]}], 'proximity_destinations': [{'name': 'Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
            {**base, 'property_code': 'WN-003', 'property_type': 'APARTMENT', 'title': 'Western North Executive Suites', 'address': 'Sefwi Wiawso', 'latitude': Decimal('6.1750'), 'longitude': Decimal('-2.4100'), 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('1900.00'), 'total_floors': 2, 'amenities': base['amenities'] + ['Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 4, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2000.00'), 'security_deposit': Decimal('4000.00')}]}], 'proximity_destinations': [{'name': 'Sefwi Wiawso Market', 'type': 'SHOPPING', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}], 'is_premium': True, 'is_featured': True, 'safety_score': 7},
        ]
