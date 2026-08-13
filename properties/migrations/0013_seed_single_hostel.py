from django.db import migrations

def seed_single_hostel_data(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    PropertyImage = apps.get_model('properties', 'PropertyImage')
    RoomType = apps.get_model('properties', 'RoomType')
    RoomTypePricing = apps.get_model('properties', 'RoomTypePricing')
    Amenity = apps.get_model('properties', 'Amenity')
    PropertyAmenity = apps.get_model('properties', 'PropertyAmenity')
    Room = apps.get_model('properties', 'Room')
    RoomImage = apps.get_model('properties', 'RoomImage')
    ProximityDestination = apps.get_model('properties', 'ProximityDestination')
    User = apps.get_model('accounts', 'User')

    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

    # Purge old properties to leave single Pentecost Executive Hostel
    Property.objects.all().delete()

    def get_or_create_amenity(name, category):
        amenity = Amenity.objects.filter(name__iexact=name).first()
        if not amenity:
            amenity = Amenity.objects.create(name=name, category=category)
        return amenity

    wifi = get_or_create_amenity('Wi-Fi', 'INTERNET')
    security = get_or_create_amenity('24/7 Security', 'SAFETY')
    water = get_or_create_amenity('Water Supply', 'UTILITIES')
    ac = get_or_create_amenity('Air Conditioning', 'GENERAL')
    study = get_or_create_amenity('Study Room', 'STUDY')
    generator = get_or_create_amenity('Standby Generator', 'UTILITIES')

    hostel = Property.objects.create(
        title="Pentecost Executive Hostel",
        property_code="HST-KMS-001",
        property_type="HOSTEL",
        property_category="STUDENT_HOUSING",
        description=(
            "Pentecost Executive Hostel is a premier student residence located just 5 minutes from the KNUST main campus gate. "
            "Built to offer students the ultimate blend of comfort, safety, and academic convenience, the hostel features air-conditioned "
            "rooms, 24/7 CCTV & security personnel, ultra-fast fibre internet, uninterrupted water flow with storage reservoirs, dedicated "
            "quiet study lounges, and modern kitchenettes on every floor."
        ),
        address="Ayeduase Main Road",
        city="Kumasi",
        region="Ashanti",
        country="Ghana",
        digital_address="AK-123-4567",
        latitude=6.678500,
        longitude=-1.570800,
        nearest_institution="KNUST",
        distance_to_campus=0.5,
        walking_time_estimate=5,
        suitable_for_students=True,
        suitable_for_workers=False,
        hostel_type="MIXED",
        ownership_type="PRIVATE",
        total_area=650.0,
        total_floors=3,
        is_available=True,
        is_verified=True,
        is_featured=True,
        status="APPROVED",
        owner_name="Kwame Mensah (Property Manager)",
        owner_email="manager@pentecostexecutivehostel.com",
        owner_phone="+233244123456",
        uploaded_by=admin_user,
        house_rules="1. Silence in study areas after 10 PM. 2. Visitors permitted in designated lounges between 8 AM and 8 PM.",
        cancellation_policy="Full refund if cancelled 14 days prior to semester start.",
        cctv=True,
        security_personnel=True,
        gated_community=True,
        water_availability="24/7 Continuous",
        electricity_stability="High (Backup Generator Available)",
        internet_availability="High-Speed Fibre Wi-Fi",
    )

    for am in [wifi, security, water, ac, study, generator]:
        PropertyAmenity.objects.get_or_create(accommodation_property=hostel, amenity=am, defaults={'is_included': True})

    PropertyImage.objects.create(
        accommodation_property=hostel,
        image="property_images/hostel_main_ext.jpeg",
        image_type="EXTERIOR",
        caption="Pentecost Executive Hostel Exterior View",
        is_primary=True,
        order=1
    )
    PropertyImage.objects.create(
        accommodation_property=hostel,
        image="property_images/hostel_ext_2.jpeg",
        image_type="EXTERIOR",
        caption="Hostel Entrance & Security Gate",
        is_primary=False,
        order=2
    )
    PropertyImage.objects.create(
        accommodation_property=hostel,
        image="property_images/hostel_ext_3.jpeg",
        image_type="INTERIOR",
        caption="Lounge & Corridor Area",
        is_primary=False,
        order=3
    )
    PropertyImage.objects.create(
        accommodation_property=hostel,
        image="property_images/hostel_kit_1.jpg",
        image_type="KITCHEN",
        caption="Modern Floor Kitchenette",
        is_primary=False,
        order=4
    )
    PropertyImage.objects.create(
        accommodation_property=hostel,
        image="property_images/hostel_bath_1.jpeg",
        image_type="BATHROOM",
        caption="Clean Washroom Facilities",
        is_primary=False,
        order=5
    )

    rt_single = RoomType.objects.create(
        accommodation_property=hostel,
        room_type_name="Single Deluxe Room (1 in a Room)",
        billing_model="SEMESTER_BASED",
        occupancy_type="SINGLE",
        total_rooms=1,
        beds_per_room=1,
        total_capacity=1,
        available_slots=1,
        air_conditioning=True,
        wifi_available=True,
        study_desk_available=True,
        wardrobe_available=True,
        private_bathroom=True,
        gender_restriction="ANY"
    )
    RoomTypePricing.objects.create(
        room_type=rt_single,
        payment_type="SEMESTER",
        semester_price=3800.00
    )

    r101 = Room.objects.create(
        accommodation_property=hostel,
        room_type=rt_single,
        room_number="101",
        floor="1st Floor",
        total_slots=1,
        occupied_slots=0,
        status="AVAILABLE"
    )
    RoomImage.objects.create(room=r101, image="property_images/hostel_room_1.jpeg", image_type="BEDROOM", is_primary=True)
    RoomImage.objects.create(room=r101, image="property_images/hostel_room_10.jpeg", image_type="BEDROOM", is_primary=False)
    RoomImage.objects.create(room=r101, image="property_images/hostel_kit_1.jpg", image_type="KITCHEN", is_primary=False)
    RoomImage.objects.create(room=r101, image="property_images/hostel_bath_1.jpeg", image_type="WASHROOM", is_primary=False)

    rt_double = RoomType.objects.create(
        accommodation_property=hostel,
        room_type_name="Double Standard Room (2 in a Room)",
        billing_model="SEMESTER_BASED",
        occupancy_type="DOUBLE",
        total_rooms=1,
        beds_per_room=2,
        total_capacity=2,
        available_slots=2,
        fan=True,
        wifi_available=True,
        study_desk_available=True,
        wardrobe_available=True,
        private_bathroom=False,
        gender_restriction="ANY"
    )
    RoomTypePricing.objects.create(
        room_type=rt_double,
        payment_type="SEMESTER",
        semester_price=2800.00
    )

    r102 = Room.objects.create(
        accommodation_property=hostel,
        room_type=rt_double,
        room_number="102",
        floor="1st Floor",
        total_slots=2,
        occupied_slots=0,
        status="AVAILABLE"
    )
    RoomImage.objects.create(room=r102, image="property_images/hostel_room_4.jpeg", image_type="BEDROOM", is_primary=True)
    RoomImage.objects.create(room=r102, image="property_images/hostel_room_5.jpeg", image_type="BEDROOM", is_primary=False)
    RoomImage.objects.create(room=r102, image="property_images/hostel_kit_2.webp", image_type="KITCHEN", is_primary=False)
    RoomImage.objects.create(room=r102, image="property_images/hostel_bath_2.jpeg", image_type="WASHROOM", is_primary=False)

    ProximityDestination.objects.create(
        accommodation_property=hostel,
        destination_name="KNUST Commercial Area",
        destination_type="SHOPPING",
        distance_km=0.4,
        travel_time_minutes=4,
        travel_mode="WALK",
        order=1
    )
    ProximityDestination.objects.create(
        accommodation_property=hostel,
        destination_name="Ayeduase Taxi Rank",
        destination_type="TRANSPORT",
        distance_km=0.2,
        travel_time_minutes=2,
        travel_mode="WALK",
        order=2
    )
    ProximityDestination.objects.create(
        accommodation_property=hostel,
        destination_name="KNUST Hospital",
        destination_type="HOSPITAL",
        distance_km=1.2,
        travel_time_minutes=5,
        travel_mode="TAXI",
        order=3
    )

def reverse_seed(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0012_roomimage'),
    ]

    operations = [
        migrations.RunPython(seed_single_hostel_data, reverse_code=reverse_seed),
    ]
