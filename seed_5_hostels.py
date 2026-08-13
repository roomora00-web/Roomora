"""
Seed script: 5 New Hostel Properties
Using images from Properties00/HOSTELS/
Each property gets: full details, amenities, property images, 2 room types, physical rooms, room images, proximity destinations.
"""

import os
import sys
import shutil
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

# ─── Image Copy Helpers ────────────────────────────────────────────────────────
SRC_DIR = os.path.join(os.path.dirname(__file__), "Properties00", "HOSTELS")
MEDIA_PROP = os.path.join(os.path.dirname(__file__), "media", "property_images")
MEDIA_ROOM = os.path.join(os.path.dirname(__file__), "media", "room_images")
os.makedirs(MEDIA_PROP, exist_ok=True)
os.makedirs(MEDIA_ROOM, exist_ok=True)

def copy_prop_image(src_filename, dest_filename):
    """Copy from Properties00/HOSTELS → media/property_images/ and return DB path."""
    src = os.path.join(SRC_DIR, src_filename)
    dst = os.path.join(MEDIA_PROP, dest_filename)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  [IMG] Copied property image: {dest_filename}")
    else:
        print(f"  [WARN] Source not found: {src}")
    return f"property_images/{dest_filename}"

def copy_room_image(src_filename, dest_filename):
    """Copy from Properties00/HOSTELS → media/room_images/ and return DB path."""
    src = os.path.join(SRC_DIR, src_filename)
    dst = os.path.join(MEDIA_ROOM, dest_filename)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  [IMG] Copied room image: {dest_filename}")
    else:
        print(f"  [WARN] Source not found: {src}")
    return f"room_images/{dest_filename}"

# ─── Amenity Helper ────────────────────────────────────────────────────────────
def get_or_create_amenity(name, category):
    amenity, _ = Amenity.objects.get_or_create(name__iexact=name, defaults={'name': name, 'category': category})
    return amenity

# Common amenities
wifi        = get_or_create_amenity('Wi-Fi', 'INTERNET')
security    = get_or_create_amenity('24/7 Security', 'SAFETY')
water       = get_or_create_amenity('Water Supply', 'UTILITIES')
ac          = get_or_create_amenity('Air Conditioning', 'GENERAL')
study       = get_or_create_amenity('Study Room', 'STUDY')
generator   = get_or_create_amenity('Standby Generator', 'UTILITIES')
laundry     = get_or_create_amenity('Laundry Service', 'LAUNDRY')
cctv_am     = get_or_create_amenity('CCTV Surveillance', 'SAFETY')
kitchen_am  = get_or_create_amenity('Communal Kitchen', 'KITCHEN')
fence_am    = get_or_create_amenity('Perimeter Fence & Gate', 'SAFETY')
fan_am      = get_or_create_amenity('Ceiling Fan', 'GENERAL')
parking_am  = get_or_create_amenity('Car Parking', 'OUTDOOR')

def add_amenities(prop, amenity_list):
    for am in amenity_list:
        PropertyAmenity.objects.get_or_create(
            accommodation_property=prop, amenity=am, defaults={'is_included': True}
        )

print("\n" + "="*70)
print("SEEDING 5 NEW HOSTEL PROPERTIES")
print("="*70)

# ══════════════════════════════════════════════════════════════════════════════
# HOSTEL 1 — Millennium Light Hostel (Accra / Legon)
# Exterior: images (18).jpeg  | Rooms: images (1).jpeg, images (4).jpeg
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1/5] Creating Millennium Light Hostel (Accra)...")

if Property.objects.filter(property_code="HST-ACC-MLH-001").exists():
    Property.objects.filter(property_code="HST-ACC-MLH-001").delete()
    print("  [DEL] Removed existing HST-ACC-MLH-001")

h1 = Property.objects.create(
    title="Millennium Light Hostel",
    property_code="HST-ACC-MLH-001",
    property_type="HOSTEL",
    property_category="STUDENT_HOUSING",
    description=(
        "Millennium Light Hostel is a well-established student residence situated just 3 minutes on foot from "
        "the University of Ghana (Legon) main campus. The hostel's iconic terracotta-painted four-storey building "
        "accommodates both male and female students in a safe, structured environment. Facilities include a "
        "24-hour security post, secure perimeter wall with razor-wire fencing, a gated compound, borehole water "
        "with overhead storage tanks, standby generator for uninterrupted power, and reliable Wi-Fi connectivity "
        "throughout all floors. Clean communal washrooms are maintained by dedicated hostel staff. "
        "The ground floor houses a convenience store and a printing centre for students."
    ),
    address="Legon Campus Road, Behind Volta Hall",
    city="Accra",
    region="Greater Accra",
    country="Ghana",
    digital_address="GA-489-2231",
    latitude=5.648900,
    longitude=-0.187100,
    nearest_institution="University of Ghana (Legon)",
    distance_to_campus=0.3,
    walking_time_estimate=3,
    nearby_landmarks="Volta Hall, Commonwealth Hall, Legon Botanical Gardens",
    suitable_for_students=True,
    suitable_for_workers=False,
    suitable_for_national_service=True,
    hostel_type="MIXED",
    ownership_type="PRIVATE",
    total_area=820.0,
    total_floors=4,
    is_available=True,
    is_verified=True,
    is_featured=True,
    status="APPROVED",
    owner_name="Nana Kofi Asante",
    owner_email="manager@millenniumlighthostel.com",
    owner_phone="+233 20 811 4422",
    uploaded_by=admin_user,
    house_rules=(
        "• Quiet hours strictly observed from 10:00 PM — 6:00 AM daily.\n"
        "• All tenants must carry their ID card at all times within the compound.\n"
        "• Communal areas (washrooms, corridors) must be left clean after use.\n"
        "• Cooking is only permitted in designated kitchenette areas on each floor.\n"
        "• Electricity must be conserved — lights and fans off when leaving the room."
    ),
    visitor_policy=(
        "• Visitors are permitted between 8:00 AM and 7:00 PM only.\n"
        "• All visitors must sign in at the security desk and collect a visitor pass.\n"
        "• Visitors are not permitted beyond the ground-floor common area.\n"
        "• Overnight stays by visitors are strictly prohibited."
    ),
    prohibited_items=(
        "• NO smoking, alcohol, or illicit substances anywhere on premises.\n"
        "• NO pets of any kind.\n"
        "• NO gas cylinders, hot plates, or open-flame cooking in rooms.\n"
        "• NO electrical appliances above 1000W (e.g., electric irons must be used in laundry room).\n"
        "• NO loud music or noise after 10:00 PM."
    ),
    emergency_contacts=(
        "• Hostel Security Desk (24/7): +233 20 811 4422\n"
        "• Hostel Manager (Nana Kofi): +233 20 811 4422\n"
        "• Legon Campus Security: +233 30 250 0392\n"
        "• Ghana Police Service (Legon): 191 / 112\n"
        "• National Fire Service: 192"
    ),
    cancellation_policy="Full refund if cancelled 14 days before semester start. 50% refund within 7 days.",
    cctv=True,
    security_personnel=True,
    gated_community=True,
    water_availability="Borehole with Overhead Tank (24/7)",
    electricity_stability="High (Backup Generator Available)",
    internet_availability="Fibre Wi-Fi — All Floors",
    utility_billing_method="INCLUDED_IN_RENT",
    fire_safety_compliance=True,
    safety_score=8,
    smoking_allowed=False,
    pets_allowed=False,
    guests_allowed=True,
    maximum_guests=2,
)

add_amenities(h1, [wifi, security, water, generator, cctv_am, fence_am, kitchen_am, fan_am])

# Property images
PropertyImage.objects.create(
    accommodation_property=h1,
    image=copy_prop_image("images (18).jpeg", "HST-ACC-MLH-001_ext_main.jpeg"),
    image_type="EXTERIOR", caption="Millennium Light Hostel — Front View", is_primary=True, order=1
)
PropertyImage.objects.create(
    accommodation_property=h1,
    image=copy_prop_image("images (7).jpeg", "HST-ACC-MLH-001_ext_2.jpeg"),
    image_type="EXTERIOR", caption="Hostel Exterior & Gated Compound", is_primary=False, order=2
)
PropertyImage.objects.create(
    accommodation_property=h1,
    image=copy_prop_image("images (17).jpeg", "HST-ACC-MLH-001_int_corridor.jpeg"),
    image_type="INTERIOR", caption="Clean Hostel Corridor", is_primary=False, order=3
)
PropertyImage.objects.create(
    accommodation_property=h1,
    image=copy_prop_image("images (11).jpeg", "HST-ACC-MLH-001_int_room.jpeg"),
    image_type="INTERIOR", caption="Typical Hostel Room Interior", is_primary=False, order=4
)

# Room Type 1: Single (1 in a room)
rt_h1_single = RoomType.objects.create(
    accommodation_property=h1,
    room_type_name="Single Room (1 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="SINGLE",
    total_rooms=15,
    beds_per_room=1,
    total_capacity=15,
    available_slots=15,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 4 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="ACADEMIC_FOCUSED",
    study_environment_rating=4,
)
RoomTypePricing.objects.create(
    room_type=rt_h1_single,
    payment_type="SEMESTER",
    semester_price=2800.00,
    monthly_price=700.00,
    security_deposit=500.00,
    registration_fee=150.00,
    currency="GHS",
)

# Room Type 2: Double (2 in a room)
rt_h1_double = RoomType.objects.create(
    accommodation_property=h1,
    room_type_name="Double Room (2 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="DOUBLE",
    total_rooms=20,
    beds_per_room=2,
    total_capacity=40,
    available_slots=40,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 3 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="BALANCED",
    study_environment_rating=3,
)
RoomTypePricing.objects.create(
    room_type=rt_h1_double,
    payment_type="SEMESTER",
    semester_price=1800.00,
    monthly_price=450.00,
    security_deposit=300.00,
    registration_fee=100.00,
    currency="GHS",
)

# Physical Rooms
r_h1_s01 = Room.objects.create(
    accommodation_property=h1, room_type=rt_h1_single,
    room_number="S101", floor="1st Floor", total_slots=1, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h1_s01, image=copy_room_image("images (19).jpeg", "HST-ACC-MLH-001_rm_S101_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h1_s01, image=copy_room_image("images (11).jpeg", "HST-ACC-MLH-001_rm_S101_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h1_d01 = Room.objects.create(
    accommodation_property=h1, room_type=rt_h1_double,
    room_number="D201", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h1_d01, image=copy_room_image("images (1).jpeg", "HST-ACC-MLH-001_rm_D201_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h1_d01, image=copy_room_image("images (4).jpeg", "HST-ACC-MLH-001_rm_D201_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h1_d02 = Room.objects.create(
    accommodation_property=h1, room_type=rt_h1_double,
    room_number="D202", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h1_d02, image=copy_room_image("images (3).jpeg", "HST-ACC-MLH-001_rm_D202_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h1_d02, image=copy_room_image("images (5).jpeg", "HST-ACC-MLH-001_rm_D202_2.jpeg"), image_type="BEDROOM", is_primary=False)

# Proximity
ProximityDestination.objects.create(accommodation_property=h1, destination_name="University of Ghana Main Gate", destination_type="INSTITUTION", distance_km=0.3, travel_time_minutes=3, travel_mode="WALK", order=1)
ProximityDestination.objects.create(accommodation_property=h1, destination_name="Legon Market", destination_type="MARKET", distance_km=0.8, travel_time_minutes=8, travel_mode="WALK", order=2)
ProximityDestination.objects.create(accommodation_property=h1, destination_name="UG Hospital", destination_type="HOSPITAL", distance_km=1.0, travel_time_minutes=5, travel_mode="TAXI", order=3)
ProximityDestination.objects.create(accommodation_property=h1, destination_name="Atomic Junction Bus Stop", destination_type="TRANSPORT", distance_km=2.5, travel_time_minutes=8, travel_mode="TROTRO", order=4)

print(f"  [OK] {h1.title} created successfully.")


# ══════════════════════════════════════════════════════════════════════════════
# HOSTEL 2 — Pink Rose Student Hostel (Accra / Madina)
# Exterior: images (8).jpeg (pink building) | Rooms: images (9).jpeg, images (6).jpeg
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2/5] Creating Pink Rose Student Hostel (Accra / Madina)...")

if Property.objects.filter(property_code="HST-ACC-PRH-002").exists():
    Property.objects.filter(property_code="HST-ACC-PRH-002").delete()
    print("  [DEL] Removed existing HST-ACC-PRH-002")

h2 = Property.objects.create(
    title="Pink Rose Student Hostel",
    property_code="HST-ACC-PRH-002",
    property_type="HOSTEL",
    property_category="STUDENT_HOUSING",
    description=(
        "Pink Rose Student Hostel is a vibrant, three-floor student residence located in Madina, approximately "
        "10 minutes by trotro from the University of Ghana, Legon. The distinctively painted pink building is "
        "a well-known landmark in the community. The hostel caters primarily to female students, offering a "
        "safe, comfortable environment with 24-hour female-only security personnel, perimeter fencing, borehole "
        "water, and consistent power backed by a diesel generator. Communal kitchenettes are provided on each "
        "floor, and Wi-Fi is available across the building. The hostel offers a peaceful study atmosphere and "
        "is walking distance to Madina Market, pharmacies, and major transport routes to Legon and Accra CBD."
    ),
    address="Kotobabi Road, Near Madina Market",
    city="Madina",
    region="Greater Accra",
    country="Ghana",
    digital_address="GA-721-5543",
    latitude=5.681200,
    longitude=-0.166900,
    nearest_institution="University of Ghana (Legon)",
    distance_to_campus=4.5,
    walking_time_estimate=55,
    nearby_landmarks="Madina Market, Madina Zongo Junction, Accra-Madina Highway",
    suitable_for_students=True,
    suitable_for_workers=True,
    suitable_for_national_service=True,
    hostel_type="GIRLS_ONLY",
    ownership_type="PRIVATE",
    total_area=600.0,
    total_floors=3,
    is_available=True,
    is_verified=True,
    is_featured=False,
    status="APPROVED",
    owner_name="Abena Osei-Agyeman",
    owner_email="info@pinkhostelgh.com",
    owner_phone="+233 24 533 9900",
    uploaded_by=admin_user,
    house_rules=(
        "• Female residents ONLY — no male visitors allowed on upper floors under any circumstance.\n"
        "• Curfew is strictly 9:30 PM — gates are locked and re-opened at 6:00 AM.\n"
        "• Cooking permitted ONLY in kitchenette areas; no cooking in bedrooms.\n"
        "• Rooms must be swept and tidied daily. Inspections occur monthly.\n"
        "• Music and noise must be kept to minimum at all times."
    ),
    visitor_policy=(
        "• Female visitors only, permitted between 9:00 AM and 6:00 PM.\n"
        "• All visitors must register at the gate security post before entry.\n"
        "• Male visitors (fathers, brothers, delivery personnel) permitted in ground-floor reception only.\n"
        "• No overnight visitors permitted."
    ),
    prohibited_items=(
        "• NO male persons beyond the ground-floor reception area.\n"
        "• NO alcohol, smoking, or drug use on the premises.\n"
        "• NO gas cylinders or hot plates in rooms.\n"
        "• NO pets of any kind.\n"
        "• NO excessively loud music."
    ),
    emergency_contacts=(
        "• Pink Rose Security Desk (24/7): +233 24 533 9900\n"
        "• Hostel Matron (Maame Esi): +233 54 219 8876\n"
        "• Madina Police Station: +233 30 250 0800\n"
        "• Emergency: 191 / 112"
    ),
    cancellation_policy="Full refund if cancelled 10 days before semester start. No refund after move-in.",
    cctv=True,
    security_personnel=True,
    gated_community=True,
    water_availability="Borehole with Storage Tank (24/7)",
    electricity_stability="Medium (Generator backup, 20 min delay)",
    internet_availability="Wi-Fi — Ground & 1st Floor",
    utility_billing_method="INCLUDED_IN_RENT",
    fire_safety_compliance=True,
    safety_score=7,
    smoking_allowed=False,
    pets_allowed=False,
    guests_allowed=True,
    maximum_guests=1,
)

add_amenities(h2, [wifi, security, water, generator, cctv_am, fence_am, kitchen_am, fan_am, laundry])

PropertyImage.objects.create(
    accommodation_property=h2,
    image=copy_prop_image("images (8).jpeg", "HST-ACC-PRH-002_ext_main.jpeg"),
    image_type="EXTERIOR", caption="Pink Rose Hostel — Iconic Pink Building", is_primary=True, order=1
)
PropertyImage.objects.create(
    accommodation_property=h2,
    image=copy_prop_image("images (13).jpeg", "HST-ACC-PRH-002_ext_2.jpeg"),
    image_type="EXTERIOR", caption="Hostel Exterior — Side View", is_primary=False, order=2
)
PropertyImage.objects.create(
    accommodation_property=h2,
    image=copy_prop_image("images (16).jpeg", "HST-ACC-PRH-002_int_corridor.jpeg"),
    image_type="INTERIOR", caption="Well-Lit Hostel Corridor", is_primary=False, order=3
)
PropertyImage.objects.create(
    accommodation_property=h2,
    image=copy_prop_image("images (14).jpeg", "HST-ACC-PRH-002_int_room.jpeg"),
    image_type="INTERIOR", caption="Standard Bedroom Interior", is_primary=False, order=4
)

# Room types
rt_h2_single = RoomType.objects.create(
    accommodation_property=h2,
    room_type_name="Single Room (1 in a Room) — Girls Only",
    billing_model="SEMESTER_BASED",
    occupancy_type="SINGLE",
    total_rooms=10,
    beds_per_room=1,
    total_capacity=10,
    available_slots=10,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 4 Rooms",
    gender_restriction="FEMALE_ONLY",
    preferred_lifestyle="QUIET",
    study_environment_rating=4,
)
RoomTypePricing.objects.create(
    room_type=rt_h2_single,
    payment_type="SEMESTER",
    semester_price=2500.00,
    monthly_price=625.00,
    security_deposit=400.00,
    registration_fee=100.00,
    currency="GHS",
)

rt_h2_double = RoomType.objects.create(
    accommodation_property=h2,
    room_type_name="Double Room (2 in a Room) — Girls Only",
    billing_model="SEMESTER_BASED",
    occupancy_type="DOUBLE",
    total_rooms=18,
    beds_per_room=2,
    total_capacity=36,
    available_slots=36,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 3 Rooms",
    gender_restriction="FEMALE_ONLY",
    preferred_lifestyle="BALANCED",
    study_environment_rating=3,
)
RoomTypePricing.objects.create(
    room_type=rt_h2_double,
    payment_type="SEMESTER",
    semester_price=1600.00,
    monthly_price=400.00,
    security_deposit=250.00,
    registration_fee=80.00,
    currency="GHS",
)

r_h2_s01 = Room.objects.create(
    accommodation_property=h2, room_type=rt_h2_single,
    room_number="S101", floor="1st Floor", total_slots=1, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h2_s01, image=copy_room_image("images (14).jpeg", "HST-ACC-PRH-002_rm_S101_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h2_s01, image=copy_room_image("images (19).jpeg", "HST-ACC-PRH-002_rm_S101_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h2_d01 = Room.objects.create(
    accommodation_property=h2, room_type=rt_h2_double,
    room_number="D201", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h2_d01, image=copy_room_image("images (9).jpeg", "HST-ACC-PRH-002_rm_D201_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h2_d01, image=copy_room_image("images (6).jpeg", "HST-ACC-PRH-002_rm_D201_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h2_d02 = Room.objects.create(
    accommodation_property=h2, room_type=rt_h2_double,
    room_number="D202", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h2_d02, image=copy_room_image("images (15).jpeg", "HST-ACC-PRH-002_rm_D202_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h2_d02, image=copy_room_image("images (16).jpeg", "HST-ACC-PRH-002_rm_D202_2.jpeg"), image_type="BEDROOM", is_primary=False)

ProximityDestination.objects.create(accommodation_property=h2, destination_name="Madina Market", destination_type="MARKET", distance_km=0.3, travel_time_minutes=4, travel_mode="WALK", order=1)
ProximityDestination.objects.create(accommodation_property=h2, destination_name="Madina Trotro Station", destination_type="TRANSPORT", distance_km=0.5, travel_time_minutes=6, travel_mode="WALK", order=2)
ProximityDestination.objects.create(accommodation_property=h2, destination_name="Madina Polyclinic", destination_type="HOSPITAL", distance_km=1.2, travel_time_minutes=7, travel_mode="TROTRO", order=3)
ProximityDestination.objects.create(accommodation_property=h2, destination_name="University of Ghana (Legon)", destination_type="INSTITUTION", distance_km=4.5, travel_time_minutes=15, travel_mode="TROTRO", order=4)

print(f"  [OK] {h2.title} created successfully.")


# ══════════════════════════════════════════════════════════════════════════════
# HOSTEL 3 — Ayeduase Hostel Block (Kumasi / KNUST area)
# Exterior: images (2).jpeg | Rooms: images (3).jpeg, images (5).jpeg
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3/5] Creating Ayeduase Modern Hostel Block (Kumasi)...")

if Property.objects.filter(property_code="HST-KMS-AMH-003").exists():
    Property.objects.filter(property_code="HST-KMS-AMH-003").delete()
    print("  [DEL] Removed existing HST-KMS-AMH-003")

h3 = Property.objects.create(
    title="Ayeduase Modern Hostel Block",
    property_code="HST-KMS-AMH-003",
    property_type="HOSTEL",
    property_category="STUDENT_HOUSING",
    description=(
        "Ayeduase Modern Hostel Block is a newly developed student accommodation facility nestled in the "
        "heart of Ayeduase, one of the most popular student communities adjacent to KNUST in Kumasi. "
        "The three-storey stone-clad building offers comfortable accommodation for both male and female "
        "students with dedicated floor sections for each gender. Each floor is equipped with a kitchenette, "
        "clean modern washrooms, study nooks, and a communal living area. The property is secured with "
        "24-hour security personnel, CCTV, and a fully gated compound with off-street parking for motorcycles "
        "and bicycles. High-speed Wi-Fi is available across all floors, and the standby generator ensures "
        "continuous power during outages."
    ),
    address="Ayeduase Road, Off KNUST Main Road",
    city="Kumasi",
    region="Ashanti",
    country="Ghana",
    digital_address="AK-541-6789",
    latitude=6.676300,
    longitude=-1.574800,
    nearest_institution="KNUST (Kwame Nkrumah University of Science and Technology)",
    distance_to_campus=0.7,
    walking_time_estimate=8,
    nearby_landmarks="KNUST Commercial Area, Ayeduase Market, KNUST Sports Stadium",
    suitable_for_students=True,
    suitable_for_workers=False,
    suitable_for_national_service=True,
    hostel_type="MIXED",
    ownership_type="PRIVATE",
    total_area=750.0,
    total_floors=3,
    is_available=True,
    is_verified=True,
    is_featured=True,
    status="APPROVED",
    owner_name="Emmanuel Boateng",
    owner_email="manager@ayeduasehostel.com",
    owner_phone="+233 27 644 5511",
    uploaded_by=admin_user,
    house_rules=(
        "• Quiet hours: 10:00 PM – 5:30 AM on weekdays; 11:00 PM – 7:00 AM on weekends.\n"
        "• Tenants must display ID at the security gate at all times.\n"
        "• Personal waste to be disposed of only in designated bins.\n"
        "• Cooking is ONLY permitted in floor kitchenettes — not in rooms.\n"
        "• Electrical appliances above 1000W are strictly prohibited."
    ),
    visitor_policy=(
        "• Visitors allowed between 8:00 AM and 8:00 PM only.\n"
        "• Male visitors are not permitted on female floors and vice versa.\n"
        "• All visitors must sign in at the gate and produce valid ID.\n"
        "• Overnight visitors are not allowed — no exceptions."
    ),
    prohibited_items=(
        "• NO smoking, alcohol, or narcotics on the premises.\n"
        "• NO gas cylinders, kerosene stoves, or open-flame cooking.\n"
        "• NO pets of any kind.\n"
        "• NO loud music between 9:00 PM and 7:00 AM.\n"
        "• NO electric heaters or high-wattage appliances."
    ),
    emergency_contacts=(
        "• Hostel Security Desk (24/7): +233 27 644 5511\n"
        "• Hostel Manager (Emmanuel): +233 27 644 5511\n"
        "• KNUST Campus Security: +233 32 206 0555\n"
        "• Kumasi Central Police: +233 32 201 2345\n"
        "• National Fire Service: 192"
    ),
    cancellation_policy="Full refund 14 days before semester start. 50% refund within 7 days. No refund after move-in.",
    cctv=True,
    security_personnel=True,
    gated_community=True,
    water_availability="Municipal Supply + Overhead Tank Backup (24/7)",
    electricity_stability="High (Generator kicks in under 5 min)",
    internet_availability="Fibre Wi-Fi — All 3 Floors",
    utility_billing_method="INCLUDED_IN_RENT",
    fire_safety_compliance=True,
    safety_score=9,
    smoking_allowed=False,
    pets_allowed=False,
    guests_allowed=True,
    maximum_guests=2,
)

add_amenities(h3, [wifi, security, water, ac, study, generator, cctv_am, fence_am, kitchen_am, parking_am])

PropertyImage.objects.create(
    accommodation_property=h3,
    image=copy_prop_image("images (2).jpeg", "HST-KMS-AMH-003_ext_main.jpeg"),
    image_type="EXTERIOR", caption="Ayeduase Modern Hostel Block — Exterior", is_primary=True, order=1
)
PropertyImage.objects.create(
    accommodation_property=h3,
    image=copy_prop_image("images (12).jpeg", "HST-KMS-AMH-003_ext_2.jpeg"),
    image_type="EXTERIOR", caption="Hostel — Side View with Balconies", is_primary=False, order=2
)
PropertyImage.objects.create(
    accommodation_property=h3,
    image=copy_prop_image("images (16).jpeg", "HST-KMS-AMH-003_int_corridor.jpeg"),
    image_type="INTERIOR", caption="Hostel Interior Corridor", is_primary=False, order=3
)
PropertyImage.objects.create(
    accommodation_property=h3,
    image=copy_prop_image("images (20).jpeg", "HST-KMS-AMH-003_int_room.jpeg"),
    image_type="INTERIOR", caption="Well-Furnished Hostel Room", is_primary=False, order=4
)

rt_h3_double = RoomType.objects.create(
    accommodation_property=h3,
    room_type_name="Double Room (2 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="DOUBLE",
    total_rooms=25,
    beds_per_room=2,
    total_capacity=50,
    available_slots=50,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 3 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="BALANCED",
    study_environment_rating=4,
)
RoomTypePricing.objects.create(
    room_type=rt_h3_double,
    payment_type="SEMESTER",
    semester_price=2200.00,
    monthly_price=550.00,
    security_deposit=350.00,
    registration_fee=100.00,
    currency="GHS",
)

rt_h3_triple = RoomType.objects.create(
    accommodation_property=h3,
    room_type_name="Triple Room (3 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="TRIPLE",
    total_rooms=10,
    beds_per_room=3,
    total_capacity=30,
    available_slots=30,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=False,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 3 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="SOCIAL",
    study_environment_rating=3,
)
RoomTypePricing.objects.create(
    room_type=rt_h3_triple,
    payment_type="SEMESTER",
    semester_price=1600.00,
    monthly_price=400.00,
    security_deposit=250.00,
    registration_fee=80.00,
    currency="GHS",
)

r_h3_d01 = Room.objects.create(
    accommodation_property=h3, room_type=rt_h3_double,
    room_number="D101", floor="1st Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h3_d01, image=copy_room_image("images (5).jpeg", "HST-KMS-AMH-003_rm_D101_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h3_d01, image=copy_room_image("images (16).jpeg", "HST-KMS-AMH-003_rm_D101_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h3_d02 = Room.objects.create(
    accommodation_property=h3, room_type=rt_h3_double,
    room_number="D201", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h3_d02, image=copy_room_image("images (3).jpeg", "HST-KMS-AMH-003_rm_D201_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h3_d02, image=copy_room_image("images (20).jpeg", "HST-KMS-AMH-003_rm_D201_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h3_t01 = Room.objects.create(
    accommodation_property=h3, room_type=rt_h3_triple,
    room_number="T301", floor="3rd Floor", total_slots=3, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h3_t01, image=copy_room_image("images (1).jpeg", "HST-KMS-AMH-003_rm_T301_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h3_t01, image=copy_room_image("images (9).jpeg", "HST-KMS-AMH-003_rm_T301_2.jpeg"), image_type="BEDROOM", is_primary=False)

ProximityDestination.objects.create(accommodation_property=h3, destination_name="KNUST Main Gate", destination_type="INSTITUTION", distance_km=0.7, travel_time_minutes=8, travel_mode="WALK", order=1)
ProximityDestination.objects.create(accommodation_property=h3, destination_name="Ayeduase Market", destination_type="MARKET", distance_km=0.3, travel_time_minutes=4, travel_mode="WALK", order=2)
ProximityDestination.objects.create(accommodation_property=h3, destination_name="Ayeduase Taxi Rank", destination_type="TRANSPORT", distance_km=0.4, travel_time_minutes=5, travel_mode="WALK", order=3)
ProximityDestination.objects.create(accommodation_property=h3, destination_name="KNUST Hospital", destination_type="HOSPITAL", distance_km=1.5, travel_time_minutes=6, travel_mode="TAXI", order=4)

print(f"  [OK] {h3.title} created successfully.")


# ══════════════════════════════════════════════════════════════════════════════
# HOSTEL 4 — Sunrise Orange Hostel (Kumasi / Kotei)
# Exterior: images (7).jpeg (orange building) | Rooms: images (17).jpeg, images (15).jpeg
# ══════════════════════════════════════════════════════════════════════════════
print("\n[4/5] Creating Sunrise Orange Hostel (Kumasi / Kotei)...")

if Property.objects.filter(property_code="HST-KMS-SOH-004").exists():
    Property.objects.filter(property_code="HST-KMS-SOH-004").delete()
    print("  [DEL] Removed existing HST-KMS-SOH-004")

h4 = Property.objects.create(
    title="Sunrise Orange Hostel",
    property_code="HST-KMS-SOH-004",
    property_type="HOSTEL",
    property_category="STUDENT_HOUSING",
    description=(
        "Sunrise Orange Hostel is a secure and affordable student residence located in Kotei, a vibrant "
        "student-dominated neighbourhood approximately 10 minutes by trotro from KNUST. "
        "Identifiable by its distinctive orange exterior walls and razor-wire security fencing, the hostel "
        "provides a structured and safe living environment for both male and female students on separate floors. "
        "Amenities include a borehole water system, standby generator, communal kitchenettes on each floor, "
        "clean shared washrooms serviced daily, and Wi-Fi internet. The hostel is close to several provision "
        "shops, print centres, pharmacies, and the Kotei Market — making daily student life very convenient."
    ),
    address="Kotei-Deduako Road, Near Kotei Market",
    city="Kumasi",
    region="Ashanti",
    country="Ghana",
    digital_address="AK-312-9901",
    latitude=6.693100,
    longitude=-1.591400,
    nearest_institution="KNUST (Kwame Nkrumah University of Science and Technology)",
    distance_to_campus=3.2,
    walking_time_estimate=38,
    nearby_landmarks="Kotei Market, Deduako Roundabout, Suame Magazine",
    suitable_for_students=True,
    suitable_for_workers=True,
    hostel_type="MIXED",
    ownership_type="PRIVATE",
    total_area=500.0,
    total_floors=3,
    is_available=True,
    is_verified=True,
    is_featured=False,
    status="APPROVED",
    owner_name="Yaw Asiedu-Mensah",
    owner_email="yaw.asiedu@sunriseghostel.com",
    owner_phone="+233 55 312 7733",
    uploaded_by=admin_user,
    house_rules=(
        "• Curfew: Gate locks at 10:00 PM and reopens at 6:00 AM.\n"
        "• All tenants must carry their hostel ID cards at all times.\n"
        "• Communal cooking areas must be cleaned after each use.\n"
        "• Waste disposal in designated bins on each floor.\n"
        "• No noise after 10:00 PM."
    ),
    visitor_policy=(
        "• Visitors permitted between 9:00 AM and 7:00 PM.\n"
        "• Opposite-gender visitors restricted to ground-floor reception.\n"
        "• All visitors must sign the visitor register at the security post.\n"
        "• No overnight visitors."
    ),
    prohibited_items=(
        "• NO smoking or alcohol on the premises.\n"
        "• NO gas cylinders or open-flame cooking in rooms.\n"
        "• NO pets.\n"
        "• NO loud music or entertainment systems after 10:00 PM."
    ),
    emergency_contacts=(
        "• Sunrise Security Desk (24/7): +233 55 312 7733\n"
        "• Manager (Yaw): +233 55 312 7733\n"
        "• Kotei Police Post: +233 32 202 7100\n"
        "• Emergency: 191 / 112"
    ),
    cancellation_policy="Full refund 10 days before semester. 50% if within 5 days. No refund after move-in.",
    cctv=True,
    security_personnel=True,
    gated_community=True,
    water_availability="Borehole with Overhead Tank (24/7)",
    electricity_stability="Medium (Generator, 10 min switchover)",
    internet_availability="Wi-Fi — Ground & 1st Floor",
    utility_billing_method="INCLUDED_IN_RENT",
    fire_safety_compliance=False,
    safety_score=7,
    smoking_allowed=False,
    pets_allowed=False,
    guests_allowed=True,
    maximum_guests=1,
)

add_amenities(h4, [wifi, security, water, generator, cctv_am, fence_am, kitchen_am, fan_am])

PropertyImage.objects.create(
    accommodation_property=h4,
    image=copy_prop_image("images (7).jpeg", "HST-KMS-SOH-004_ext_main.jpeg"),
    image_type="EXTERIOR", caption="Sunrise Orange Hostel — Exterior View", is_primary=True, order=1
)
PropertyImage.objects.create(
    accommodation_property=h4,
    image=copy_prop_image("images (18).jpeg", "HST-KMS-SOH-004_ext_2.jpeg"),
    image_type="EXTERIOR", caption="Hostel Compound & Entrance", is_primary=False, order=2
)
PropertyImage.objects.create(
    accommodation_property=h4,
    image=copy_prop_image("images (17).jpeg", "HST-KMS-SOH-004_int_room.jpeg"),
    image_type="INTERIOR", caption="Student Room Interior — Wardrobe & Bunk", is_primary=False, order=3
)
PropertyImage.objects.create(
    accommodation_property=h4,
    image=copy_prop_image("images (20).jpeg", "HST-KMS-SOH-004_int_room2.jpeg"),
    image_type="INTERIOR", caption="Double Bed Room", is_primary=False, order=4
)

rt_h4_single = RoomType.objects.create(
    accommodation_property=h4,
    room_type_name="Single Room (1 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="SINGLE",
    total_rooms=8,
    beds_per_room=1,
    total_capacity=8,
    available_slots=8,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 5 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="QUIET",
    study_environment_rating=4,
)
RoomTypePricing.objects.create(
    room_type=rt_h4_single,
    payment_type="SEMESTER",
    semester_price=2400.00,
    monthly_price=600.00,
    security_deposit=350.00,
    registration_fee=100.00,
    currency="GHS",
)

rt_h4_double = RoomType.objects.create(
    accommodation_property=h4,
    room_type_name="Double Room (2 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="DOUBLE",
    total_rooms=16,
    beds_per_room=2,
    total_capacity=32,
    available_slots=32,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=False,
    private_bathroom=False,
    shared_bathroom_ratio="1 Washroom per 4 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="BALANCED",
    study_environment_rating=3,
)
RoomTypePricing.objects.create(
    room_type=rt_h4_double,
    payment_type="SEMESTER",
    semester_price=1700.00,
    monthly_price=425.00,
    security_deposit=250.00,
    registration_fee=80.00,
    currency="GHS",
)

r_h4_s01 = Room.objects.create(
    accommodation_property=h4, room_type=rt_h4_single,
    room_number="S101", floor="1st Floor", total_slots=1, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h4_s01, image=copy_room_image("images (19).jpeg", "HST-KMS-SOH-004_rm_S101_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h4_s01, image=copy_room_image("images.jpeg", "HST-KMS-SOH-004_rm_S101_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h4_d01 = Room.objects.create(
    accommodation_property=h4, room_type=rt_h4_double,
    room_number="D201", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h4_d01, image=copy_room_image("images (17).jpeg", "HST-KMS-SOH-004_rm_D201_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h4_d01, image=copy_room_image("images (15).jpeg", "HST-KMS-SOH-004_rm_D201_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h4_d02 = Room.objects.create(
    accommodation_property=h4, room_type=rt_h4_double,
    room_number="D202", floor="2nd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h4_d02, image=copy_room_image("images (4).jpeg", "HST-KMS-SOH-004_rm_D202_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h4_d02, image=copy_room_image("images (3).jpeg", "HST-KMS-SOH-004_rm_D202_2.jpeg"), image_type="BEDROOM", is_primary=False)

ProximityDestination.objects.create(accommodation_property=h4, destination_name="Kotei Market", destination_type="MARKET", distance_km=0.2, travel_time_minutes=3, travel_mode="WALK", order=1)
ProximityDestination.objects.create(accommodation_property=h4, destination_name="Kotei Trotro Stop", destination_type="TRANSPORT", distance_km=0.3, travel_time_minutes=4, travel_mode="WALK", order=2)
ProximityDestination.objects.create(accommodation_property=h4, destination_name="Deduako Health Centre", destination_type="HOSPITAL", distance_km=1.0, travel_time_minutes=5, travel_mode="TAXI", order=3)
ProximityDestination.objects.create(accommodation_property=h4, destination_name="KNUST (Kumasi)", destination_type="INSTITUTION", distance_km=3.2, travel_time_minutes=12, travel_mode="TROTRO", order=4)

print(f"  [OK] {h4.title} created successfully.")


# ══════════════════════════════════════════════════════════════════════════════
# HOSTEL 5 — White Block Executive Hostel (Kumasi / KNUST Ext.)
# Exterior: images (12).jpeg | Rooms: images (15).jpeg, images (16).jpeg
# ══════════════════════════════════════════════════════════════════════════════
print("\n[5/5] Creating White Block Executive Hostel (Kumasi / KNUST Ext.)...")

if Property.objects.filter(property_code="HST-KMS-WBE-005").exists():
    Property.objects.filter(property_code="HST-KMS-WBE-005").delete()
    print("  [DEL] Removed existing HST-KMS-WBE-005")

h5 = Property.objects.create(
    title="White Block Executive Hostel",
    property_code="HST-KMS-WBE-005",
    property_type="HOSTEL",
    property_category="STUDENT_HOUSING",
    description=(
        "White Block Executive Hostel is a premium student accommodation facility near KNUST, designed "
        "for students who value quality and modern amenities without compromise. The newly-built white-plastered "
        "four-storey building features air-conditioned rooms, tiled floors, 24-hour fibre Wi-Fi, and private "
        "ensuite bathrooms for executive single room occupants. The building is powered by a 60KVA generator "
        "for uninterrupted electricity, and triple-filtered borehole water ensures clean water at all times. "
        "Each room features a study desk, wardrobe, reading lamp, and window blinds. The hostel also features "
        "a dedicated car park, a communal lounge with TV, and weekly room cleaning services included in the rent."
    ),
    address="KNUST Extension Road, Off Bomso Junction",
    city="Kumasi",
    region="Ashanti",
    country="Ghana",
    digital_address="AK-780-3321",
    latitude=6.671800,
    longitude=-1.562400,
    nearest_institution="KNUST (Kwame Nkrumah University of Science and Technology)",
    distance_to_campus=1.5,
    walking_time_estimate=18,
    nearby_landmarks="Bomso Junction, KNUST Extension, Asokwa Market",
    suitable_for_students=True,
    suitable_for_workers=True,
    suitable_for_single_professionals=True,
    hostel_type="MIXED",
    ownership_type="PRIVATE",
    total_area=900.0,
    total_floors=4,
    is_available=True,
    is_verified=True,
    is_featured=True,
    status="APPROVED",
    owner_name="Dr. Kofi Owusu-Mensah",
    owner_email="admin@whiteblockexecutive.com",
    owner_phone="+233 20 977 4456",
    uploaded_by=admin_user,
    house_rules=(
        "• Absolute quiet hours from 11:00 PM – 7:00 AM (executive standard).\n"
        "• All tenants must sign a lease agreement and code of conduct upon check-in.\n"
        "• Rooms are inspected monthly — tenants are required to maintain cleanliness.\n"
        "• No cooking in rooms — use the communal kitchenette.\n"
        "• Parking for 2-wheelers only; car parking by prior arrangement.\n"
        "• Electricity used responsibly — AC must be switched off when leaving room."
    ),
    visitor_policy=(
        "• Visitors allowed between 10:00 AM and 8:00 PM.\n"
        "• All visitors must sign in at the reception with a valid photo ID.\n"
        "• Visitors are not permitted on upper floors — use the ground-floor lounge.\n"
        "• Overnight visitors are strictly not allowed."
    ),
    prohibited_items=(
        "• NO smoking anywhere inside the building.\n"
        "• NO alcohol or drug use on premises.\n"
        "• NO gas cylinders or hot plates in rooms.\n"
        "• NO pets.\n"
        "• NO modification to furniture, fixtures, or room layout without approval."
    ),
    emergency_contacts=(
        "• White Block Reception (24/7): +233 20 977 4456\n"
        "• Building Manager (Dr. Kofi): +233 20 977 4456\n"
        "• KNUST Security: +233 32 206 0555\n"
        "• Komfo Anokye Teaching Hospital: +233 32 202 2301\n"
        "• Emergency: 191 / 112"
    ),
    cancellation_policy="Full refund if cancelled 21 days before semester. No refund after move-in.",
    cctv=True,
    security_personnel=True,
    gated_community=True,
    water_availability="Triple-Filtered Borehole Water (24/7)",
    electricity_stability="Very High (60KVA Generator — Instant Changeover)",
    internet_availability="Fibre Wi-Fi — All Rooms & Common Areas",
    utility_billing_method="INCLUDED_IN_RENT",
    fire_safety_compliance=True,
    safety_score=9,
    smoking_allowed=False,
    pets_allowed=False,
    guests_allowed=True,
    maximum_guests=2,
)

add_amenities(h5, [wifi, security, water, ac, study, generator, cctv_am, fence_am, kitchen_am, parking_am, laundry])

PropertyImage.objects.create(
    accommodation_property=h5,
    image=copy_prop_image("images (12).jpeg", "HST-KMS-WBE-005_ext_main.jpeg"),
    image_type="EXTERIOR", caption="White Block Executive Hostel — Modern Exterior", is_primary=True, order=1
)
PropertyImage.objects.create(
    accommodation_property=h5,
    image=copy_prop_image("images (10).jpeg", "HST-KMS-WBE-005_ext_2.jpeg"),
    image_type="EXTERIOR", caption="Hostel Campus — Full Block View", is_primary=False, order=2
)
PropertyImage.objects.create(
    accommodation_property=h5,
    image=copy_prop_image("images (15).jpeg", "HST-KMS-WBE-005_int_room.jpeg"),
    image_type="INTERIOR", caption="Executive Room — AC & Study Desk", is_primary=False, order=3
)
PropertyImage.objects.create(
    accommodation_property=h5,
    image=copy_prop_image("images (16).jpeg", "HST-KMS-WBE-005_int_lounge.jpeg"),
    image_type="INTERIOR", caption="Communal Lounge Area", is_primary=False, order=4
)
PropertyImage.objects.create(
    accommodation_property=h5,
    image=copy_prop_image("images (14).jpeg", "HST-KMS-WBE-005_int_bedroom.jpeg"),
    image_type="INTERIOR", caption="Executive Single Bedroom", is_primary=False, order=5
)

# Executive single room type
rt_h5_exec = RoomType.objects.create(
    accommodation_property=h5,
    room_type_name="Executive Single Room (1 in a Room — Ensuite)",
    billing_model="SEMESTER_BASED",
    occupancy_type="SINGLE",
    total_rooms=20,
    beds_per_room=1,
    total_capacity=20,
    available_slots=20,
    air_conditioning=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=True,
    gender_restriction="ANY",
    preferred_lifestyle="QUIET",
    study_environment_rating=5,
)
RoomTypePricing.objects.create(
    room_type=rt_h5_exec,
    payment_type="SEMESTER",
    semester_price=4500.00,
    monthly_price=1125.00,
    security_deposit=700.00,
    registration_fee=200.00,
    currency="GHS",
)
# Also add academic year pricing
RoomTypePricing.objects.create(
    room_type=rt_h5_exec,
    payment_type="YEARLY",
    yearly_price=8200.00,
    academic_year_price=8200.00,
    security_deposit=700.00,
    registration_fee=200.00,
    currency="GHS",
)

# Standard double room type
rt_h5_double = RoomType.objects.create(
    accommodation_property=h5,
    room_type_name="Standard Double Room (2 in a Room)",
    billing_model="SEMESTER_BASED",
    occupancy_type="DOUBLE",
    total_rooms=15,
    beds_per_room=2,
    total_capacity=30,
    available_slots=30,
    fan=True,
    wifi_available=True,
    study_desk_available=True,
    wardrobe_available=True,
    private_bathroom=False,
    shared_bathroom_ratio="1 Ensuite Washroom per 2 Rooms",
    gender_restriction="ANY",
    preferred_lifestyle="BALANCED",
    study_environment_rating=4,
)
RoomTypePricing.objects.create(
    room_type=rt_h5_double,
    payment_type="SEMESTER",
    semester_price=3000.00,
    monthly_price=750.00,
    security_deposit=450.00,
    registration_fee=150.00,
    currency="GHS",
)

# Physical rooms
r_h5_e01 = Room.objects.create(
    accommodation_property=h5, room_type=rt_h5_exec,
    room_number="E101", floor="1st Floor", total_slots=1, occupied_slots=0, status="AVAILABLE",
    notes="Executive room with ensuite bathroom. Air-conditioned."
)
RoomImage.objects.create(room=r_h5_e01, image=copy_room_image("images (15).jpeg", "HST-KMS-WBE-005_rm_E101_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h5_e01, image=copy_room_image("images (14).jpeg", "HST-KMS-WBE-005_rm_E101_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h5_e02 = Room.objects.create(
    accommodation_property=h5, room_type=rt_h5_exec,
    room_number="E201", floor="2nd Floor", total_slots=1, occupied_slots=0, status="AVAILABLE",
    notes="Executive room with ensuite bathroom. Air-conditioned."
)
RoomImage.objects.create(room=r_h5_e02, image=copy_room_image("images (16).jpeg", "HST-KMS-WBE-005_rm_E201_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h5_e02, image=copy_room_image("images.jpeg", "HST-KMS-WBE-005_rm_E201_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h5_d01 = Room.objects.create(
    accommodation_property=h5, room_type=rt_h5_double,
    room_number="D301", floor="3rd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h5_d01, image=copy_room_image("images (5).jpeg", "HST-KMS-WBE-005_rm_D301_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h5_d01, image=copy_room_image("images (3).jpeg", "HST-KMS-WBE-005_rm_D301_2.jpeg"), image_type="BEDROOM", is_primary=False)

r_h5_d02 = Room.objects.create(
    accommodation_property=h5, room_type=rt_h5_double,
    room_number="D302", floor="3rd Floor", total_slots=2, occupied_slots=0, status="AVAILABLE"
)
RoomImage.objects.create(room=r_h5_d02, image=copy_room_image("images (4).jpeg", "HST-KMS-WBE-005_rm_D302_1.jpeg"), image_type="BEDROOM", is_primary=True)
RoomImage.objects.create(room=r_h5_d02, image=copy_room_image("images (17).jpeg", "HST-KMS-WBE-005_rm_D302_2.jpeg"), image_type="BEDROOM", is_primary=False)

ProximityDestination.objects.create(accommodation_property=h5, destination_name="KNUST Main Campus", destination_type="INSTITUTION", distance_km=1.5, travel_time_minutes=6, travel_mode="TAXI", order=1)
ProximityDestination.objects.create(accommodation_property=h5, destination_name="Bomso Junction", destination_type="TRANSPORT", distance_km=0.3, travel_time_minutes=4, travel_mode="WALK", order=2)
ProximityDestination.objects.create(accommodation_property=h5, destination_name="Asokwa Market", destination_type="MARKET", distance_km=1.0, travel_time_minutes=5, travel_mode="TROTRO", order=3)
ProximityDestination.objects.create(accommodation_property=h5, destination_name="Komfo Anokye Teaching Hospital", destination_type="HOSPITAL", distance_km=4.5, travel_time_minutes=15, travel_mode="TAXI", order=4)
ProximityDestination.objects.create(accommodation_property=h5, destination_name="Asokwa Shopping Mall", destination_type="SHOPPING", distance_km=1.2, travel_time_minutes=6, travel_mode="TROTRO", order=5)

print(f"  [OK] {h5.title} created successfully.")


# ─── Final Summary ────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SEED COMPLETE — SUMMARY")
print("="*70)

from properties.models import Property, Room, RoomImage, PropertyImage

for prop in Property.objects.filter(property_code__in=[
    "HST-ACC-MLH-001", "HST-ACC-PRH-002", "HST-KMS-AMH-003",
    "HST-KMS-SOH-004", "HST-KMS-WBE-005"
]):
    rooms = Room.objects.filter(accommodation_property=prop)
    prop_imgs = PropertyImage.objects.filter(accommodation_property=prop)
    room_imgs = RoomImage.objects.filter(room__accommodation_property=prop)
    print(f"\n  [{prop.property_code}] {prop.title}")
    print(f"    City: {prop.city} | Type: {prop.hostel_type} | Status: {prop.status}")
    print(f"    Rooms: {rooms.count()} physical | Property Images: {prop_imgs.count()} | Room Images: {room_imgs.count()}")
    print(f"    Amenities: {prop.amenities.count()}")
    print(f"    Proximity Destinations: {prop.proximity_destinations.count()}")

print("\n✅ All 5 hostel properties seeded successfully!\n")
