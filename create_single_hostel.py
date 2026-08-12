import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from properties.models import (
    Property, PropertyImage, RoomType, RoomTypePricing, 
    Amenity, PropertyAmenity, Room, RoomImage, ProximityDestination
)
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

print("Purging all existing properties to keep ONLY ONE single hostel...")
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

# Create the Single Hostel Property
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

# Add Amenities
for am in [wifi, security, water, ac, study, generator]:
    PropertyAmenity.objects.get_or_create(accommodation_property=hostel, amenity=am, defaults={'is_included': True})

# Property Gallery Images
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

# Room Types
rt_single = RoomType.objects.create(
    accommodation_property=hostel,
    room_type_name="Single Deluxe Room (1 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="SINGLE",
    total_rooms=10,
    beds_per_room=1,
    total_capacity=10,
    available_slots=5,
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

rt_double = RoomType.objects.create(
    accommodation_property=hostel,
    room_type_name="Double Standard Room (2 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="DOUBLE",
    total_rooms=15,
    beds_per_room=2,
    total_capacity=30,
    available_slots=12,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1:2",
    gender_restriction="ANY"
)
RoomTypePricing.objects.create(
    room_type=rt_double,
    payment_type="SEMESTER",
    semester_price=2800.00
)

rt_quad = RoomType.objects.create(
    accommodation_property=hostel,
    room_type_name="Quad Standard Room (4 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="QUAD",
    total_rooms=20,
    beds_per_room=4,
    total_capacity=80,
    available_slots=25,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    bed_type="BUNK",
    gender_restriction="ANY"
)
RoomTypePricing.objects.create(
    room_type=rt_quad,
    payment_type="SEMESTER",
    semester_price=1950.00
)

# Physical Rooms & Room Images
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

r102 = Room.objects.create(
    accommodation_property=hostel,
    room_type=rt_double,
    room_number="102",
    floor="1st Floor",
    total_slots=2,
    occupied_slots=1,
    status="PARTIALLY_OCCUPIED"
)
RoomImage.objects.create(room=r102, image="property_images/hostel_room_2.jpeg", image_type="BEDROOM", is_primary=True)

r103 = Room.objects.create(
    accommodation_property=hostel,
    room_type=rt_quad,
    room_number="103",
    floor="1st Floor",
    total_slots=4,
    occupied_slots=1,
    status="PARTIALLY_OCCUPIED"
)
RoomImage.objects.create(room=r103, image="property_images/hostel_room_3.jpeg", image_type="BEDROOM", is_primary=True)

# Proximity Destinations
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

print(f"SUCCESS! Purged all properties. Single hostel created: {hostel.title} (ID: {hostel.id})")
