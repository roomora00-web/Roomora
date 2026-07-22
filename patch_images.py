with open("properties/management/commands/populate_ghana_properties.py", "r") as f:
    content = f.read()

import re

new_create_images = """    def create_property_images(self, property_obj, prop_data):
        import random
        image_types = ['EXTERIOR', 'INTERIOR', 'ROOM', 'BATHROOM']
        
        if property_obj.property_type in ['APARTMENT', 'FLAT', 'STUDIO']:
            prefix = 'apt_'
        elif property_obj.property_type in ['HOSTEL', 'STUDENT_APARTMENT']:
            prefix = 'hstl_'
        else:
            prefix = 'oth_'
            
        for i, image_type in enumerate(image_types):
            img_idx = random.randint(0, 9)
            local_filename = f"{prefix}{img_idx}.jpg"
            image_path = f"property_images/{local_filename}"
            
            PropertyImage.objects.create(
                accommodation_property=property_obj,
                image=image_path,
                image_type=image_type,
                caption=f'{image_type.capitalize()} view of {property_obj.title}',
                is_primary=(i == 0),
                order=i
            )

    def get_image_keywords(self, property_obj, prop_data):
        return []"""

# Replace the two functions completely
# We know create_property_images starts at def create_property_images and get_image_keywords ends around line 433
pattern = r'    def create_property_images\(self, property_obj, prop_data\):.*?    def generate_ashanti_properties\(self\):'
new_text = new_create_images + '\n\n    def generate_ashanti_properties(self):'
content = re.sub(pattern, new_text, content, flags=re.DOTALL)

with open("properties/management/commands/populate_ghana_properties.py", "w") as f:
    f.write(content)
