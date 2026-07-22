import re
with open('landing/templates/landing/property_detail.html', 'r') as f:
    content = f.read()

# Fix gallery badge
content = re.sub(r'(\.pd-gallery-badge\s*\{[^}]*color:\s*)#111111', r'\1#FFFFFF', content)
content = re.sub(r'(\.pd-gallery-badge:hover\s*\{[^}]*color:\s*)#111111', r'\1#FFFFFF', content)

# Fix has-more
content = re.sub(r'(\.pd-bento-side\.has-more::after\s*\{[^}]*color:\s*)#111', r'\1#FFFFFF', content)

# Fix lightbox
content = re.sub(r'(\.pd-lightbox-close\s*\{[^}]*color:\s*)#111', r'\1#FFFFFF', content)

# Fix star rating capsule that overlays the image
content = re.sub(r'(\.rating-badge-capsule\s*\{[^}]*color:\s*)#111111', r'\1#FFFFFF', content)
content = re.sub(r'(\.rating-badge-capsule\s*\{[^}]*background:\s*)rgba\(255, 255, 255, 0.75\)', r'\1rgba(0, 0, 0, 0.75)', content)

# Fix heart circle
content = re.sub(r'(\.favorite-heart-circle\s*\{[^}]*color:\s*)#111111', r'\1#FFFFFF', content)
content = re.sub(r'(\.favorite-heart-circle\s*\{[^}]*background:\s*)rgba\(255, 255, 255, 0.75\)', r'\1rgba(0, 0, 0, 0.75)', content)

# Any other elements on dark backgrounds?
# Let's write it out and save.
with open('landing/templates/landing/property_detail.html', 'w') as f:
    f.write(content)
