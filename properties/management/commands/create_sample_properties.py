from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from properties.models import Property, Amenity, RoomType, UnitType, RoomTypePricing, UnitTypePricing, RentalDuration

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample hostel and apartment properties'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample properties before creating new ones',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)
        
        if clear:
            self.stdout.write('Clearing existing sample properties...')
            Property.objects.filter(property_code__startswith='HST').delete()
            Property.objects.filter(property_code__startswith='APT').delete()
            RoomType.objects.all().delete()
            UnitType.objects.all().delete()
            RoomTypePricing.objects.all().delete()
            UnitTypePricing.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing properties'))
        
        self.stdout.write('Creating sample properties...')
        
        # Create or get a user for uploaded_by
        user, created = User.objects.get_or_create(
            email='admin@staymatch.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'phone': '+233241234567',
                'user_type': 'ADMIN'
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create amenities
        amenities_data = [
            ('WiFi', 'INTERNET', 'fa-wifi'),
            ('Security', 'SAFETY', 'fa-shield-alt'),
            ('Water', 'UTILITIES', 'fa-tint'),
            ('Electricity', 'UTILITIES', 'fa-bolt'),
            ('Generator', 'UTILITIES', 'fa-plug'),
            ('Parking', 'GENERAL', 'fa-parking'),
            ('CCTV', 'SAFETY', 'fa-video'),
            ('Kitchen', 'KITCHEN', 'fa-utensils'),
            ('Laundry', 'LAUNDRY', 'fa-tshirt'),
            ('Study Area', 'STUDY', 'fa-book'),
            ('Common Room', 'GENERAL', 'fa-couch'),
            ('Gym', 'GENERAL', 'fa-dumbbell'),
            ('Swimming Pool', 'OUTDOOR', 'fa-swimming-pool'),
            ('Garden', 'OUTDOOR', 'fa-tree'),
            ('Air Conditioning', 'UTILITIES', 'fa-snowflake'),
        ]
        
        amenities = []
        for name, category, icon in amenities_data:
            amenity, created = Amenity.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'icon': icon,
                    'description': f'{name} facility'
                }
            )
            amenities.append(amenity)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(amenities)} amenities'))
        
        # Create 10 hostels
        hostels_data = [
            {
                'title': 'Royal Heights Hostel',
                'address': '123 Campus Road, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'nearest_institution': 'KNUST',
                'distance_to_campus': 0.5,
                'description': 'Premium student accommodation near KNUST with modern amenities and comfortable living spaces.',
            },
            {
                'title': 'Elite Student Residence',
                'address': '45 Legon Road, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'nearest_institution': 'University of Ghana',
                'distance_to_campus': 0.3,
                'description': 'Luxury student residence in Legon with state-of-the-art facilities.',
            },
            {
                'title': 'Park View Accommodation',
                'address': '78 University Ave, Cape Coast',
                'city': 'Cape Coast',
                'region': 'Central',
                'nearest_institution': 'UCC',
                'distance_to_campus': 0.8,
                'description': 'Affordable student housing with beautiful park views near UCC.',
            },
            {
                'title': 'Sunrise Hostel',
                'address': '56 Tech Road, Takoradi',
                'city': 'Takoradi',
                'region': 'Western',
                'nearest_institution': 'Takoradi Technical University',
                'distance_to_campus': 1.2,
                'description': 'Modern hostel with excellent facilities for students.',
            },
            {
                'title': 'Blue Sky Hostel',
                'address': '23 Main Street, Tamale',
                'city': 'Tamale',
                'region': 'Northern',
                'nearest_institution': 'UDS',
                'distance_to_campus': 2.0,
                'description': 'Comfortable accommodation for students in the Northern region.',
            },
            {
                'title': 'Green Valley Hostel',
                'address': '89 Education Lane, Sunyani',
                'city': 'Sunyani',
                'region': 'Bono',
                'nearest_institution': 'UENR',
                'distance_to_campus': 1.5,
                'description': 'Eco-friendly hostel with sustainable features.',
            },
            {
                'title': 'City Center Hostel',
                'address': '12 Market Street, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'nearest_institution': 'KNUST',
                'distance_to_campus': 3.0,
                'description': 'Conveniently located hostel in the heart of Kumasi.',
            },
            {
                'title': 'Ocean View Hostel',
                'address': '34 Beach Road, Winneba',
                'city': 'Winneba',
                'region': 'Central',
                'nearest_institution': 'UEW',
                'distance_to_campus': 1.0,
                'description': 'Scenic hostel with ocean views near University of Education.',
            },
            {
                'title': 'Tech Hub Hostel',
                'address': '67 Innovation Drive, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'nearest_institution': 'Accra Technical University',
                'distance_to_campus': 0.7,
                'description': 'Modern tech-focused hostel with high-speed internet.',
            },
            {
                'title': 'Garden City Hostel',
                'address': '91 Botanical Ave, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'nearest_institution': 'KNUST',
                'distance_to_campus': 1.8,
                'description': 'Peaceful hostel surrounded by beautiful gardens.',
            },
        ]
        
        for i, hostel_data in enumerate(hostels_data, 1):
            property_code = f'HST{i:04d}'
            property_obj = Property.objects.create(
                uploaded_by=user,
                property_code=property_code,
                property_type='HOSTEL',
                property_category='STUDENT_HOUSING',
                title=hostel_data['title'],
                description=hostel_data['description'],
                address=hostel_data['address'],
                city=hostel_data['city'],
                region=hostel_data['region'],
                country='Ghana',
                nearest_institution=hostel_data['nearest_institution'],
                distance_to_campus=hostel_data['distance_to_campus'],
                total_area=500 + (i * 50),
                hostel_type='MIXED',
                ownership_type='PRIVATE',
                is_available=True,
                is_verified=True,
                status='APPROVED',
                is_featured=(i <= 3),
                security_personnel=True,
                cctv=True,
                gated_community=True,
                water_availability='24/7',
                electricity_stability='Stable',
                internet_availability='High-speed',
                utility_billing_method='SEPARATE_BILLING',
            )
            
            # Add amenities to hostel
            property_obj.amenities.set(amenities[:8])
            
            # Create room types for hostel
            room_types = [
                ('Single Room', 'SINGLE', 1, 2500, 3000),
                ('Double Room', 'DOUBLE', 2, 1800, 2200),
                ('Triple Room', 'TRIPLE', 3, 1500, 1800),
                ('Quad Room', 'QUAD', 4, 1200, 1500),
            ]
            
            for rt_name, occupancy_type, beds, semester_price, yearly_price in room_types:
                room_type = RoomType.objects.create(
                    accommodation_property=property_obj,
                    room_type_name=rt_name,
                    occupancy_type=occupancy_type,
                    total_rooms=5 + i,
                    beds_per_room=beds,
                    total_capacity=(5 + i) * beds,
                    available_slots=(5 + i) * beds,
                    occupied_slots=0,
                    private_bathroom=False,
                    wifi_available=True,
                    study_desk_available=True,
                    wardrobe_available=True,
                    fan=True,
                )
                
                # Create pricing
                RoomTypePricing.objects.create(
                    room_type=room_type,
                    payment_type='SEMESTER',
                    semester_price=semester_price,
                    currency='GHS'
                )
                
                RoomTypePricing.objects.create(
                    room_type=room_type,
                    payment_type='YEARLY',
                    yearly_price=yearly_price,
                    currency='GHS'
                )
        
        self.stdout.write(self.style.SUCCESS('Created 10 hostels'))
        
        # Create 10 apartments
        apartments_data = [
            {
                'title': 'Sunrise Apartments',
                'address': '123 East Legon, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Modern apartments in East Legon with premium amenities.',
            },
            {
                'title': 'Elite Residences',
                'address': '45 Airport Residential, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Luxury apartments in the Airport Residential area.',
            },
            {
                'title': 'Garden City Apartments',
                'address': '78 Ahodwo, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'description': 'Beautiful apartments with garden views in Kumasi.',
            },
            {
                'title': 'Ocean View Apartments',
                'address': '56 Beach Road, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Stunning apartments with ocean views.',
            },
            {
                'title': 'City Center Apartments',
                'address': '23 Central Business District, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Convenient apartments in the heart of Accra.',
            },
            {
                'title': 'Green Valley Apartments',
                'address': '89 Ridge, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'description': 'Peaceful apartments in a quiet neighborhood.',
            },
            {
                'title': 'Tech Hub Apartments',
                'address': '34 Cantonments, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Modern apartments ideal for tech professionals.',
            },
            {
                'title': 'University Heights',
                'address': '67 Legon, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Student-friendly apartments near University of Ghana.',
            },
            {
                'title': 'Serenity Gardens',
                'address': '12 Spintex, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Tranquil apartments with beautiful gardens.',
            },
            {
                'title': 'Metro Living',
                'address': '91 Ridge, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'description': 'Contemporary apartments in a prime location.',
            },
        ]
        
        for i, apt_data in enumerate(apartments_data, 1):
            property_code = f'APT{i:04d}'
            property_obj = Property.objects.create(
                uploaded_by=user,
                property_code=property_code,
                property_type='APARTMENT',
                property_category='RESIDENTIAL',
                title=apt_data['title'],
                description=apt_data['description'],
                address=apt_data['address'],
                city=apt_data['city'],
                region=apt_data['region'],
                country='Ghana',
                total_area=150 + (i * 20),
                total_floors=3 + (i % 3),
                is_available=True,
                is_verified=True,
                status='APPROVED',
                is_featured=(i <= 3),
                security_personnel=True,
                cctv=True,
                gated_community=True,
                water_availability='24/7',
                electricity_stability='Stable',
                internet_availability='High-speed',
                utility_billing_method='SEPARATE_BILLING',
            )
            
            # Add amenities to apartment
            property_obj.amenities.set(amenities[:10])
            
            # Create unit types for apartment
            unit_types = [
                ('Studio', 1, 1, 1800, 2500),
                ('1 Bedroom', 1, 1, 2500, 3500),
                ('2 Bedroom', 2, 2, 3500, 4500),
                ('3 Bedroom', 3, 3, 4500, 6000),
            ]
            
            for ut_name, bedrooms, bathrooms, monthly_price, yearly_price in unit_types:
                unit_type = UnitType.objects.create(
                    accommodation_property=property_obj,
                    unit_name=ut_name,
                    number_of_units=3 + i,
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    kitchen=1,
                    total_units=3 + i,
                    occupied_units=0,
                    available_units=3 + i,
                    furnished_status='SEMI_FURNISHED',
                    air_conditioning=True,
                    water_heater=True,
                    refrigerator=True,
                    internet=True,
                    generator=True,
                )
                
                # Create pricing
                UnitTypePricing.objects.create(
                    unit_type=unit_type,
                    payment_type='MONTHLY',
                    monthly_price=monthly_price,
                    currency='GHS'
                )
                
                UnitTypePricing.objects.create(
                    unit_type=unit_type,
                    payment_type='YEARLY',
                    yearly_price=yearly_price,
                    currency='GHS'
                )
        
        self.stdout.write(self.style.SUCCESS('Created 10 apartments'))
        self.stdout.write(self.style.SUCCESS('Sample properties created successfully!'))
