import os
import re
import random

template_dir = 'landing/templates/landing'
image_dir = 'media/property_images'

# Get all valid local images
local_images = [f'/media/property_images/{f}' for f in os.listdir(image_dir) if f.endswith('.jpg') or f.endswith('.png')]

# Regex to find unsplash URLs
unsplash_pattern = re.compile(r'https://images\.unsplash\.com/[^\s\'"]+')

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            if unsplash_pattern.search(content):
                # Replace each match with a random local image
                def replace_func(match):
                    return random.choice(local_images)
                
                new_content = unsplash_pattern.sub(replace_func, content)
                
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Fixed {filepath}")

