# Generated manually to fix broken image URLs

from django.db import migrations


def update_image_urls(apps, schema_editor):
    """Update existing property image URLs from deprecated source.unsplash.com to working format"""
    PropertyImage = apps.get_model('properties', 'PropertyImage')
    
    # Working Unsplash photo IDs
    photo_ids = [
        'photo-1522708323590-d24dbb6b0267',  # Modern apartment
        'photo-1502672260266-1c1ef2d93688',  # Building exterior
        'photo-1560448204-e02f11c3d0e2',  # Interior room
        'photo-1554995207-c18c203602cb',  # Kitchen
        'photo-1584622650111-993a426fbf0a',  # Bathroom
        'photo-1560185007-cde436f6a4d0',  # Amenities
        'photo-1595526114035-0d45ed16cfbf',  # Hostel room
        'photo-1522771739844-6a9f6d5f14af',  # Student housing
        'photo-1493809842364-78817add7ffb',  # Modern building
        'photo-1484154218962-a197022b5858',  # Residential
        'photo-1512917774080-9991f1c4c750',  # Apartment complex
        'photo-1567681812100-5bfe18c7b729',  # City housing
    ]
    
    # Get all property images
    all_images = PropertyImage.objects.all()
    
    for image in all_images:
        # Check if the image has a broken source.unsplash.com URL using image.name (string field)
        if image.name and 'source.unsplash.com' in image.name:
            # Generate a new working URL based on the property code
            property_code = image.accommodation_property.property_code if image.accommodation_property else 'DEFAULT'
            start_index = hash(property_code) % len(photo_ids)
            
            # Use image order to select different photos
            photo_index = (start_index + image.order) % len(photo_ids)
            photo_id = photo_ids[photo_index]
            
            # Update to working URL format
            image.name = f"https://images.unsplash.com/photo-{photo_id}?w=800&h=600&fit=crop"
            image.save()


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0010_populate_ghana_properties'),
    ]

    operations = [
        migrations.RunPython(update_image_urls, migrations.RunPython.noop),
    ]
