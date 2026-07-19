from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from properties.models import (
    Property, PropertyAmenity, Amenity, RoomType, RoomTypePricing,
    UnitType, UnitTypePricing, Room, ProximityDestination
)
from accounts.models import User


class Command(BaseCommand):
    help = 'Populate the database with 30 properties with full information'

    def handle(self, *args, **options):
        self.stdout.write('Starting property population...')
        
        admin_user = User.objects.filter(user_type='ADMIN').first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email='admin@staymatch.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                user_type='ADMIN'
            )
        
        self.create_amenities()
        properties_data = self.get_properties_data()
        
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
        ]
        
        for name, category, icon in amenities:
            Amenity.objects.get_or_create(
                name=name,
                defaults={'category': category, 'icon': icon}
            )
        
        self.stdout.write('Created amenities')

    def create_property(self, prop_data, admin_user):
        # Check if property already exists
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
                PropertyAmenity.objects.create(
                    accommodation_property=property_obj,
                    amenity=amenity,
                    is_included=True
                )
            except Amenity.DoesNotExist:
                continue
        
        if property_obj.property_type in ['HOSTEL', 'STUDENT_APARTMENT']:
            self.create_room_types(property_obj, prop_data)
        else:
            self.create_unit_types(property_obj, prop_data)
        
        self.create_proximity_destinations(property_obj, prop_data)
        self.stdout.write(f'Created property: {property_obj.title}')

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
        
        # Get existing room numbers for this property to avoid duplicates
        existing_numbers = set(Room.objects.filter(
            accommodation_property=property_obj
        ).values_list('room_number', flat=True))
        
        room_counter = 1
        for floor in range(1, floor_count + 1):
            for room_num in range(1, rooms_per_floor + 1):
                # Generate unique room number
                while True:
                    room_number = f"{floor}{room_num:02d}"
                    if room_number not in existing_numbers:
                        break
                    # If duplicate, try next number
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

    def get_properties_data(self):
        return self.generate_knust_properties() + self.generate_ucc_properties() + self.generate_accra_properties() + self.generate_takoradi_properties() + self.generate_kumasi_properties()

    def generate_knust_properties(self):
        base = {
            'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana',
            'nearest_institution': 'Kwame Nkrumah University of Science and Technology',
            'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room'],
            'ownership_type': 'INSTITUTION_AFFILIATED',
            'property_category': 'STUDENT_HOUSING',
            'description': 'Modern student accommodation with excellent facilities and security.'
        }
        
        return [
            {**base, 'property_code': 'KNUST-H001', 'property_type': 'HOSTEL', 'title': 'Unity Hall Annex', 'address': 'KNUST Campus, Ayeduase', 'latitude': Decimal('6.6743'), 'longitude': Decimal('-1.5715'), 'distance_to_campus': Decimal('0.5'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'total_area': Decimal('2500.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Laundry Service', 'Elevator', 'Parking'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 20, 'beds_per_room': 1, 'total_capacity': 20, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3500.00'), 'security_deposit': Decimal('500.00')}]}, {'name': 'Double Sharing Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'DOUBLE', 'total_rooms': 15, 'beds_per_room': 2, 'total_capacity': 30, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('2500.00'), 'security_deposit': Decimal('400.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'KNUST-H002', 'property_type': 'HOSTEL', 'title': 'Africa Hall Annex', 'address': 'KNUST Campus, Ayeduase', 'latitude': Decimal('6.6750'), 'longitude': Decimal('-1.5720'), 'distance_to_campus': Decimal('0.8'), 'walking_time_estimate': 8, 'hostel_type': 'GIRLS_ONLY', 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Library'], 'room_types': [{'name': 'Premium Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 15, 'beds_per_room': 1, 'total_capacity': 15, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('4500.00'), 'security_deposit': Decimal('600.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.8'), 'travel_time_minutes': 8}]},
            {**base, 'property_code': 'KNUST-H003', 'property_type': 'HOSTEL', 'title': 'Republic Hall Annex', 'address': 'KNUST Campus, Ayeduase', 'latitude': Decimal('6.6735'), 'longitude': Decimal('-1.5710'), 'distance_to_campus': Decimal('0.6'), 'walking_time_estimate': 6, 'hostel_type': 'BOYS_ONLY', 'total_area': Decimal('2800.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 25, 'beds_per_room': 1, 'total_capacity': 25, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3200.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.6'), 'travel_time_minutes': 6}]},
            {**base, 'property_code': 'KNUST-H004', 'property_type': 'STUDENT_APARTMENT', 'title': 'KNUST Commercial Area Apartments', 'address': 'KNUST Commercial Area', 'latitude': Decimal('6.6740'), 'longitude': Decimal('-1.5725'), 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'ownership_type': 'PRIVATE', 'total_area': Decimal('1500.00'), 'total_floors': 5, 'amenities': ['24/7 Security', 'Free WiFi', 'Elevator', 'Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1800.00'), 'security_deposit': Decimal('2000.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'KNUST-H005', 'property_type': 'HOSTEL', 'title': 'Queens Hall Annex', 'address': 'KNUST Campus, Ayeduase', 'latitude': Decimal('6.6755'), 'longitude': Decimal('-1.5718'), 'distance_to_campus': Decimal('0.7'), 'walking_time_estimate': 7, 'hostel_type': 'GIRLS_ONLY', 'total_area': Decimal('2200.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Library'], 'room_types': [{'name': 'Premium Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('4800.00'), 'security_deposit': Decimal('700.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.7'), 'travel_time_minutes': 7}]},
            {**base, 'property_code': 'KNUST-H006', 'property_type': 'HOSTEL', 'title': 'Katanga Hall Annex', 'address': 'KNUST Campus, Ayeduase', 'latitude': Decimal('6.6738'), 'longitude': Decimal('-1.5712'), 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'MIXED', 'total_area': Decimal('2600.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 18, 'beds_per_room': 1, 'total_capacity': 18, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3400.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
        ]

    def generate_ucc_properties(self):
        base = {
            'city': 'Cape Coast', 'region': 'Central', 'country': 'Ghana',
            'nearest_institution': 'University of Cape Coast',
            'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room'],
            'ownership_type': 'INSTITUTION_AFFILIATED',
            'property_category': 'STUDENT_HOUSING',
            'description': 'Quality student accommodation near campus with modern amenities.'
        }
        
        return [
            {**base, 'property_code': 'UCC-H001', 'property_type': 'HOSTEL', 'title': 'Atlantic Hall Annex', 'address': 'UCC Campus', 'latitude': Decimal('5.1020'), 'longitude': Decimal('-1.2480'), 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'BOYS_ONLY', 'total_area': Decimal('2500.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Laundry Service', 'Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 20, 'beds_per_room': 1, 'total_capacity': 20, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3800.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {**base, 'property_code': 'UCC-H002', 'property_type': 'HOSTEL', 'title': 'Oguaa Hall Annex', 'address': 'UCC Campus', 'latitude': Decimal('5.1025'), 'longitude': Decimal('-1.2485'), 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'GIRLS_ONLY', 'total_area': Decimal('2000.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Library'], 'room_types': [{'name': 'Premium Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('4600.00'), 'security_deposit': Decimal('600.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
            {**base, 'property_code': 'UCC-H003', 'property_type': 'STUDENT_APARTMENT', 'title': 'Cape Coast Student Apartments', 'address': 'Near UCC Campus', 'latitude': Decimal('5.1030'), 'longitude': Decimal('-1.2490'), 'distance_to_campus': Decimal('0.8'), 'walking_time_estimate': 10, 'ownership_type': 'PRIVATE', 'total_area': Decimal('1400.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Elevator', 'Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 10, 'beds_per_room': 1, 'total_capacity': 10, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1600.00'), 'security_deposit': Decimal('2000.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.8'), 'travel_time_minutes': 10}]},
            {**base, 'property_code': 'UCC-H004', 'property_type': 'HOSTEL', 'title': 'Kwame Nkrumah Hall Annex', 'address': 'UCC Campus', 'latitude': Decimal('5.1015'), 'longitude': Decimal('-1.2475'), 'distance_to_campus': Decimal('0.5'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'total_area': Decimal('2200.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Laundry Service', 'Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 16, 'beds_per_room': 1, 'total_capacity': 16, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3300.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'UCC-H005', 'property_type': 'HOSTEL', 'title': 'Casely-Hayford Hall Annex', 'address': 'UCC Campus', 'latitude': Decimal('5.1022'), 'longitude': Decimal('-1.2488'), 'distance_to_campus': Decimal('0.6'), 'walking_time_estimate': 6, 'hostel_type': 'MIXED', 'total_area': Decimal('2400.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Laundry Service', 'Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 18, 'beds_per_room': 1, 'total_capacity': 18, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3200.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'UCC Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.6'), 'travel_time_minutes': 6}]},
        ]

    def generate_accra_properties(self):
        base = {
            'city': 'Accra', 'region': 'Greater Accra', 'country': 'Ghana',
            'amenities': ['24/7 Security', 'Free WiFi'],
            'ownership_type': 'PRIVATE',
            'description': 'Modern residential accommodation in prime Accra location.'
        }
        
        return [
            {**base, 'property_code': 'ACC-A001', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Airport Residential Apartments', 'address': 'Airport Residential Area', 'latitude': Decimal('5.5600'), 'longitude': Decimal('-0.2050'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'suitable_for_expatriates': True, 'total_area': Decimal('3000.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Elevator', 'Parking', 'Generator Backup'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('4500.00'), 'security_deposit': Decimal('9000.00')}]}], 'proximity_destinations': [{'name': 'Kotoka Airport', 'type': 'TRANSPORT', 'distance_km': Decimal('2.0'), 'travel_time_minutes': 5}]},
            {**base, 'property_code': 'ACC-A002', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'East Legon Executive Apartments', 'address': 'East Legon', 'latitude': Decimal('5.6300'), 'longitude': Decimal('-0.1500'), 'nearest_institution': 'University of Ghana', 'distance_to_campus': Decimal('5.0'), 'suitable_for_students': True, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2800.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator', 'Parking'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 10, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2800.00'), 'security_deposit': Decimal('5600.00')}]}], 'proximity_destinations': [{'name': 'University of Ghana', 'type': 'INSTITUTION', 'distance_km': Decimal('5.0'), 'travel_time_minutes': 15}]},
            {**base, 'property_code': 'ACC-A003', 'property_type': 'STUDENT_APARTMENT', 'property_category': 'STUDENT_HOUSING', 'title': 'Legon Student Village', 'address': 'Legon', 'latitude': Decimal('5.6500'), 'longitude': Decimal('-0.1800'), 'nearest_institution': 'University of Ghana', 'distance_to_campus': Decimal('1.5'), 'walking_time_estimate': 15, 'total_area': Decimal('1800.00'), 'total_floors': 3, 'amenities': base['amenities'] + ['Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1000.00'), 'security_deposit': Decimal('1200.00')}]}], 'proximity_destinations': [{'name': 'University of Ghana', 'type': 'INSTITUTION', 'distance_km': Decimal('1.5'), 'travel_time_minutes': 15}]},
            {**base, 'property_code': 'ACC-A004', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'University of Ghana Hostel Annex', 'address': 'University of Ghana Campus', 'latitude': Decimal('5.6520'), 'longitude': Decimal('-0.1870'), 'nearest_institution': 'University of Ghana', 'distance_to_campus': Decimal('0.2'), 'walking_time_estimate': 2, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2600.00'), 'total_floors': 5, 'amenities': base['amenities'] + ['Shared Kitchen', 'Library', 'Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 24, 'beds_per_room': 1, 'total_capacity': 24, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3600.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'University of Ghana', 'type': 'INSTITUTION', 'distance_km': Decimal('0.2'), 'travel_time_minutes': 2}]},
            {**base, 'property_code': 'ACC-A005', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Spintex Road Apartments', 'address': 'Spintex Road', 'latitude': Decimal('5.6200'), 'longitude': Decimal('-0.1200'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'total_area': Decimal('2500.00'), 'total_floors': 4, 'amenities': base['amenities'] + ['Elevator', 'Parking'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2500.00'), 'security_deposit': Decimal('5000.00')}]}], 'proximity_destinations': [{'name': 'Accra Mall', 'type': 'SHOPPING', 'distance_km': Decimal('5.0'), 'travel_time_minutes': 15}]},
        ]

    def generate_takoradi_properties(self):
        return [
            {'property_code': 'TAK-H001', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Takoradi Technical University Hostel', 'description': 'Modern hostel at TTU with excellent facilities for engineering students.', 'address': 'TTU Campus', 'city': 'Takoradi', 'region': 'Western', 'country': 'Ghana', 'latitude': Decimal('4.8800'), 'longitude': Decimal('-1.7500'), 'nearest_institution': 'Takoradi Technical University', 'distance_to_campus': Decimal('0.3'), 'walking_time_estimate': 3, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2200.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 16, 'beds_per_room': 1, 'total_capacity': 16, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3000.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'Takoradi Technical University', 'type': 'INSTITUTION', 'distance_km': Decimal('0.3'), 'travel_time_minutes': 3}]},
            {'property_code': 'TAK-H002', 'property_type': 'STUDENT_APARTMENT', 'property_category': 'STUDENT_HOUSING', 'title': 'Takoradi Student Apartments', 'description': 'Affordable student apartments near TTU campus for independent living.', 'address': 'Near TTU Campus', 'city': 'Takoradi', 'region': 'Western', 'country': 'Ghana', 'latitude': Decimal('4.8850'), 'longitude': Decimal('-1.7550'), 'nearest_institution': 'Takoradi Technical University', 'distance_to_campus': Decimal('1.0'), 'walking_time_estimate': 12, 'ownership_type': 'PRIVATE', 'total_area': Decimal('1500.00'), 'total_floors': 3, 'amenities': ['24/7 Security', 'Free WiFi', 'Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 8, 'beds_per_room': 1, 'total_capacity': 8, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('900.00'), 'security_deposit': Decimal('1000.00')}]}], 'proximity_destinations': [{'name': 'Takoradi Technical University', 'type': 'INSTITUTION', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 12}]},
            {'property_code': 'TAK-H003', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Takoradi Harbour Apartments', 'description': 'Modern apartments near Takoradi Harbour for maritime professionals.', 'address': 'Near Takoradi Harbour', 'city': 'Takoradi', 'region': 'Western', 'country': 'Ghana', 'latitude': Decimal('4.8750'), 'longitude': Decimal('-1.7450'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'ownership_type': 'PRIVATE', 'total_area': Decimal('2000.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Elevator', 'Parking'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2200.00'), 'security_deposit': Decimal('4400.00')}]}], 'proximity_destinations': [{'name': 'Takoradi Harbour', 'type': 'OTHER', 'distance_km': Decimal('1.5'), 'travel_time_minutes': 15}]},
            {'property_code': 'TAK-H004', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Takoradi Nursing Training College Hostel', 'description': 'Female-only hostel for nursing students with excellent study environment.', 'address': 'Nursing Training College Campus', 'city': 'Takoradi', 'region': 'Western', 'country': 'Ghana', 'latitude': Decimal('4.8820'), 'longitude': Decimal('-1.7520'), 'nearest_institution': 'Takoradi Nursing Training College', 'distance_to_campus': Decimal('0.2'), 'walking_time_estimate': 2, 'hostel_type': 'GIRLS_ONLY', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('1800.00'), 'total_floors': 3, 'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Library'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 12, 'beds_per_room': 1, 'total_capacity': 12, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3500.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'Nursing Training College', 'type': 'INSTITUTION', 'distance_km': Decimal('0.2'), 'travel_time_minutes': 2}]},
            {'property_code': 'TAK-H005', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Kojokrom Residential Apartments', 'description': 'Family-oriented apartments in Kojokrom for long-term residents.', 'address': 'Kojokrom', 'city': 'Takoradi', 'region': 'Western', 'country': 'Ghana', 'latitude': Decimal('4.8700'), 'longitude': Decimal('-1.7400'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'ownership_type': 'PRIVATE', 'total_area': Decimal('2200.00'), 'total_floors': 3, 'amenities': ['24/7 Security', 'Free WiFi', 'Parking'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2800.00'), 'security_deposit': Decimal('5600.00')}]}], 'proximity_destinations': [{'name': 'Local Schools', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
        ]

    def generate_kumasi_properties(self):
        return [
            {'property_code': 'KUM-C001', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Kumasi City Center Apartments', 'description': 'Modern apartments in Kumasi city center for urban professionals.', 'address': 'Adum', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6900'), 'longitude': Decimal('-1.6200'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'ownership_type': 'PRIVATE', 'total_area': Decimal('2800.00'), 'total_floors': 5, 'amenities': ['24/7 Security', 'Free WiFi', 'Elevator', 'Parking'], 'unit_types': [{'name': 'One-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 10, 'bedrooms': 1, 'bathrooms': 1, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2400.00'), 'security_deposit': Decimal('4800.00')}]}], 'proximity_destinations': [{'name': 'Kumasi Market', 'type': 'MARKET', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {'property_code': 'KUM-C002', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Patasi Residential Apartments', 'description': 'Family-friendly apartments in Patasi for quiet residential living.', 'address': 'Patasi', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.7000'), 'longitude': Decimal('-1.6300'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'ownership_type': 'PRIVATE', 'total_area': Decimal('2400.00'), 'total_floors': 3, 'amenities': ['24/7 Security', 'Free WiFi', 'Parking'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 8, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2600.00'), 'security_deposit': Decimal('5200.00')}]}], 'proximity_destinations': [{'name': 'Local Schools', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {'property_code': 'KUM-C003', 'property_type': 'STUDENT_APARTMENT', 'property_category': 'STUDENT_HOUSING', 'title': 'KNUST Off-Campus Student Apartments', 'description': 'Affordable student apartments near KNUST campus for independent students.', 'address': 'Kotei', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6800'), 'longitude': Decimal('-1.5800'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('2.0'), 'walking_time_estimate': 20, 'ownership_type': 'PRIVATE', 'total_area': Decimal('1600.00'), 'total_floors': 3, 'amenities': ['24/7 Security', 'Free WiFi', 'Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 10, 'beds_per_room': 1, 'total_capacity': 10, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1100.00'), 'security_deposit': Decimal('1300.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('2.0'), 'travel_time_minutes': 20}]},
            {'property_code': 'KUM-C004', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Asokwa Residential Apartments', 'description': 'Modern apartments in Asokwa for families and professionals.', 'address': 'Asokwa', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6950'), 'longitude': Decimal('-1.6400'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'ownership_type': 'PRIVATE', 'total_area': Decimal('2600.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Parking', 'Garden'], 'unit_types': [{'name': 'Two-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 6, 'bedrooms': 2, 'bathrooms': 2, 'kitchen': 1, 'balcony': True, 'furnished_status': 'SEMI_FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('2700.00'), 'security_deposit': Decimal('5400.00')}]}], 'proximity_destinations': [{'name': 'Commercial Area', 'type': 'MARKET', 'distance_km': Decimal('1.0'), 'travel_time_minutes': 10}]},
            {'property_code': 'KUM-C005', 'property_type': 'APARTMENT', 'property_category': 'RESIDENTIAL', 'title': 'Kwadaso Executive Apartments', 'description': 'Executive apartments in Kwadaso for professionals and families.', 'address': 'Kwadaso', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.7100'), 'longitude': Decimal('-1.6500'), 'suitable_for_students': False, 'suitable_for_workers': True, 'suitable_for_families': True, 'ownership_type': 'PRIVATE', 'total_area': Decimal('3000.00'), 'total_floors': 5, 'amenities': ['24/7 Security', 'Free WiFi', 'Elevator', 'Parking', 'Generator Backup'], 'unit_types': [{'name': 'Three-Bedroom Apartment', 'billing_model': 'MONTHLY_BASED', 'number_of_units': 4, 'bedrooms': 3, 'bathrooms': 3, 'kitchen': 1, 'balcony': True, 'furnished_status': 'FURNISHED', 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('4000.00'), 'security_deposit': Decimal('8000.00')}]}], 'proximity_destinations': [{'name': 'Commercial Area', 'type': 'MARKET', 'distance_km': Decimal('1.5'), 'travel_time_minutes': 15}]},
            {'property_code': 'KNUST-H007', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Brunei Hall Annex', 'description': 'Modern mixed hostel with state-of-the-art facilities and comfort.', 'address': 'KNUST Campus, Ayeduase', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6745'), 'longitude': Decimal('-1.5722'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('0.5'), 'walking_time_estimate': 5, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2400.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room', 'Library', 'Elevator'], 'room_types': [{'name': 'Premium Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 16, 'beds_per_room': 1, 'total_capacity': 16, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('4200.00'), 'security_deposit': Decimal('600.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.5'), 'travel_time_minutes': 5}]},
            {'property_code': 'KNUST-H008', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Conti Hall Annex', 'description': 'Traditional male hostel with rich history and strong alumni network.', 'address': 'KNUST Campus, Ayeduase', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6732'), 'longitude': Decimal('-1.5708'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('0.6'), 'walking_time_estimate': 6, 'hostel_type': 'BOYS_ONLY', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2700.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Study Room', 'Elevator'], 'room_types': [{'name': 'Standard Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 22, 'beds_per_room': 1, 'total_capacity': 22, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('3100.00'), 'security_deposit': Decimal('500.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.6'), 'travel_time_minutes': 6}]},
            {'property_code': 'KNUST-H009', 'property_type': 'STUDENT_APARTMENT', 'property_category': 'STUDENT_HOUSING', 'title': 'Ayeduase Student Apartments', 'description': 'Affordable student apartments located in Ayeduase community.', 'address': 'Ayeduase', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6760'), 'longitude': Decimal('-1.5730'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('1.2'), 'walking_time_estimate': 15, 'ownership_type': 'PRIVATE', 'total_area': Decimal('1200.00'), 'total_floors': 3, 'amenities': ['24/7 Security', 'Free WiFi', 'Parking'], 'room_types': [{'name': 'Studio Apartment', 'billing_model': 'MONTHLY_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 10, 'beds_per_room': 1, 'total_capacity': 10, 'pricing': [{'payment_type': 'MONTHLY', 'monthly_price': Decimal('1200.00'), 'security_deposit': Decimal('1500.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('1.2'), 'travel_time_minutes': 15}]},
            {'property_code': 'KNUST-H010', 'property_type': 'HOSTEL', 'property_category': 'STUDENT_HOUSING', 'title': 'Ghana Hall Annex', 'description': 'Modern mixed hostel with excellent facilities and strong academic focus.', 'address': 'KNUST Campus, Ayeduase', 'city': 'Kumasi', 'region': 'Ashanti', 'country': 'Ghana', 'latitude': Decimal('6.6748'), 'longitude': Decimal('-1.5716'), 'nearest_institution': 'Kwame Nkrumah University of Science and Technology', 'distance_to_campus': Decimal('0.4'), 'walking_time_estimate': 4, 'hostel_type': 'MIXED', 'ownership_type': 'INSTITUTION_AFFILIATED', 'total_area': Decimal('2300.00'), 'total_floors': 4, 'amenities': ['24/7 Security', 'Free WiFi', 'Shared Kitchen', 'Library', 'Elevator'], 'room_types': [{'name': 'Premium Single Room', 'billing_model': 'SEMESTER_BASED', 'occupancy_type': 'SINGLE', 'total_rooms': 14, 'beds_per_room': 1, 'total_capacity': 14, 'pricing': [{'payment_type': 'SEMESTER', 'semester_price': Decimal('4000.00'), 'security_deposit': Decimal('600.00')}]}], 'proximity_destinations': [{'name': 'KNUST Main Campus', 'type': 'INSTITUTION', 'distance_km': Decimal('0.4'), 'travel_time_minutes': 4}]},
        ]
