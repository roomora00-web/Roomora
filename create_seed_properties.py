import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from properties.models import (
    Property, PropertyImage, RoomType, RoomTypePricing, 
    UnitType, UnitTypePricing, Amenity, PropertyAmenity
)
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

print("Clearing old properties...")
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

# 1. Pentecost Executive Hostel
p1 = Property.objects.create(
    title="Pentecost Executive Hostel",
    property_code="HST-KMS-001",
    property_type="HOSTEL",
    property_category="STUDENT_HOUSING",
    description="Modern premium student hostel located 5 minutes from KNUST campus. Features high-speed Wi-Fi, 24/7 security, air-conditioned rooms, and study lounges.",
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
    hostel_type="MIXED",
    ownership_type="PRIVATE",
    total_area=450.0,
    is_available=True,
    is_verified=True,
    is_featured=True,
    status="APPROVED",
    uploaded_by=admin_user,
)

PropertyAmenity.objects.get_or_create(accommodation_property=p1, amenity=wifi, defaults={'is_included': True})
PropertyAmenity.objects.get_or_create(accommodation_property=p1, amenity=security, defaults={'is_included': True})
PropertyAmenity.objects.get_or_create(accommodation_property=p1, amenity=water, defaults={'is_included': True})
PropertyAmenity.objects.get_or_create(accommodation_property=p1, amenity=ac, defaults={'is_included': True})

PropertyImage.objects.create(
    accommodation_property=p1,
    image="property_images/hostel_4_0.jpg",
    image_type="EXTERIOR",
    is_primary=True,
    order=1
)

rt1 = RoomType.objects.create(
    accommodation_property=p1,
    room_type_name="Single Deluxe Room",
    billing_model="SEMESTER_BASED",
    occupancy_type="SINGLE",
    total_rooms=10,
    total_capacity=10,
    available_slots=5,
    air_conditioning=True,
    wifi_available=True,
    private_bathroom=True
)

RoomTypePricing.objects.create(
    room_type=rt1,
    payment_type="SEMESTER",
    semester_price=3500.00
)

# 2. Emerald Heights Executive Apartment
p2 = Property.objects.create(
    title="Emerald Heights Executive Apartment",
    property_code="APT-ACC-002",
    property_type="APARTMENT",
    property_category="RESIDENTIAL",
    description="Luxury 2-bedroom executive apartment featuring scenic views, contemporary interior finishes, gated security, and backup generator.",
    address="Ring Road Central, Cantonments",
    city="Accra",
    region="Greater Accra",
    country="Ghana",
    digital_address="GA-098-7654",
    latitude=5.560000,
    longitude=-0.180000,
    nearest_institution="University of Ghana",
    distance_to_campus=2.5,
    walking_time_estimate=15,
    suitable_for_students=True,
    suitable_for_workers=True,
    total_area=120.0,
    is_available=True,
    is_verified=True,
    is_featured=True,
    status="APPROVED",
    uploaded_by=admin_user,
)

PropertyAmenity.objects.get_or_create(accommodation_property=p2, amenity=wifi, defaults={'is_included': True})
PropertyAmenity.objects.get_or_create(accommodation_property=p2, amenity=security, defaults={'is_included': True})
PropertyAmenity.objects.get_or_create(accommodation_property=p2, amenity=ac, defaults={'is_included': True})

PropertyImage.objects.create(
    accommodation_property=p2,
    image="property_images/apt_1.jpg",
    image_type="EXTERIOR",
    is_primary=True,
    order=1
)

ut1 = UnitType.objects.create(
    accommodation_property=p2,
    unit_name="2-Bedroom Executive Suite",
    billing_model="MONTHLY_BASED",
    number_of_units=5,
    bedrooms=2,
    bathrooms=2,
    total_units=5,
    available_units=3,
    furnished_status="FURNISHED",
    air_conditioning=True,
    internet=True
)

UnitTypePricing.objects.create(
    unit_type=ut1,
    payment_type="MONTHLY",
    monthly_price=2500.00
)

print(f"SUCCESS: Created properties: {[p.title for p in Property.objects.all()]}")
