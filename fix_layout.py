import re

with open('landing/templates/landing/property_detail.html', 'r') as f:
    content = f.read()

# Define regex patterns to extract sections
def extract_section(section_id):
    pattern = r'(<section id="' + section_id + r'".*?</section>)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1), match.span()
    return None, None

overview, span_o = extract_section('overview')
rooms, span_r = extract_section('rooms')
amenities, span_a = extract_section('amenities')
location, span_l = extract_section('location')
policies, span_p = extract_section('policies')
reviews, span_rev = extract_section('reviews')

if all([overview, rooms, amenities, location, policies, reviews]):
    # Find the bounds of all sections to replace them
    start_idx = min([s[0] for s in [span_o, span_r, span_a, span_l, span_p, span_rev]])
    end_idx = max([s[1] for s in [span_o, span_r, span_a, span_l, span_p, span_rev]])
    
    new_sections = (
        overview + "\n\n" +
        rooms + "\n\n" +
        amenities + "\n\n" +
        policies + "\n\n" +
        location + "\n\n" +
        reviews + "\n"
    )
    
    new_content = content[:start_idx] + new_sections + content[end_idx:]
    
    with open('landing/templates/landing/property_detail.html', 'w') as f:
        f.write(new_content)
    print("Successfully reordered sections.")
else:
    print("Could not find all sections.")
