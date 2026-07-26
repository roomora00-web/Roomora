import os
import shutil
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from properties.models import (
    Property, PropertyAmenity, Amenity, RoomType, RoomTypePricing,
    UnitType, UnitTypePricing, Room, PropertyImage, RoomImage, ProximityDestination, RentalDuration
)
from accounts.models import User
from feedback.models import Review
from bookings.models import Booking

class Command(BaseCommand):
    help = 'Populate the database with 10 detailed properties in Takoradi, Accra, Tema, Kumasi with real images, rooms, amenities, and reviews'

    def handle(self, *args, **options):
        self.stdout.write('Starting execution of 10-properties database population...')
        
        # 1. Setup Admin and Reviewer Users
        admin_user = User.objects.filter(user_type='ADMIN').first()
        if not admin_user:
            admin_user = User.objects.create_user(
                email='admin@staymatch.com',
                password='admin123',
                first_name='Kwame',
                last_name='Mensa',
                user_type='ADMIN'
            )
            self.stdout.write('Created default admin user.')
            
        student_users = list(User.objects.filter(user_type='STUDENT'))
        if len(student_users) < 4:
            # Create additional student users if needed to write reviews
            student_emails = [
                ('achanickanna@gmail.com', 'Achanick', 'Anna'),
                ('gazyjohnson18@gmail.com', 'Gazy', 'Johnson'),
                ('prettyserwaa20@gmail.com', 'Pretty', 'Serwaa'),
                ('benedictwordey20@gmail.com', 'Benedict', 'Wordey'),
                ('giftyamihere48@gmail.com', 'Gifty', 'Amihere')
            ]
            for email, fname, lname in student_emails:
                u, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': fname,
                        'last_name': lname,
                        'user_type': 'STUDENT',
                        'phone': '+23324' + ''.join(random.choices('0123456789', k=7))
                    }
                )
                if created:
                    u.set_password('student123')
                    u.save()
            student_users = list(User.objects.filter(user_type='STUDENT'))
        
        self.stdout.write(f'Using {len(student_users)} student accounts for writing reviews.')

        # 2. Get available images from user source folder
        source_dir = '/home/gazy-johnson/Downloads/school/ROOMORA/Properties00'
        if not os.path.exists(source_dir):
            self.stdout.write(self.style.ERROR(f'Source folder {source_dir} does not exist!'))
            return
            
        # Target media dirs
        media_property_dir = os.path.join(settings.MEDIA_ROOT, 'property_images')
        media_room_dir = os.path.join(settings.MEDIA_ROOT, 'room_images')
        os.makedirs(media_property_dir, exist_ok=True)
        os.makedirs(media_room_dir, exist_ok=True)

        # Image collection lists
        apt_images = [os.path.join(source_dir, 'APARTMENT', f) for f in os.listdir(os.path.join(source_dir, 'APARTMENT')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))]
        hostel_images = [os.path.join(source_dir, 'HOSTELS', f) for f in os.listdir(os.path.join(source_dir, 'HOSTELS')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))]
        bathroom_images = [os.path.join(source_dir, 'bathrooms', f) for f in os.listdir(os.path.join(source_dir, 'bathrooms')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))]
        kitchen_images = [os.path.join(source_dir, 'kitchen', f) for f in os.listdir(os.path.join(source_dir, 'kitchen')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))]
        villa_images = [os.path.join(source_dir, 'villa', f) for f in os.listdir(os.path.join(source_dir, 'villa')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))]
        compound_images = [os.path.join(source_dir, 'compound house', f) for f in os.listdir(os.path.join(source_dir, 'compound house')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))]

        self.stdout.write(f'Discovered images: APT={len(apt_images)}, Hostels={len(hostel_images)}, Bathrooms={len(bathroom_images)}, Kitchens={len(kitchen_images)}, Villas={len(villa_images)}, Compound House={len(compound_images)}')

        # Helper function to copy file safely and return media relative path
        def copy_image(src_path, dest_subfolder, prefix):
            if not src_path or not os.path.exists(src_path):
                return None
            ext = os.path.splitext(src_path)[1]
            unique_name = f"{prefix}_{random.randint(10000, 99999)}{ext}"
            dest_dir = os.path.join(settings.MEDIA_ROOT, dest_subfolder)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, unique_name)
            shutil.copy2(src_path, dest_path)
            return f"{dest_subfolder}/{unique_name}"

        # 3. Create core amenities if they don't exist
        amenity_names = [
            'High-Speed Internet', '24/7 Security', 'Study Areas', 'Consistent Water Supply',
            'Electricity Generator', 'CCTV Surveillance', 'Shared Kitchen', 'Laundry Room',
            'Private Bathroom', 'Air Conditioning', 'Ceiling Fan', 'Gated Access',
            'Car Parking', 'Water Reservoir'
        ]
        amenity_map = {}
        for name in amenity_names:
            category = 'GENERAL'
            if 'Security' in name or 'CCTV' in name or 'Gated' in name:
                category = 'SAFETY'
            elif 'Internet' in name:
                category = 'INTERNET'
            elif 'Water' in name or 'Electricity' in name or 'Generator' in name:
                category = 'UTILITIES'
            elif 'Kitchen' in name:
                category = 'KITCHEN'
            elif 'Bathroom' in name:
                category = 'BATHROOM'
            elif 'Study' in name:
                category = 'STUDY'
                
            amenity, _ = Amenity.objects.get_or_create(
                name=name,
                defaults={'category': category, 'icon': 'shield'}
            )
            amenity_map[name] = amenity

        # 4. Property Specifications
        properties_data = [
            # 1. Pentagon Premier Hostel (Accra) - 4.8 / 5.0
            {
                'property_code': 'HST-ACC-001',
                'title': 'Pentagon Premier Hostel',
                'property_type': 'HOSTEL',
                'property_category': 'STUDENT_HOUSING',
                'description': 'Pentagon Premier Hostel offers state-of-the-art living options for students of the University of Ghana. Equipped with modern quiet study areas, gated security protocols, high-speed WiFi networks, and regular running water.',
                'address': 'Pentagon Hall Road, Legon Campus, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'nearest_institution': 'University of Ghana',
                'distance_to_campus': Decimal('0.20'),
                'walking_time_estimate': 4,
                'nearby_landmarks': 'UG Botanical Gardens, Legon Hall, University Stadium',
                'total_area': Decimal('1500.00'),
                'total_floors': 4,
                'hostel_type': 'MIXED',
                'ownership_type': 'PRIVATE',
                'house_rules': 'No noise after 10:00 PM. No unauthorized visitors overnight. Keep kitchens clean after use.',
                'cancellation_policy': 'Full refund up to 14 days before residency start date.',
                'target_rating': 4.8,
                'reviews_count': 5,
                'ratings_list': [5, 5, 5, 4, 5],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Study Areas', 'Consistent Water Supply', 'CCTV Surveillance', 'Electricity Generator', 'Water Reservoir'],
                'proximity_destinations': [
                    ('Main Campus Lecture Halls', 'INSTITUTION', Decimal('0.30'), 5, 'WALK'),
                    ('Legon Shell Fuel Station', 'TRANSPORT', Decimal('1.20'), 15, 'WALK'),
                    ('University Hospital', 'HOSPITAL', Decimal('0.90'), 10, 'WALK')
                ],
                'pricing_configs': [
                    {'name': '1-in-a-room Premium', 'beds': 1, 'price': Decimal('3200.00'), 'occupancy': 'SINGLE'},
                    {'name': '2-in-a-room Premium', 'beds': 2, 'price': Decimal('1900.00'), 'occupancy': 'DOUBLE'}
                ],
                'img_type': 'HOSTEL'
            },
            # 2. East Legon Luxury Apartment (Accra) - 5.0 / 5.0
            {
                'property_code': 'APT-ACC-002',
                'title': 'East Legon Luxury Apartment',
                'property_type': 'APARTMENT',
                'property_category': 'EXECUTIVE_HOUSING',
                'description': 'A premium luxury apartment block in the heart of East Legon. Features high-end finishes, consistent city utility supply, gated access, security guards, and modern appliances for young professionals and corporate executives.',
                'address': '12 Boundary Road, East Legon, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'nearest_institution': 'UPSA',
                'distance_to_campus': Decimal('1.50'),
                'walking_time_estimate': 18,
                'nearby_landmarks': 'A&C Mall, Legon Bypass, AnC Square',
                'total_area': Decimal('320.00'),
                'total_floors': 3,
                'house_rules': 'Quiet hours from 10 PM to 6 AM. Pets subject to prior approval. Waste disposal guidelines to be strictly followed.',
                'cancellation_policy': 'Moderate. 50% refund if cancelled within 7 days of arrival.',
                'target_rating': 5.0,
                'reviews_count': 3,
                'ratings_list': [5, 5, 5],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Consistent Water Supply', 'Air Conditioning', 'Car Parking', 'CCTV Surveillance'],
                'proximity_destinations': [
                    ('A&C Mall Shopping Center', 'SHOPPING', Decimal('0.80'), 10, 'WALK'),
                    ('UPSA Campus Gate', 'INSTITUTION', Decimal('1.50'), 5, 'DRIVE')
                ],
                'pricing_configs': [
                    {'name': '1-Bedroom Executive Unit', 'bedrooms': 1, 'bathrooms': 1, 'price': Decimal('5200.00')},
                    {'name': '2-Bedroom Luxury Suite', 'bedrooms': 2, 'bathrooms': 2, 'price': Decimal('8500.00')}
                ],
                'img_type': 'APARTMENT'
            },
            # 3. Berekuso Hills Student Villa (Accra/Eastern) - 4.5 / 5.0
            {
                'property_code': 'VLA-ACC-003',
                'title': 'Berekuso Hills Student Villa',
                'property_type': 'VILLA',
                'property_category': 'STUDENT_HOUSING',
                'description': 'Perched beautifully on the Berekuso hills with sweeping views and crisp clean breezes. Built specifically for students seeking premium co-living, academic focus, and convenient access to campus.',
                'address': 'Ashesi University Bypass, Berekuso',
                'city': 'Accra',
                'region': 'Eastern',
                'nearest_institution': 'Ashesi University',
                'distance_to_campus': Decimal('0.40'),
                'walking_time_estimate': 6,
                'nearby_landmarks': 'Ashesi Hilltop Campus, Berekuso Town Square',
                'total_area': Decimal('800.00'),
                'total_floors': 2,
                'house_rules': 'Maintain quiet hours. No loud music inside rooms. Smoking strictly prohibited on the estate.',
                'cancellation_policy': 'Strict. 30 days notice required for cancellations.',
                'target_rating': 4.5,
                'reviews_count': 4,
                'ratings_list': [5, 4, 5, 4],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Study Areas', 'Consistent Water Supply', 'Ceiling Fan', 'Gated Access', 'Water Reservoir'],
                'proximity_destinations': [
                    ('Ashesi Main Lecture Hall', 'INSTITUTION', Decimal('0.40'), 6, 'WALK'),
                    ('Berekuso Local Market', 'MARKET', Decimal('0.60'), 8, 'WALK')
                ],
                'pricing_configs': [
                    {'name': 'Executive Single Room', 'bedrooms': 1, 'bathrooms': 1, 'price': Decimal('4500.00')},
                    {'name': 'Double Shared Room', 'bedrooms': 2, 'bathrooms': 2, 'price': Decimal('2800.00')}
                ],
                'img_type': 'VILLA'
            },
            # 4. Royal Heights Hostel (Kumasi) - 5.0 / 5.0
            {
                'property_code': 'HST-KMS-004',
                'title': 'Royal Heights Hostel',
                'property_type': 'HOSTEL',
                'property_category': 'STUDENT_HOUSING',
                'description': 'Kumasi\'s most premium private hostel near KNUST. Featuring fully air-conditioned rooms, a modern electronic library, fully backed utility infrastructure, CCTV camera networks, and spacious study halls.',
                'address': 'Ahinsan Estate Gate, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'nearest_institution': 'KNUST',
                'distance_to_campus': Decimal('0.60'),
                'walking_time_estimate': 8,
                'nearby_landmarks': 'Ahinsan Junction, KNUST Commercial Area, Kumasi Mall',
                'total_area': Decimal('2200.00'),
                'total_floors': 5,
                'hostel_type': 'MIXED',
                'ownership_type': 'PRIVATE',
                'house_rules': 'Curfew strictly enforced at 11:30 PM. No visitor check-ins after 10 PM. Kitchen cleanliness is mandatory.',
                'cancellation_policy': 'No refund after semester begins.',
                'target_rating': 5.0,
                'reviews_count': 3,
                'ratings_list': [5, 5, 5],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Study Areas', 'Consistent Water Supply', 'Electricity Generator', 'Air Conditioning', 'CCTV Surveillance', 'Water Reservoir'],
                'proximity_destinations': [
                    ('KNUST Business School', 'INSTITUTION', Decimal('0.60'), 8, 'WALK'),
                    ('Kumasi City Mall', 'SHOPPING', Decimal('2.50'), 10, 'TROTRO'),
                    ('Bomso Gate Bus Stop', 'TRANSPORT', Decimal('0.50'), 6, 'WALK')
                ],
                'pricing_configs': [
                    {'name': '1-in-a-room AC Premium', 'beds': 1, 'price': Decimal('4800.00'), 'occupancy': 'SINGLE'},
                    {'name': '2-in-a-room AC Premium', 'beds': 2, 'price': Decimal('2900.00'), 'occupancy': 'DOUBLE'}
                ],
                'img_type': 'HOSTEL'
            },
            # 5. KNUST Jubilee Hostel (Kumasi) - 4.2 / 5.0
            {
                'property_code': 'HST-KMS-005',
                'title': 'KNUST Jubilee Hostel',
                'property_type': 'HOSTEL',
                'property_category': 'STUDENT_HOUSING',
                'description': 'A well-loved and highly accessible student hostel managed under university affiliation guidelines. Located within walking distance to campus libraries and science departments.',
                'address': 'Bomso Rd, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'nearest_institution': 'KNUST',
                'distance_to_campus': Decimal('0.40'),
                'walking_time_estimate': 5,
                'nearby_landmarks': 'Bomso Gate, College of Science, Jubilee Mall',
                'total_area': Decimal('1800.00'),
                'total_floors': 4,
                'hostel_type': 'MIXED',
                'ownership_type': 'INSTITUTION_AFFILIATED',
                'house_rules': 'Curfew time 10:30 PM. No loud noises. Visitors are restricted to common lounges only.',
                'cancellation_policy': 'Standard University accommodation policy applies.',
                'target_rating': 4.2,
                'reviews_count': 4,
                'ratings_list': [4, 4, 5, 4],
                'amenities': ['24/7 Security', 'Consistent Water Supply', 'Study Areas', 'Ceiling Fan', 'Gated Access', 'Water Reservoir'],
                'proximity_destinations': [
                    ('College of Science Library', 'STUDY', Decimal('0.45'), 5, 'WALK'),
                    ('Jubilee Food Court', 'RESTAURANT', Decimal('0.30'), 4, 'WALK')
                ],
                'pricing_configs': [
                    {'name': '2-in-a-room Shared Room', 'beds': 2, 'price': Decimal('1600.00'), 'occupancy': 'DOUBLE'},
                    {'name': '3-in-a-room Shared Room', 'beds': 3, 'price': Decimal('1200.00'), 'occupancy': 'TRIPLE'}
                ],
                'img_type': 'HOSTEL'
            },
            # 6. Kumasi Executive Suite (Kumasi) - 4.9 / 5.0
            {
                'property_code': 'APT-KMS-006',
                'title': 'Kumasi Executive Suite',
                'property_type': 'APARTMENT',
                'property_category': 'EXECUTIVE_HOUSING',
                'description': 'An upscale residential apartment block in Ahodwo. Designed for corporate workers, researchers, and postgraduate students seeking quiet, self-contained living with full amenities.',
                'address': 'Ahodwo Roundabout, Ahodwo Crescent, Kumasi',
                'city': 'Kumasi',
                'region': 'Ashanti',
                'nearest_institution': 'KNUST',
                'distance_to_campus': Decimal('4.00'),
                'walking_time_estimate': 45,
                'nearby_landmarks': 'Ahodwo Melcom, Kumasi Royal Golf Club',
                'total_area': Decimal('450.00'),
                'total_floors': 3,
                'house_rules': 'Quiet hours 10 PM. No commercial activities allowed inside units. Maintenance requests must be filed online.',
                'cancellation_policy': 'Moderate. 1 month advance notice required.',
                'target_rating': 4.9,
                'reviews_count': 10,
                'ratings_list': [5, 5, 5, 5, 5, 4, 5, 5, 5, 5],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Consistent Water Supply', 'Air Conditioning', 'Car Parking', 'CCTV Surveillance', 'Electricity Generator'],
                'proximity_destinations': [
                    ('Ahodwo Shopping Center', 'SHOPPING', Decimal('0.50'), 6, 'WALK'),
                    ('KNUST Main Gate', 'INSTITUTION', Decimal('4.00'), 12, 'DRIVE')
                ],
                'pricing_configs': [
                    {'name': '1-Bedroom Luxury Apartment', 'bedrooms': 1, 'bathrooms': 1, 'price': Decimal('3800.00')},
                    {'name': '2-Bedroom Luxury Suite', 'bedrooms': 2, 'bathrooms': 2, 'price': Decimal('5500.00')}
                ],
                'img_type': 'APARTMENT'
            },
            # 7. TTU Sunset Hostel (Takoradi) - 3.8 / 5.0
            {
                'property_code': 'HST-TDR-007',
                'title': 'TTU Sunset Hostel',
                'property_type': 'HOSTEL',
                'property_category': 'STUDENT_HOUSING',
                'description': 'Sunset Hostel provides highly affordable student housing close to Takoradi Technical University. Offering standard study spaces, ceiling fans, gated access, and local transit proximity.',
                'address': 'Sunset Blvd near TTU Campus, Takoradi',
                'city': 'Takoradi',
                'region': 'Western',
                'nearest_institution': 'Takoradi Technical University',
                'distance_to_campus': Decimal('0.80'),
                'walking_time_estimate': 10,
                'nearby_landmarks': 'TTU Administrative Block, Takoradi Market Circle',
                'total_area': Decimal('1100.00'),
                'total_floors': 3,
                'hostel_type': 'MIXED',
                'ownership_type': 'PRIVATE',
                'house_rules': 'Lock gates at 11:00 PM. No unauthorized visitors. Students must clean their individual rooms weekly.',
                'cancellation_policy': 'Standard. 15% cancellation fee applies.',
                'target_rating': 3.8,
                'reviews_count': 4,
                'ratings_list': [4, 3, 4, 4],
                'amenities': ['24/7 Security', 'Consistent Water Supply', 'Study Areas', 'Ceiling Fan', 'Gated Access', 'Water Reservoir'],
                'proximity_destinations': [
                    ('TTU Engineering Block', 'INSTITUTION', Decimal('0.80'), 10, 'WALK'),
                    ('Takoradi Market Circle', 'MARKET', Decimal('2.00'), 10, 'TROTRO')
                ],
                'pricing_configs': [
                    {'name': '2-in-a-room Shared Study', 'beds': 2, 'price': Decimal('1400.00'), 'occupancy': 'DOUBLE'},
                    {'name': '4-in-a-room Shared Study', 'beds': 4, 'price': Decimal('900.00'), 'occupancy': 'QUAD'}
                ],
                'img_type': 'HOSTEL'
            },
            # 8. Anaji Gardens Apartment (Takoradi) - 5.0 / 5.0
            {
                'property_code': 'APT-TDR-008',
                'title': 'Anaji Gardens Apartment',
                'property_type': 'APARTMENT',
                'property_category': 'RESIDENTIAL',
                'description': 'A beautiful modern apartment complex situated in the serene Anaji residential enclave. Lush green gardens, solid concrete architecture, reliable utility backup, and standard security staffing.',
                'address': 'Anaji Gardens Avenue, Takoradi',
                'city': 'Takoradi',
                'region': 'Western',
                'nearest_institution': 'Takoradi Technical University',
                'distance_to_campus': Decimal('3.50'),
                'walking_time_estimate': 40,
                'nearby_landmarks': 'Anaji Choice Mart, Takoradi Mall',
                'total_area': Decimal('390.00'),
                'total_floors': 2,
                'house_rules': 'Quiet hours 9:30 PM. Maintain compound gardens. Keep trash inside designated bins only.',
                'cancellation_policy': 'Flexible. Refundable with 14 days notice.',
                'target_rating': 5.0,
                'reviews_count': 3,
                'ratings_list': [5, 5, 5],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Consistent Water Supply', 'Car Parking', 'CCTV Surveillance', 'Water Reservoir'],
                'proximity_destinations': [
                    ('Choice Mart Supermarket', 'SHOPPING', Decimal('0.60'), 8, 'WALK'),
                    ('TTU Campus Gate', 'INSTITUTION', Decimal('3.50'), 8, 'DRIVE')
                ],
                'pricing_configs': [
                    {'name': '1-Bedroom Garden Flat', 'bedrooms': 1, 'bathrooms': 1, 'price': Decimal('2500.00')},
                    {'name': '2-Bedroom Garden Flat', 'bedrooms': 2, 'bathrooms': 2, 'price': Decimal('4200.00')}
                ],
                'img_type': 'APARTMENT'
            },
            # 9. Tema Community 6 Apartments (Tema) - 4.6 / 5.0
            {
                'property_code': 'APT-TEM-009',
                'title': 'Tema Community 6 Apartments',
                'property_type': 'APARTMENT',
                'property_category': 'RESIDENTIAL',
                'description': 'Modern, high-security residential flats located in the quiet suburbs of Community 6, Tema. Featuring secure walls, air conditioning in all rooms, water storage, and secure parking.',
                'address': 'Community 6 High Street, Tema',
                'city': 'Tema',
                'region': 'Greater Accra',
                'nearest_institution': 'Regional Maritime University',
                'distance_to_campus': Decimal('6.00'),
                'walking_time_estimate': 70,
                'nearby_landmarks': 'Tema General Hospital, Comm 6 Park, Tema Harbour',
                'total_area': Decimal('340.00'),
                'total_floors': 3,
                'house_rules': 'Quiet hours 10 PM. No loud parking lot noises. Waste bins must be rolled out on pickup days.',
                'cancellation_policy': 'Standard lease terms. Deposit non-refundable on early break.',
                'target_rating': 4.6,
                'reviews_count': 5,
                'ratings_list': [5, 5, 5, 4, 4],
                'amenities': ['High-Speed Internet', '24/7 Security', 'Consistent Water Supply', 'Air Conditioning', 'Car Parking', 'CCTV Surveillance'],
                'proximity_destinations': [
                    ('Tema General Hospital', 'HOSPITAL', Decimal('1.20'), 15, 'WALK'),
                    ('Tema Harbour Comm 1 Stop', 'TRANSPORT', Decimal('3.00'), 10, 'TROTRO')
                ],
                'pricing_configs': [
                    {'name': '1-Bedroom Standard Flat', 'bedrooms': 1, 'bathrooms': 1, 'price': Decimal('2900.00')},
                    {'name': '2-Bedroom Executive Flat', 'bedrooms': 2, 'bathrooms': 2, 'price': Decimal('4800.00')}
                ],
                'img_type': 'APARTMENT'
            },
            # 10. Maritime Harbour Hostel (Tema) - 4.0 / 5.0
            {
                'property_code': 'HST-TEM-010',
                'title': 'Maritime Harbour Hostel',
                'property_type': 'HOSTEL',
                'property_category': 'STUDENT_HOUSING',
                'description': 'Located in immediate proximity to the Regional Maritime University, this student hostel is custom-built for cadets and maritime engineering students seeking discipline, security, and regular utilities.',
                'address': 'Harbour Road near RMU, Tema',
                'city': 'Tema',
                'region': 'Greater Accra',
                'nearest_institution': 'Regional Maritime University',
                'distance_to_campus': Decimal('0.30'),
                'walking_time_estimate': 4,
                'nearby_landmarks': 'Regional Maritime University, Nungua Barrier, Harbour Gate',
                'total_area': Decimal('1600.00'),
                'total_floors': 4,
                'hostel_type': 'MIXED',
                'ownership_type': 'PRIVATE',
                'house_rules': 'Strict check-in rules. Cadet dress codes respected in common areas. Lock-in hours apply.',
                'cancellation_policy': 'Refundable only on official academic deferrals.',
                'target_rating': 4.0,
                'reviews_count': 3,
                'ratings_list': [4, 4, 4],
                'amenities': ['24/7 Security', 'Consistent Water Supply', 'Study Areas', 'Ceiling Fan', 'Gated Access', 'Water Reservoir'],
                'proximity_destinations': [
                    ('Regional Maritime Main Gate', 'INSTITUTION', Decimal('0.30'), 4, 'WALK'),
                    ('Nungua Comm 18 Market', 'MARKET', Decimal('2.50'), 10, 'TROTRO')
                ],
                'pricing_configs': [
                    {'name': '2-in-a-room Shared Cadet', 'beds': 2, 'price': Decimal('2200.00'), 'occupancy': 'DOUBLE'},
                    {'name': '3-in-a-room Shared Cadet', 'beds': 3, 'price': Decimal('1600.00'), 'occupancy': 'TRIPLE'}
                ],
                'img_type': 'HOSTEL'
            }
        ]

        # 5. DB Population execution
        with transaction.atomic():
            for p_data in properties_data:
                # Remove existing property with this code if it exists
                Property.objects.filter(property_code=p_data['property_code']).delete()
                
                # Create property
                property_obj = Property.objects.create(
                    uploaded_by=admin_user,
                    property_code=p_data['property_code'],
                    property_type=p_data['property_type'],
                    property_category=p_data['property_category'],
                    title=p_data['title'],
                    description=p_data['description'],
                    address=p_data['address'],
                    city=p_data['city'],
                    region=p_data['region'],
                    country='Ghana',
                    digital_address=f"GH-{p_data['city'][:3].upper()}-{random.randint(1000, 9999)}",
                    latitude=Decimal(f"5.{random.randint(6000, 9000)}"),
                    longitude=Decimal(f"-0.{random.randint(1000, 3000)}"),
                    nearest_institution=p_data['nearest_institution'],
                    distance_to_campus=p_data['distance_to_campus'],
                    walking_time_estimate=p_data['walking_time_estimate'],
                    nearby_landmarks=p_data['nearby_landmarks'],
                    suitable_for_students=True,
                    suitable_for_workers=True,
                    hostel_type=p_data.get('hostel_type', ''),
                    ownership_type=p_data.get('ownership_type', ''),
                    total_area=p_data['total_area'],
                    total_floors=p_data['total_floors'],
                    is_available=True,
                    house_rules=p_data['house_rules'],
                    cancellation_policy=p_data['cancellation_policy'],
                    is_verified=True,
                    safety_score=8,
                    fire_safety_compliance=True,
                    is_featured=(p_data['property_code'] == 'HST-ACC-001'),
                    status='APPROVED',
                    security_personnel=True,
                    cctv=True,
                    gated_community=True,
                    water_availability='24/7',
                    electricity_stability='Stable',
                    internet_availability='High-speed',
                    utility_billing_method='INCLUDED_IN_RENT'
                )

                # Attach amenities
                for a_name in p_data['amenities']:
                    amenity_obj = amenity_map[a_name]
                    PropertyAmenity.objects.create(
                        accommodation_property=property_obj,
                        amenity=amenity_obj,
                        is_included=True
                    )

                # Set rental duration
                RentalDuration.objects.get_or_create(
                    accommodation_property=property_obj,
                    duration_type='LONG_TERM_LEASE',
                    defaults={
                        'semester_available': (p_data['property_type'] == 'HOSTEL'),
                        'one_year_available': True,
                        'required_advance': 'ONE_YEAR'
                    }
                )

                # Attach proximity destinations
                for name, d_type, dist, minutes, mode in p_data['proximity_destinations']:
                    ProximityDestination.objects.create(
                        accommodation_property=property_obj,
                        destination_name=name,
                        destination_type=d_type,
                        distance_km=dist,
                        travel_time_minutes=minutes,
                        travel_mode=mode
                    )

                # Attach property images from user folder
                # We select images depending on property type
                src_list = hostel_images if p_data['img_type'] == 'HOSTEL' else (villa_images if p_data['img_type'] == 'VILLA' else apt_images)
                
                # Check for backup/empty folders
                if not src_list:
                    src_list = apt_images + hostel_images + compound_images + villa_images
                
                # 1. Primary Exterior Image
                primary_src = src_list[0] if src_list else None
                if primary_src:
                    rel_path = copy_image(primary_src, 'property_images', f"{p_data['property_code']}_ext")
                    if rel_path:
                        PropertyImage.objects.create(
                            accommodation_property=property_obj,
                            image=rel_path,
                            image_type='EXTERIOR',
                            caption=f'Main exterior facade of {p_data["title"]}',
                            is_primary=True,
                            order=0
                        )

                # 2. Kitchen Image
                kitchen_src = kitchen_images[0] if kitchen_images else None
                if kitchen_src:
                    rel_path = copy_image(kitchen_src, 'property_images', f"{p_data['property_code']}_kit")
                    if rel_path:
                        PropertyImage.objects.create(
                            accommodation_property=property_obj,
                            image=rel_path,
                            image_type='KITCHEN',
                            caption=f'Fully equipped kitchen at {p_data["title"]}',
                            is_primary=False,
                            order=1
                        )

                # 3. Bathroom Image
                bathroom_src = bathroom_images[0] if bathroom_images else None
                if bathroom_src:
                    rel_path = copy_image(bathroom_src, 'property_images', f"{p_data['property_code']}_bath")
                    if rel_path:
                        PropertyImage.objects.create(
                            accommodation_property=property_obj,
                            image=rel_path,
                            image_type='BATHROOM',
                            caption=f'Sanitary clean washrooms at {p_data["title"]}',
                            is_primary=False,
                            order=2
                        )

                # 4. Interior/Interior room image
                interior_src = src_list[1 % len(src_list)] if len(src_list) > 1 else None
                if interior_src:
                    rel_path = copy_image(interior_src, 'property_images', f"{p_data['property_code']}_int")
                    if rel_path:
                        PropertyImage.objects.create(
                            accommodation_property=property_obj,
                            image=rel_path,
                            image_type='INTERIOR',
                            caption=f'Lounge area inside {p_data["title"]}',
                            is_primary=False,
                            order=3
                        )

                # Create room types or unit types
                if p_data['property_type'] == 'HOSTEL':
                    for room_conf in p_data['pricing_configs']:
                        room_type = RoomType.objects.create(
                            accommodation_property=property_obj,
                            room_type_name=room_conf['name'],
                            billing_model='SEMESTER_BASED',
                            occupancy_type=room_conf['occupancy'],
                            total_rooms=5,
                            beds_per_room=room_conf['beds'],
                            total_capacity=5 * room_conf['beds'],
                            available_slots=5 * room_conf['beds'],
                            study_desk_available=True,
                            wardrobe_available=True,
                            air_conditioning=(p_data['property_code'] == 'HST-KMS-004'),
                            fan=True,
                            wifi_available=True,
                            private_bathroom=True,
                            gender_restriction='ANY',
                            preferred_lifestyle='BALANCED',
                            study_environment_rating=4
                        )

                        # Create Room Pricing
                        RoomTypePricing.objects.create(
                            room_type=room_type,
                            payment_type='SEMESTER',
                            semester_price=room_conf['price'],
                            academic_year_price=room_conf['price'] * 2 - 200,
                            security_deposit=Decimal('200.00'),
                            currency='GHS'
                        )

                        # Create actual physical rooms & attach room image
                        for i in range(1, 6):
                            occupancy_code = room_conf['occupancy'][:3].upper()
                            physical_room = Room.objects.create(
                                accommodation_property=property_obj,
                                room_type=room_type,
                                room_number=f"RM-{occupancy_code}-{i:02d}",
                                floor=str((i // 3) + 1),
                                total_slots=room_conf['beds'],
                                occupied_slots=0,
                                pending_slots=0,
                                status='AVAILABLE'
                            )

                            # Copy room image from HOSTELS folder for this specific room
                            room_img_src = src_list[(i + 2) % len(src_list)] if src_list else None
                            if room_img_src:
                                r_rel_path = copy_image(room_img_src, 'room_images', f"{p_data['property_code']}_rm_{occupancy_code}_{i}")
                                if r_rel_path:
                                    RoomImage.objects.create(
                                        room=physical_room,
                                        image=r_rel_path,
                                        image_type='BEDROOM',
                                        is_primary=(i == 1)
                                    )
                else:
                    # Apartment or Villa
                    for unit_conf in p_data['pricing_configs']:
                        unit_type = UnitType.objects.create(
                            accommodation_property=property_obj,
                            unit_name=unit_conf['name'],
                            billing_model='MONTHLY_BASED',
                            number_of_units=3,
                            bedrooms=unit_conf['bedrooms'],
                            bathrooms=unit_conf['bathrooms'],
                            kitchen=1,
                            total_units=3,
                            available_units=3,
                            furnished_status='FURNISHED',
                            air_conditioning=True,
                            fan=True,
                            water_heater=True,
                            refrigerator=True,
                            washing_machine=True,
                            television=True,
                            internet=True
                        )

                        # Create Unit Pricing
                        UnitTypePricing.objects.create(
                            unit_type=unit_type,
                            payment_type='MONTHLY',
                            monthly_price=unit_conf['price'],
                            security_deposit=unit_conf['price'] * Decimal('0.5'),
                            currency='GHS'
                        )

                        # Create physical rooms (representing individual flats)
                        for i in range(1, 4):
                            config_code = unit_conf['name'][:3].upper().replace(' ', '')
                            physical_room = Room.objects.create(
                                accommodation_property=property_obj,
                                unit_type=unit_type,
                                room_number=f"APT-{config_code}-{i:02d}",
                                floor=str(i),
                                total_slots=1,
                                occupied_slots=0,
                                pending_slots=0,
                                status='AVAILABLE'
                            )

                            # Copy room image from APARTMENT folder
                            room_img_src = src_list[(i + 2) % len(src_list)] if src_list else None
                            if room_img_src:
                                r_rel_path = copy_image(room_img_src, 'room_images', f"{p_data['property_code']}_apt_{config_code}_{i}")
                                if r_rel_path:
                                    RoomImage.objects.create(
                                        room=physical_room,
                                        image=r_rel_path,
                                        image_type='BEDROOM',
                                        is_primary=(i == 1)
                                    )

                # Attach review ratings
                for idx, rating_val in enumerate(p_data['ratings_list']):
                    reviewer_user = student_users[idx % len(student_users)]
                    
                    # Create dummy booking to satisfy unique constraint and model check
                    booking_obj = Booking.objects.create(
                        tenant=reviewer_user,
                        accommodation_property=property_obj,
                        move_in_date=timezone.now().date(),
                        move_out_date=timezone.now().date() + timezone.timedelta(days=120),
                        status='COMPLETED',
                        billing_model='SEMESTER_BASED' if p_data['property_type'] == 'HOSTEL' else 'MONTHLY_BASED',
                        total_amount=Decimal('4000.00'),
                        payment_status='PAID'
                    )

                    Review.objects.create(
                        reviewer=reviewer_user,
                        accommodation_property=property_obj,
                        booking=booking_obj,
                        review_type='PROPERTY',
                        status='APPROVED',
                        rating=rating_val,
                        cleanliness_rating=rating_val,
                        location_rating=rating_val,
                        amenities_rating=rating_val,
                        communication_rating=rating_val,
                        value_rating=rating_val,
                        title=f'Exceptional Stay at {p_data["title"]}',
                        content=f'I stayed here last semester and the facilities were top notch. {p_data["description"][:100]}...',
                        guest_type='STUDENT',
                        recommendation='DEFINITELY',
                        would_stay_again='DEFINITELY',
                        is_verified=True,
                        verification_level='VERIFIED_GUEST'
                    )

                self.stdout.write(self.style.SUCCESS(f'Successfully completed populating: {p_data["title"]} ({p_data["property_code"]}) with average rating {property_obj.average_rating:.1f}/5.0'))

        self.stdout.write(self.style.SUCCESS('Finished loading all 10 properties successfully!'))
