from django.core.management.base import BaseCommand
from properties.models import Property, PropertyImage


class Command(BaseCommand):
    help = 'Update property images with unique Unsplash images for all existing properties'

    def handle(self, *args, **options):
        self.stdout.write('Starting property image update...')
        
        properties = Property.objects.all()
        updated_count = 0
        
        for property_obj in properties:
            # Delete existing images
            PropertyImage.objects.filter(accommodation_property=property_obj).delete()
            
            # Create new images
            self.create_property_images(property_obj)
            updated_count += 1
            self.stdout.write(f'Updated images for: {property_obj.title} - {property_obj.region}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated images for {updated_count} properties'))

    def create_property_images(self, property_obj):
        # Create unique images for each property using Unsplash source URLs
        image_types = ['EXTERIOR', 'INTERIOR', 'ROOM', 'KITCHEN', 'BATHROOM', 'AMENITY']
        
        # Generate unique keywords based on property type and region
        keywords = self.get_image_keywords(property_obj)
        
        for i, image_type in enumerate(image_types[:4]):  # At least 4 images
            keyword = keywords[i % len(keywords)]
            # Use unique identifier to ensure different images
            unique_id = f"{property_obj.property_code}_{i}"
            
            # Use picsum.photos for reliable placeholder images
            image_url = f"https://picsum.photos/seed/{unique_id}/800/600"
            
            PropertyImage.objects.create(
                accommodation_property=property_obj,
                image=image_url,  # Using URL instead of local file
                image_type=image_type,
                caption=f'{image_type} view of {property_obj.title} - {keyword}',
                is_primary=(i == 0),
                order=i
            )

    def get_image_keywords(self, property_obj):
        """Generate relevant image keywords based on property type and region"""
        property_type = property_obj.property_type.lower()
        region = property_obj.region.lower()
        
        # Base keywords by property type
        type_keywords = {
            'hostel': ['ghana-hostel', 'student-dormitory', 'shared-room', 'bunk-bed'],
            'apartment': ['ghana-apartment', 'modern-apartment', 'luxury-apartment', 'city-apartment'],
            'student_apartment': ['student-housing', 'student-apartment', 'campus-housing', 'dorm-room'],
            'flat': ['ghana-flat', 'apartment-flat', 'residential-flat'],
            'compound_house': ['ghana-compound-house', 'african-house', 'family-home'],
            'townhouse': ['ghana-townhouse', 'modern-townhouse'],
            'duplex': ['ghana-duplex', 'luxury-duplex'],
            'villa': ['ghana-villa', 'luxury-villa', 'estate-home'],
            'studio': ['studio-apartment', 'small-apartment', 'compact-living'],
        }
        
        # Region-specific keywords
        region_keywords = {
            'ashanti': ['kumasi', 'ashanti-region', 'ghana-city'],
            'brong-ahafo': ['sunyani', 'brong-ahafo', 'ghana-town'],
            'central': ['cape-coast', 'central-region', 'ghana-coast'],
            'eastern': ['koforidua', 'eastern-region', 'ghana-hills'],
            'greater accra': ['accra', 'ghana-capital', 'modern-africa'],
            'northern': ['tamale', 'northern-ghana', 'savanna'],
            'upper east': ['bolgatanga', 'upper-east-ghana'],
            'upper west': ['wa', 'upper-west-ghana'],
            'volta': ['ho', 'volta-region', 'ghana-lake'],
            'western': ['takoradi', 'western-ghana', 'ghana-harbour'],
            'ahafo': ['mim', 'ahafo-region'],
            'bono east': ['techiman', 'bono-east'],
            'north east': ['nalerigu', 'north-east-ghana'],
            'oti': ['dambai', 'oti-region'],
            'savannah': ['damongo', 'savannah-ghana'],
            'western north': ['sefwi-wiawso', 'western-north'],
        }
        
        # Get appropriate keywords
        type_list = type_keywords.get(property_type, ['ghana-housing', 'african-home'])
        region_list = region_keywords.get(region, ['ghana', 'africa'])
        
        # Combine and return unique keywords
        combined = type_list + region_list
        # Add some general housing keywords
        combined.extend(['building', 'architecture', 'real-estate'])
        
        return combined[:6]  # Return up to 6 unique keywords
