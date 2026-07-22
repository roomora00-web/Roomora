with open('landing/templates/landing/property_detail.html', 'r') as f:
    lines = f.readlines()

def find_line(text, start=0):
    for i in range(start, len(lines)):
        if text in lines[i]:
            return i
    return -1

overview_start = find_line("<!-- ── SECTION 4: PROPERTY OVERVIEW")
rooms_start = find_line("<!-- ── SECTION 5: ROOM / UNIT TYPE CARDS")
location_start = find_line("<!-- ── SECTION 7: LOCATION & PROXIMITY")
amenities_start = find_line("<!-- ── SECTION 6: AMENITIES")
policies_start = find_line("<!-- ── SECTION 8: HOUSE RULES")
reviews_start = find_line("<!-- ── SECTION 9: REVIEWS")
end_start = find_line("<!-- ── SECTION 9: ROOMMATE MATCHING PREVIEW (REMOVED)")

overview = lines[overview_start:rooms_start]
rooms = lines[rooms_start:location_start]
location = lines[location_start:amenities_start]
amenities = lines[amenities_start:policies_start]
policies = lines[policies_start:reviews_start]
reviews = lines[reviews_start:end_start]

before = lines[:overview_start]
after = lines[end_start:]

# New order: Overview, Amenities, Rooms, Location, Reviews, Policies
new_lines = before + overview + amenities + rooms + location + reviews + policies + after

with open('landing/templates/landing/property_detail.html', 'w') as f:
    f.writelines(new_lines)
print("Reordered successfully!")
