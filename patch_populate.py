with open("properties/management/commands/populate_ghana_properties.py", "r") as f:
    content = f.read()

import re

# We will replace the generate_* functions to just slice their return values.
# Wait, let's just do it directly.
# Replace `return [` with `return [` but then slice it.
# Actually, the simplest way to trim to 20 properties is to change `get_all_ghana_properties`.

new_get_all = """    def get_all_ghana_properties(self):
        \"\"\"Generate exactly 20 properties\"\"\"
        all_properties = []
        
        all_properties.extend(self.generate_greater_accra_properties()[:3])
        all_properties.extend(self.generate_ashanti_properties()[:2])
        all_properties.extend(self.generate_central_properties()[:2])
        
        # 1 each for the other 13 regions
        all_properties.extend(self.generate_brong_ahafo_properties()[:1])
        all_properties.extend(self.generate_eastern_properties()[:1])
        all_properties.extend(self.generate_northern_properties()[:1])
        all_properties.extend(self.generate_upper_east_properties()[:1])
        all_properties.extend(self.generate_upper_west_properties()[:1])
        all_properties.extend(self.generate_volta_properties()[:1])
        all_properties.extend(self.generate_western_properties()[:1])
        all_properties.extend(self.generate_ahafo_properties()[:1])
        all_properties.extend(self.generate_bono_east_properties()[:1])
        all_properties.extend(self.generate_north_east_properties()[:1])
        all_properties.extend(self.generate_oti_properties()[:1])
        all_properties.extend(self.generate_savannah_properties()[:1])
        all_properties.extend(self.generate_western_north_properties()[:1])
        
        return all_properties"""

# Find the def get_all_ghana_properties block and replace it
content = re.sub(r'    def get_all_ghana_properties.*?return all_properties', new_get_all, content, flags=re.DOTALL)

# Now rewrite create_property_images
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
            )"""

content = re.sub(r'    def create_property_images.*?        return keywords', new_create_images + '\n\n    def get_image_keywords(self, property_obj, prop_data):\n        return []', content, flags=re.DOTALL)

# Add code to clear the DB at the start of handle
content = content.replace("self.create_amenities()", "self.stdout.write('Clearing existing properties...')\\n        Property.objects.all().delete()\\n        self.create_amenities()")

with open("properties/management/commands/populate_ghana_properties.py", "w") as f:
    f.write(content)
