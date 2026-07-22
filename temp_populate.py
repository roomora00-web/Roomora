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
