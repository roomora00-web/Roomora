import os
import django
import itertools
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from properties.models import Property, Room, PropertyImage, RoomImage

print("Deleting old images...")
PropertyImage.objects.all().delete()
RoomImage.objects.all().delete()

base_dir = '/home/gazy-johnson/Downloads/school/ROOMORA/Properties00'

def load_images(folder):
    path = os.path.join(base_dir, folder)
    if os.path.exists(path):
        return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return []

pools = {
    'HOSTEL': load_images('HOSTELS'),
    'APARTMENT': load_images('APARTMENT'),
    'COMPOUND': load_images('compound house'),
    'VILLA': load_images('villa'),
}

bathroom_imgs = load_images('bathrooms')
kitchen_imgs = load_images('kitchen')

def get_pool(prop_type):
    if prop_type in ['HOSTEL', 'STUDENT_APARTMENT']: return pools['HOSTEL']
    if prop_type in ['COMPOUND_HOUSE']: return pools['COMPOUND']
    if prop_type in ['VILLA']: return pools['VILLA']
    return pools['APARTMENT']

# Use cyclers so we distribute images nicely
cyclers = {k: itertools.cycle(v) if v else None for k, v in pools.items()}
bath_cycler = itertools.cycle(bathroom_imgs) if bathroom_imgs else None
kitchen_cycler = itertools.cycle(kitchen_imgs) if kitchen_imgs else None

properties = Property.objects.all()

for prop in properties:
    pool_key = 'APARTMENT'
    if prop.property_type in ['HOSTEL', 'STUDENT_APARTMENT']: pool_key = 'HOSTEL'
    elif prop.property_type == 'COMPOUND_HOUSE': pool_key = 'COMPOUND'
    elif prop.property_type == 'VILLA': pool_key = 'VILLA'
    
    cycler = cyclers[pool_key]
    if cycler:
        # Cover image
        cover_path = next(cycler)
        with open(cover_path, 'rb') as f:
            PropertyImage.objects.create(
                accommodation_property=prop,
                image=File(f, name=os.path.basename(cover_path)),
                is_primary=True,
                image_type='EXTERIOR'
            )
        
        # Room images
        for room in prop.rooms.all():
            # Bedroom
            bed_path = next(cycler)
            with open(bed_path, 'rb') as f:
                RoomImage.objects.create(
                    room=room,
                    image=File(f, name=os.path.basename(bed_path)),
                    image_type='BEDROOM',
                    is_primary=True
                )
            
            # Washroom
            if bath_cycler:
                bath_path = next(bath_cycler)
                with open(bath_path, 'rb') as f:
                    RoomImage.objects.create(
                        room=room,
                        image=File(f, name=os.path.basename(bath_path)),
                        image_type='WASHROOM',
                        is_primary=False
                    )
                    
            # Kitchen
            if kitchen_cycler:
                kit_path = next(kitchen_cycler)
                with open(kit_path, 'rb') as f:
                    RoomImage.objects.create(
                        room=room,
                        image=File(f, name=os.path.basename(kit_path)),
                        image_type='KITCHEN',
                        is_primary=False
                    )

print("Finished assigning real images to all properties and rooms.")
