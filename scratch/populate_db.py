import os
from django.core.files import File
from properties.models import Property, RoomType, UnitType, Room, PropertyImage, RoomImage, RoomTypePricing, UnitTypePricing
from accounts.models import User
import glob
import random

# Get a host user
host_user = User.objects.filter(user_type='HOST').first()
if not host_user:
    host_user = User.objects.create(email='host_pop@example.com', user_type='HOST', first_name='Demo', last_name='Host')
    host_user.set_password('password123')
    host_user.save()

# Delete existing properties
Property.objects.all().delete()

# Image helpers
def get_random_image(folder):
    images = glob.glob(f"/home/gazy-johnson/Downloads/school/ROOMORA/Properties00/{folder}/*.*")
    if images:
        return random.choice(images)
    return None

def add_room_image(room, folder, img_type, is_primary=False):
    img_path = get_random_image(folder)
    if img_path:
        with open(img_path, 'rb') as f:
            RoomImage.objects.create(
                room=room,
                image=File(f, name=os.path.basename(img_path)),
                image_type=img_type,
                is_primary=is_primary
            )

def add_property_image(prop, folder):
    img_path = get_random_image(folder)
    if img_path:
        with open(img_path, 'rb') as f:
            PropertyImage.objects.create(
                accommodation_property=prop,
                image=File(f, name=os.path.basename(img_path)),
                is_primary=True
            )

# Real Property Definitions
properties_data = [
    {
        "title": "Evandy Hostel",
        "type": "HOSTEL",
        "address": "Boundary Road, East Legon",
        "city": "Accra",
        "region": "Greater Accra",
        "desc": "A premium student hostel offering comfort, security, and a great study environment. Close to major campuses with regular shuttle services.",
        "rules": "1. No loud music after 10 PM.\n2. Visitors must leave by 8 PM.\n3. Keep communal areas clean.\n4. No smoking indoors.",
        "prohibited": "Hot plates, weapons, pets, illicit substances.",
        "img_folder": "HOSTELS",
        "rooms": [
            {"slots": 2, "name": "Twin Standard", "price": 4500},
            {"slots": 4, "name": "Quad Room", "price": 3000},
            {"slots": 1, "name": "Executive Single", "price": 6000}
        ]
    },
    {
        "title": "Bani Hostel",
        "type": "HOSTEL",
        "address": "Legon Campus Road",
        "city": "Accra",
        "region": "Greater Accra",
        "desc": "Affordable and convenient student accommodation located within walking distance of the main university campus.",
        "rules": "1. Quiet hours are strictly observed during exams.\n2. Respect your roommates' space.\n3. Cooking is only allowed in designated kitchens.",
        "prohibited": "Pets, large sound systems, flammable materials.",
        "img_folder": "HOSTELS",
        "rooms": [
            {"slots": 2, "name": "A-Shared Double", "price": 3800},
            {"slots": 2, "name": "B-Shared Double", "price": 3900}
        ]
    },
    {
        "title": "Pentagon Hostel",
        "type": "HOSTEL",
        "address": "Pentagon Avenue",
        "city": "Accra",
        "region": "Greater Accra",
        "desc": "An exclusive private hostel tailored for focused students who require a single-occupancy setup with full privacy.",
        "rules": "1. No overnight guests.\n2. Keep noise levels to an absolute minimum.\n3. Maintain personal hygiene in shared corridors.",
        "prohibited": "Pets, smoking, heavy electrical appliances.",
        "img_folder": "HOSTELS",
        "rooms": [
            {"slots": 1, "name": "Premium Single", "price": 7500}
        ]
    },
    {
        "title": "Oasis Apartments",
        "type": "APARTMENT",
        "address": "Spintex Road, Comm 18",
        "city": "Accra",
        "region": "Greater Accra",
        "desc": "A fully furnished, modern single-room apartment perfect for young professionals or independent students seeking luxury.",
        "rules": "1. Respect the neighbors in the block.\n2. Do not leave garbage in the hallway.\n3. Parties require prior management approval.",
        "prohibited": "Illegal substances, unregistered subletting.",
        "img_folder": "APARTMENT",
        "rooms": [
            {"slots": 1, "name": "Studio Apartment", "shared": False, "price": 2000}
        ]
    },
    {
        "title": "Pearl Shared Residence",
        "type": "APARTMENT",
        "address": "Cantonments",
        "city": "Accra",
        "region": "Greater Accra",
        "desc": "A spacious, upscale apartment designed to be shared by two residents, offering private bedrooms with shared living and kitchen areas.",
        "rules": "1. Shared chores are expected to be maintained.\n2. Coordinate with your flatmate regarding visitors.\n3. Lock the main door at all times.",
        "prohibited": "Pets (unless agreed by both parties), weapons.",
        "img_folder": "APARTMENT",
        "rooms": [
            {"slots": 2, "name": "Shared Flat Setup", "shared": True, "price": 3500}
        ]
    }
]

for p_data in properties_data:
    prop = Property.objects.create(
        uploaded_by=host_user,
        title=p_data["title"],
        property_type=p_data["type"],
        description=p_data["desc"],
        address=p_data["address"],
        city=p_data["city"],
        region=p_data["region"],
        house_rules=p_data["rules"],
        prohibited_items=p_data["prohibited"],
        status='PUBLISHED',
        is_verified=True,
        total_area=100.0,
    )
    add_property_image(prop, p_data["img_folder"])
    
    for i, r_data in enumerate(p_data["rooms"]):
        if p_data["type"] == "HOSTEL":
            rt = RoomType.objects.create(
                accommodation_property=prop,
                room_type_name=r_data["name"],
                occupancy_type='SINGLE' if r_data["slots"] == 1 else 'SHARED',
                total_rooms=1,
                beds_per_room=r_data["slots"],
                total_capacity=r_data["slots"],
                available_slots=r_data["slots"]
            )
            # Create pricing
            RoomTypePricing.objects.create(
                room_type=rt,
                payment_type='SEMESTER',
                semester_price=r_data["price"]
            )
            room = Room.objects.filter(room_type=rt).first()
            if not room:
                print(f"Failed to find created room for {r_data['name']}")
                continue
                
        else:
            ut = UnitType.objects.create(
                accommodation_property=prop,
                unit_name=r_data["name"],
                number_of_units=1,
                bedrooms=r_data["slots"],
                bathrooms=1,
                total_units=1,
                available_units=1,
                shared_apartment_allowed=r_data["shared"],
            )
            UnitTypePricing.objects.create(
                unit_type=ut,
                payment_type='MONTHLY',
                monthly_price=r_data["price"]
            )
            room = Room.objects.filter(unit_type=ut).first()
            if not room:
                slots = 2 if r_data.get("shared") else 1
                room = Room.objects.create(
                    accommodation_property=prop,
                    unit_type=ut,
                    room_number=f"UNIT-{p_data['title'][:3].upper()}-{i+1}",
                    total_slots=slots,
                    status='AVAILABLE'
                )
        
        # Use bedroom/interior images based on property type folder
        add_room_image(room, p_data["img_folder"], 'BEDROOM', is_primary=True)
        # Kitchen and bathroom from specific folders
        add_room_image(room, "kitchen", 'KITCHEN')
        add_room_image(room, "bathrooms", 'WASHROOM')

print("Database populated successfully!")
