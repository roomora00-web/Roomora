import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from properties.models import Property, Room, RoomImage, PropertyImage, RoomType, UnitType, PropertyAmenity, Amenity
from accounts.models import User

# First, import raw data from the management command
from properties.management.commands.populate_ghana_properties import Command as PopulateCommand

cmd = PopulateCommand()

admin_user = User.objects.filter(user_type='ADMIN').first()
if not admin_user:
    admin_user = User.objects.create_user(
        email='admin@staymatch.com',
        password='admin123',
        first_name='Kwame',
        last_name='Mensa',
        user_type='ADMIN'
    )

print("Clearing properties...")
Property.objects.all().delete()
cmd.create_amenities()

properties_data = cmd.get_all_ghana_properties()

# Mapping properties based on available images
category_images = {
    'HOSTEL': [],
    'APARTMENT': [],
    'COMPOUND': [],
    'VILLA': [],
}

media_dir = '/home/gazy-johnson/Downloads/school/ROOMORA/media/property_images'
for f in os.listdir(media_dir):
    if f.startswith('real_'):
        if 'hostel' in f:
            category_images['HOSTEL'].append(f)
        elif 'apartment' in f:
            category_images['APARTMENT'].append(f)
        elif 'compound' in f:
            category_images['COMPOUND'].append(f)
        elif 'villa' in f:
            category_images['VILLA'].append(f)

print(f"Loaded images: Hostels {len(category_images['HOSTEL'])}, Apartments {len(category_images['APARTMENT'])}, Compound {len(category_images['COMPOUND'])}, Villa {len(category_images['VILLA'])}")

for prop_data in properties_data:
    # Let's dynamically adjust the type if needed, but for now we'll match as best we can.
    prop_type = prop_data['property_type']
    
    # We map missing types to APARTMENT or HOSTEL
    cat_key = prop_type
    if cat_key not in category_images or not category_images[cat_key]:
        if 'COMPOUND' in prop_type: cat_key = 'COMPOUND'
        elif 'VILLA' in prop_type: cat_key = 'VILLA'
        elif prop_type in ['FLAT', 'STUDIO']: cat_key = 'APARTMENT'
        elif prop_type in ['STUDENT_APARTMENT']: cat_key = 'HOSTEL'
        else: cat_key = 'APARTMENT'
        
        if not category_images.get(cat_key):
            cat_key = 'APARTMENT'

    prop_data['property_type'] = cat_key # Force update type
    
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
        total_area=prop_data.get('total_area', 100),
        is_available=True,
    )
    
    # Amenities
    amenities = Amenity.objects.all()[:5]
    for am in amenities:
        PropertyAmenity.objects.create(accommodation_property=property_obj, amenity=am)
        
    # Images
    avail_imgs = category_images[cat_key]
    if len(avail_imgs) >= 1:
        # Cover page (exterior)
        cover_img = avail_imgs[0]
        PropertyImage.objects.create(
            accommodation_property=property_obj,
            image=f"property_images/{cover_img}",
            is_primary=True,
            image_type='EXTERIOR'
        )

    # Generate Rooms (RoomType + actual Rooms)
    if cat_key == 'HOSTEL':
        # Create a RoomType
        rt = RoomType.objects.create(
            accommodation_property=property_obj,
            room_type_name="Standard Double Room",
            occupancy_type="DOUBLE",
            total_rooms=4
        )
        for i in range(1, 5):
            room = Room.objects.create(
                accommodation_property=property_obj,
                room_type=rt,
                room_number=f"{i}01",
                total_slots=2,
                status="AVAILABLE"
            )
            # Add room images (interior, washroom, kitchen)
            imgs_to_pick = random.sample(avail_imgs, min(3, len(avail_imgs)))
            for idx, img in enumerate(imgs_to_pick):
                img_type = ['BEDROOM', 'WASHROOM', 'KITCHEN'][idx % 3]
                RoomImage.objects.create(
                    room=room,
                    image=f"property_images/{img}",
                    image_type=img_type,
                    is_primary=(idx==0)
                )
    else:
        # Apartment/Compound/Villa
        rt = RoomType.objects.create(
            accommodation_property=property_obj,
            room_type_name="Master Bedroom",
            occupancy_type="SINGLE",
            total_rooms=2
        )
        for i in range(1, 3):
            room = Room.objects.create(
                accommodation_property=property_obj,
                room_type=rt,
                room_number=f"A{i}",
                total_slots=1,
                status="AVAILABLE"
            )
            imgs_to_pick = random.sample(avail_imgs, min(3, len(avail_imgs)))
            for idx, img in enumerate(imgs_to_pick):
                img_type = ['BEDROOM', 'WASHROOM', 'KITCHEN'][idx % 3]
                RoomImage.objects.create(
                    room=room,
                    image=f"property_images/{img}",
                    image_type=img_type,
                    is_primary=(idx==0)
                )

print("Finished rebuilding properties and generating actual rooms!")
