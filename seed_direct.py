"""
Direct psycopg2 seed — Hostels 2 through 5.
Hostel 1 (HST-ACC-MLH-001) was already seeded by the Django script.
"""
import os
import shutil
import psycopg2
import datetime

DB_URL = (
    "postgresql://neondb_owner:npg_hfcSAEns58xB"
    "@ep-spring-frog-aweee9ze-pooler.c-12.us-east-1.aws.neon.tech"
    "/neondb?sslmode=require&channel_binding=require"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR  = os.path.join(BASE_DIR, "Properties00", "HOSTELS")
MEDIA_P  = os.path.join(BASE_DIR, "media", "property_images")
MEDIA_R  = os.path.join(BASE_DIR, "media", "room_images")
os.makedirs(MEDIA_P, exist_ok=True)
os.makedirs(MEDIA_R, exist_ok=True)

def cp(src, dst, media_dir):
    s = os.path.join(SRC_DIR, src)
    d = os.path.join(media_dir, dst)
    if os.path.exists(s):
        shutil.copy2(s, d)
    else:
        print(f"  [WARN] Missing source: {src}")
    folder = "property_images" if media_dir == MEDIA_P else "room_images"
    return f"{folder}/{dst}"

print("Connecting...")
conn = psycopg2.connect(DB_URL, connect_timeout=30)
conn.autocommit = False
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.timezone.utc)
print("Connected OK\n")

# ── Admin user ──────────────────────────────────────────────────────────
cur.execute("SELECT id FROM users WHERE is_superuser=TRUE ORDER BY id LIMIT 1;")
admin_id = (cur.fetchone() or [None])[0]
print(f"Admin ID: {admin_id}")

# ── Amenities ───────────────────────────────────────────────────────────
def am(name, cat):
    cur.execute("SELECT id FROM amenities WHERE LOWER(name)=LOWER(%s) LIMIT 1;", (name,))
    r = cur.fetchone()
    if r: return r[0]
    cur.execute(
        "INSERT INTO amenities(name,category,icon,description,created_at) VALUES(%s,%s,'','',%s) RETURNING id;",
        (name, cat, now))
    return cur.fetchone()[0]

W=am('Wi-Fi','INTERNET'); SE=am('24/7 Security','SAFETY'); WA=am('Water Supply','UTILITIES')
AC=am('Air Conditioning','GENERAL'); ST=am('Study Room','STUDY'); GN=am('Standby Generator','UTILITIES')
LA=am('Laundry Service','LAUNDRY'); CC=am('CCTV Surveillance','SAFETY'); KI=am('Communal Kitchen','KITCHEN')
FE=am('Perimeter Fence & Gate','SAFETY'); FA=am('Ceiling Fan','GENERAL'); PK=am('Car Parking','OUTDOOR')
print("Amenities OK\n")

# ── Helpers ─────────────────────────────────────────────────────────────
def del_existing(code):
    cur.execute("SELECT id FROM properties WHERE property_code=%s;", (code,))
    r = cur.fetchone()
    if not r:
        return
    pid = r[0]
    print(f"  [DEL] Cascading delete of {code} (id={pid})...")
    # Delete room images first (via rooms)
    cur.execute("""DELETE FROM properties_roomimage WHERE room_id IN
                   (SELECT id FROM rooms WHERE accommodation_property_id=%s);""", (pid,))
    # Delete rooms
    cur.execute("DELETE FROM rooms WHERE accommodation_property_id=%s;", (pid,))
    # Delete room type pricing (via room types)
    cur.execute("""DELETE FROM room_type_pricing WHERE room_type_id IN
                   (SELECT id FROM room_types WHERE accommodation_property_id=%s);""", (pid,))
    # Delete room types
    cur.execute("DELETE FROM room_types WHERE accommodation_property_id=%s;", (pid,))
    # Delete property images
    cur.execute("DELETE FROM property_images WHERE accommodation_property_id=%s;", (pid,))
    # Delete amenities
    cur.execute("DELETE FROM property_amenities WHERE accommodation_property_id=%s;", (pid,))
    # Delete proximity destinations
    cur.execute("DELETE FROM proximity_destinations WHERE accommodation_property_id=%s;", (pid,))
    # Now safe to delete property
    cur.execute("DELETE FROM properties WHERE id=%s;", (pid,))
    print(f"  [DEL] Removed {code} OK")

def insert_property(
        code, title, prop_type, cat, desc,
        address, city, region, postal_code, digital_address,
        lat, lon, total_area, total_floors,
        nearest_inst, distance, walking_time, nearby_landmarks,
        hostel_type, ownership_type,
        owner_name, owner_email, owner_phone,
        house_rules, visitor_policy, prohibited_items, emergency_contacts, cancellation_policy,
        cctv, security_personnel, gated_community,
        water_avail, electricity_stab, internet_avail,
        utility_billing, fire_safety, safety_score,
        smoking, pets, guests, max_guests,
        stu=True, wkr=False, ns_=False, sp=False, is_featured=False):
    del_existing(code)
    cur.execute("""
        INSERT INTO properties (
          property_code, property_type, property_category, title, description,
          address, city, region, country, postal_code, digital_address,
          latitude, longitude, total_area, total_floors,
          nearest_institution, distance_to_campus, walking_time_estimate, nearby_landmarks,
          hostel_type, ownership_type,
          owner_name, owner_email, owner_phone, uploaded_by_id,
          house_rules, visitor_policy, prohibited_items, emergency_contacts, cancellation_policy,
          rejection_reason,
          cctv, security_personnel, gated_community,
          water_availability, electricity_stability, internet_availability,
          utility_billing_method, fire_safety_compliance, safety_score,
          smoking_allowed, pets_allowed, guests_allowed, maximum_guests,
          suitable_for_students, suitable_for_workers, suitable_for_national_service,
          suitable_for_single_professionals, suitable_for_families,
          suitable_for_couples, suitable_for_expatriates, suitable_for_short_stay,
          is_available, is_verified, is_featured, status,
          views_count, saves_count, booking_requests_count,
          created_at, updated_at
        ) VALUES (
          %s,%s,%s,%s,%s,
          %s,%s,%s,'Ghana',%s,%s,
          %s,%s,%s,%s,
          %s,%s,%s,%s,
          %s,%s,
          %s,%s,%s,%s,
          %s,%s,%s,%s,%s,
          '',
          %s,%s,%s,
          %s,%s,%s,
          %s,%s,%s,
          %s,%s,%s,%s,
          %s,%s,%s,
          %s,%s,
          %s,%s,%s,
          TRUE,TRUE,%s,'APPROVED',
          0,0,0,
          %s,%s
        ) RETURNING id;
    """, (
        code, prop_type, cat, title, desc,
        address, city, region, postal_code, digital_address,
        lat, lon, total_area, total_floors,
        nearest_inst, distance, walking_time, nearby_landmarks,
        hostel_type, ownership_type,
        owner_name, owner_email, owner_phone, admin_id,
        house_rules, visitor_policy, prohibited_items, emergency_contacts, cancellation_policy,
        cctv, security_personnel, gated_community,
        water_avail, electricity_stab, internet_avail,
        utility_billing, fire_safety, safety_score,
        smoking, pets, guests, max_guests,
        stu, wkr, ns_, sp, False, False, False, False,
        is_featured, now, now
    ))
    return cur.fetchone()[0]

def add_ams(pid, am_ids):
    for aid in am_ids:
        cur.execute("""
            INSERT INTO property_amenities(accommodation_property_id,amenity_id,is_included,notes)
            VALUES(%s,%s,TRUE,'') ON CONFLICT(accommodation_property_id,amenity_id) DO NOTHING;
        """, (pid, aid))

def add_pi(pid, path, itype, caption, primary, order):
    cur.execute("""
        INSERT INTO property_images(accommodation_property_id,image,image_type,caption,is_primary,"order",uploaded_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s);
    """, (pid, path, itype, caption, primary, order, now))

def add_rt(pid, name, billing, occ, total_r, beds, cap, avail,
           fan=False, ac=False, wifi=True, desk=True, ward=True,
           pbath=False, sbath='', gender='ANY', lifestyle='BALANCED', srating=3):
    cur.execute("""
        INSERT INTO room_types(
          accommodation_property_id, room_type_name, billing_model,
          occupancy_type, total_rooms, beds_per_room, total_capacity,
          available_slots, occupied_slots,
          fan, air_conditioning, wifi_available, study_desk_available, wardrobe_available,
          private_bathroom, shared_bathroom_ratio, balcony, electricity_backup,
          gender_restriction, preferred_lifestyle, study_environment_rating,
          waiting_list_enabled, bed_type, created_at, updated_at
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s,%s,%s,%s,FALSE,FALSE,%s,%s,%s,FALSE,'SINGLE',%s,%s)
        RETURNING id;
    """, (pid, name, billing, occ, total_r, beds, cap, avail,
          fan, ac, wifi, desk, ward, pbath, sbath, gender, lifestyle, srating, now, now))
    return cur.fetchone()[0]

def add_pricing(rtid, ptype, sem=None, mon=None, yr=None, dep=None, reg=None, ayr=None):
    cur.execute("""
        INSERT INTO room_type_pricing(
          room_type_id, payment_type,
          monthly_price, semester_price, yearly_price, academic_year_price,
          daily_price, weekly_price, two_years_price,
          security_deposit, registration_fee, maintenance_fee, utility_fee,
          currency, max_semesters, min_months, max_months,
          grace_period_days, overstay_multiplier,
          allow_two_year_advance, early_checkout_allowed, allow_monthly_extensions
        ) VALUES(%s,%s,%s,%s,%s,%s,NULL,NULL,NULL,%s,%s,NULL,NULL,'GHS',3,1,12,7,1.5,FALSE,TRUE,FALSE)
        ON CONFLICT(room_type_id,payment_type) DO NOTHING;
    """, (rtid, ptype, mon, sem, yr, ayr, dep, reg))

def add_room(pid, rtid, num, floor, slots):
    cur.execute("""
        INSERT INTO rooms(accommodation_property_id,room_type_id,room_number,floor,
          total_slots,occupied_slots,pending_slots,status,notes,created_at,updated_at)
        VALUES(%s,%s,%s,%s,%s,0,0,'AVAILABLE','',%s,%s)
        ON CONFLICT(accommodation_property_id,room_number) DO NOTHING RETURNING id;
    """, (pid, rtid, num, floor, slots, now, now))
    r = cur.fetchone()
    if r: return r[0]
    cur.execute("SELECT id FROM rooms WHERE accommodation_property_id=%s AND room_number=%s;", (pid, num))
    return cur.fetchone()[0]

def add_ri(rid, path, itype, primary):
    cur.execute("""
        INSERT INTO properties_roomimage(room_id,image,image_type,is_primary,created_at)
        VALUES(%s,%s,%s,%s,%s);
    """, (rid, path, itype, primary, now))

def add_prox(pid, name, dtype, dist, ttime, mode, order):
    cur.execute("""
        INSERT INTO proximity_destinations(
          accommodation_property_id,destination_name,destination_type,
          distance_km,travel_time_minutes,travel_mode,notes,"order")
        VALUES(%s,%s,%s,%s,%s,%s,'',%s);
    """, (pid, name, dtype, dist, ttime, mode, order))


# ════════════════════════════════════════════════════════════════════════
# HOSTEL 2 — Pink Rose Student Hostel (Accra / Madina) — Girls Only
# ════════════════════════════════════════════════════════════════════════
print("[2/5] Pink Rose Student Hostel...")
p2 = insert_property(
    code="HST-ACC-PRH-002", title="Pink Rose Student Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc=(
        "Pink Rose Student Hostel is a vibrant, three-floor student residence located in Madina, "
        "approximately 10 minutes by trotro from the University of Ghana, Legon. The distinctively "
        "painted pink building is a well-known landmark in the community. The hostel caters primarily "
        "to female students, offering a safe, comfortable environment with 24-hour female-only security "
        "personnel, perimeter fencing, borehole water, and consistent power backed by a diesel generator. "
        "Communal kitchenettes are provided on each floor and Wi-Fi is available across the building. "
        "The hostel is walking distance to Madina Market, pharmacies, and major transport routes."
    ),
    address="Kotobabi Road, Near Madina Market", city="Madina", region="Greater Accra",
    postal_code="GA-721", digital_address="GA-721-5543",
    lat=5.681200, lon=-0.166900, total_area=600.0, total_floors=3,
    nearest_inst="University of Ghana (Legon)", distance=4.5, walking_time=55,
    nearby_landmarks="Madina Market, Madina Zongo Junction, Accra-Madina Highway",
    hostel_type="GIRLS_ONLY", ownership_type="PRIVATE",
    owner_name="Abena Osei-Agyeman", owner_email="info@pinkhostelgh.com", owner_phone="+233 24 533 9900",
    house_rules=(
        "Female residents ONLY — no male visitors on upper floors under any circumstance. "
        "Curfew strictly 9:30 PM (gates locked, reopened 6:00 AM). Cooking permitted ONLY in kitchenette "
        "areas; not in bedrooms. Rooms must be swept daily. Music kept to minimum at all times."
    ),
    visitor_policy=(
        "Female visitors only, 9:00 AM to 6:00 PM. All visitors register at the gate security post. "
        "Male visitors (fathers, brothers, deliveries) permitted in ground-floor reception only. "
        "No overnight visitors permitted."
    ),
    prohibited_items=(
        "No males beyond the ground-floor reception area. No alcohol, smoking, or drug use. "
        "No gas cylinders or hot plates in rooms. No pets. No excessively loud music."
    ),
    emergency_contacts=(
        "Pink Rose Security Desk (24/7): +233 24 533 9900. "
        "Hostel Matron (Maame Esi): +233 54 219 8876. "
        "Madina Police Station: +233 30 250 0800. Emergency: 112."
    ),
    cancellation_policy="Full refund 10 days before semester start. No refund after move-in.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole with Storage Tank (24/7)",
    electricity_stab="Medium (Generator backup, 20 min delay)",
    internet_avail="Wi-Fi — Ground & 1st Floor",
    utility_billing="INCLUDED_IN_RENT", fire_safety=True, safety_score=7,
    smoking=False, pets=False, guests=True, max_guests=1,
    stu=True, wkr=True, ns_=True, is_featured=False,
)
add_ams(p2, [W,SE,WA,GN,CC,FE,KI,FA,LA])
add_pi(p2, cp("images (8).jpeg",  "HST-ACC-PRH-002_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Pink Rose Hostel — Iconic Pink Building", True,  1)
add_pi(p2, cp("images (13).jpeg", "HST-ACC-PRH-002_ext_2.jpeg",    MEDIA_P), "EXTERIOR", "Hostel Exterior — Side View",            False, 2)
add_pi(p2, cp("images (16).jpeg", "HST-ACC-PRH-002_int_corridor.jpeg", MEDIA_P), "INTERIOR", "Well-Lit Hostel Corridor",           False, 3)
add_pi(p2, cp("images (14).jpeg", "HST-ACC-PRH-002_int_room.jpeg", MEDIA_P), "INTERIOR", "Standard Bedroom Interior",             False, 4)

rt2s = add_rt(p2, "Single Room (1-in-room) — Girls Only", "SEMESTER_BASED", "SINGLE", 10, 1, 10, 10,
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 4 Rooms",
              gender="FEMALE_ONLY", lifestyle="QUIET", srating=4)
add_pricing(rt2s, "SEMESTER", sem=2500.00, mon=625.00, dep=400.00, reg=100.00)

rt2d = add_rt(p2, "Double Room (2-in-room) — Girls Only", "SEMESTER_BASED", "DOUBLE", 18, 2, 36, 36,
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              gender="FEMALE_ONLY", lifestyle="BALANCED", srating=3)
add_pricing(rt2d, "SEMESTER", sem=1600.00, mon=400.00, dep=250.00, reg=80.00)

r2s1 = add_room(p2, rt2s, "S101", "1st Floor", 1)
add_ri(r2s1, cp("images (14).jpeg", "HST-ACC-PRH-002_rm_S101_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r2s1, cp("images (19).jpeg", "HST-ACC-PRH-002_rm_S101_2.jpeg", MEDIA_R), "BEDROOM", False)

r2d1 = add_room(p2, rt2d, "D201", "2nd Floor", 2)
add_ri(r2d1, cp("images (9).jpeg",  "HST-ACC-PRH-002_rm_D201_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r2d1, cp("images (6).jpeg",  "HST-ACC-PRH-002_rm_D201_2.jpeg", MEDIA_R), "BEDROOM", False)

r2d2 = add_room(p2, rt2d, "D202", "2nd Floor", 2)
add_ri(r2d2, cp("images (15).jpeg", "HST-ACC-PRH-002_rm_D202_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r2d2, cp("images (16).jpeg", "HST-ACC-PRH-002_rm_D202_2.jpeg", MEDIA_R), "BEDROOM", False)

add_prox(p2, "Madina Market",         "MARKET",      0.3, 4,  "WALK",   1)
add_prox(p2, "Madina Trotro Station", "TRANSPORT",   0.5, 6,  "WALK",   2)
add_prox(p2, "Madina Polyclinic",     "HOSPITAL",    1.2, 7,  "TROTRO", 3)
add_prox(p2, "University of Ghana",   "INSTITUTION", 4.5, 15, "TROTRO", 4)
conn.commit()
print(f"  [OK] p2 id={p2}")


# ════════════════════════════════════════════════════════════════════════
# HOSTEL 3 — Ayeduase Modern Hostel Block (Kumasi / KNUST)
# ════════════════════════════════════════════════════════════════════════
print("\n[3/5] Ayeduase Modern Hostel Block...")
p3 = insert_property(
    code="HST-KMS-AMH-003", title="Ayeduase Modern Hostel Block",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc=(
        "Ayeduase Modern Hostel Block is a newly developed student accommodation facility nestled in the "
        "heart of Ayeduase, one of the most popular student communities adjacent to KNUST in Kumasi. "
        "The three-storey stone-clad building offers comfortable accommodation for both male and female "
        "students with dedicated floor sections per gender. Each floor is equipped with a kitchenette, "
        "modern washrooms, study nooks, and a communal living area. The property has 24-hour security "
        "personnel, CCTV, and a fully gated compound with off-street parking. High-speed Wi-Fi is "
        "available across all floors, and the standby generator ensures continuous power."
    ),
    address="Ayeduase Road, Off KNUST Main Road", city="Kumasi", region="Ashanti",
    postal_code="AK-541", digital_address="AK-541-6789",
    lat=6.676300, lon=-1.574800, total_area=750.0, total_floors=3,
    nearest_inst="KNUST", distance=0.7, walking_time=8,
    nearby_landmarks="KNUST Commercial Area, Ayeduase Market, KNUST Sports Stadium",
    hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Emmanuel Boateng", owner_email="manager@ayeduasehostel.com", owner_phone="+233 27 644 5511",
    house_rules=(
        "Quiet hours: 10:00 PM – 5:30 AM weekdays; 11:00 PM – 7:00 AM weekends. "
        "Tenants must carry ID at the security gate at all times. Cooking ONLY in floor kitchenettes. "
        "Electrical appliances above 1000W are strictly prohibited."
    ),
    visitor_policy=(
        "Visitors allowed 8:00 AM – 8:00 PM only. "
        "Male visitors not permitted on female floors and vice versa. "
        "All visitors must sign in at the gate and show valid ID. No overnight visitors."
    ),
    prohibited_items=(
        "No smoking, alcohol, or narcotics on the premises. "
        "No gas cylinders, kerosene stoves, or open-flame cooking. "
        "No pets. No loud music between 9:00 PM and 7:00 AM. No high-wattage appliances."
    ),
    emergency_contacts=(
        "Hostel Security Desk (24/7): +233 27 644 5511. "
        "Manager (Emmanuel Boateng): +233 27 644 5511. "
        "KNUST Security: +233 32 206 0555. Emergency: 112."
    ),
    cancellation_policy="Full refund 14 days before semester. 50% within 7 days. No refund after move-in.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Municipal + Overhead Tank Backup (24/7)",
    electricity_stab="High (Generator kicks in under 5 min)",
    internet_avail="Fibre Wi-Fi — All 3 Floors",
    utility_billing="INCLUDED_IN_RENT", fire_safety=True, safety_score=9,
    smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, wkr=False, ns_=True, is_featured=True,
)
add_ams(p3, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK])
add_pi(p3, cp("images (2).jpeg",  "HST-KMS-AMH-003_ext_main.jpeg",     MEDIA_P), "EXTERIOR", "Ayeduase Hostel Block — Exterior", True,  1)
add_pi(p3, cp("images (12).jpeg", "HST-KMS-AMH-003_ext_2.jpeg",         MEDIA_P), "EXTERIOR", "Hostel — Side View with Balconies", False, 2)
add_pi(p3, cp("images (16).jpeg", "HST-KMS-AMH-003_int_corridor.jpeg",  MEDIA_P), "INTERIOR", "Interior Corridor",                False, 3)
add_pi(p3, cp("images (20).jpeg", "HST-KMS-AMH-003_int_room.jpeg",      MEDIA_P), "INTERIOR", "Well-Furnished Hostel Room",       False, 4)

rt3d = add_rt(p3, "Double Room (2-in-room)", "SEMESTER_BASED", "DOUBLE", 25, 2, 50, 50,
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              gender="ANY", lifestyle="BALANCED", srating=4)
add_pricing(rt3d, "SEMESTER", sem=2200.00, mon=550.00, dep=350.00, reg=100.00)

rt3t = add_rt(p3, "Triple Room (3-in-room)", "SEMESTER_BASED", "TRIPLE", 10, 3, 30, 30,
              fan=True, wifi=True, desk=True, ward=False, pbath=False, sbath="1 per 3 Rooms",
              gender="ANY", lifestyle="SOCIAL", srating=3)
add_pricing(rt3t, "SEMESTER", sem=1600.00, mon=400.00, dep=250.00, reg=80.00)

r3d1 = add_room(p3, rt3d, "D101", "1st Floor", 2)
add_ri(r3d1, cp("images (5).jpeg",  "HST-KMS-AMH-003_rm_D101_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r3d1, cp("images (16).jpeg", "HST-KMS-AMH-003_rm_D101_2.jpeg", MEDIA_R), "BEDROOM", False)

r3d2 = add_room(p3, rt3d, "D201", "2nd Floor", 2)
add_ri(r3d2, cp("images (3).jpeg",  "HST-KMS-AMH-003_rm_D201_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r3d2, cp("images (20).jpeg", "HST-KMS-AMH-003_rm_D201_2.jpeg", MEDIA_R), "BEDROOM", False)

r3t1 = add_room(p3, rt3t, "T301", "3rd Floor", 3)
add_ri(r3t1, cp("images (1).jpeg", "HST-KMS-AMH-003_rm_T301_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r3t1, cp("images (9).jpeg", "HST-KMS-AMH-003_rm_T301_2.jpeg", MEDIA_R), "BEDROOM", False)

add_prox(p3, "KNUST Main Gate",    "INSTITUTION", 0.7, 8, "WALK",   1)
add_prox(p3, "Ayeduase Market",    "MARKET",      0.3, 4, "WALK",   2)
add_prox(p3, "Ayeduase Taxi Rank", "TRANSPORT",   0.4, 5, "WALK",   3)
add_prox(p3, "KNUST Hospital",     "HOSPITAL",    1.5, 6, "TAXI",   4)
conn.commit()
print(f"  [OK] p3 id={p3}")


# ════════════════════════════════════════════════════════════════════════
# HOSTEL 4 — Sunrise Orange Hostel (Kumasi / Kotei)
# ════════════════════════════════════════════════════════════════════════
print("\n[4/5] Sunrise Orange Hostel...")
p4 = insert_property(
    code="HST-KMS-SOH-004", title="Sunrise Orange Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc=(
        "Sunrise Orange Hostel is a secure and affordable student residence located in Kotei, "
        "a vibrant student-dominated neighbourhood approximately 10 minutes by trotro from KNUST. "
        "Identifiable by its distinctive orange exterior walls and razor-wire security fencing, the "
        "hostel provides a structured and safe living environment for both male and female students on "
        "separate floors. Amenities include a borehole water system, standby generator, communal "
        "kitchenettes, clean shared washrooms serviced daily, and Wi-Fi internet. The hostel is close "
        "to provision shops, print centres, pharmacies, and the Kotei Market."
    ),
    address="Kotei-Deduako Road, Near Kotei Market", city="Kumasi", region="Ashanti",
    postal_code="AK-312", digital_address="AK-312-9901",
    lat=6.693100, lon=-1.591400, total_area=500.0, total_floors=3,
    nearest_inst="KNUST", distance=3.2, walking_time=38,
    nearby_landmarks="Kotei Market, Deduako Roundabout, Suame Magazine",
    hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Yaw Asiedu-Mensah", owner_email="yaw.asiedu@sunriseghostel.com", owner_phone="+233 55 312 7733",
    house_rules=(
        "Curfew: Gate locks at 10:00 PM, reopens at 6:00 AM. Carry hostel ID at all times. "
        "Communal cooking areas must be cleaned after each use. Waste in designated bins. "
        "No noise after 10:00 PM."
    ),
    visitor_policy=(
        "Visitors permitted between 9:00 AM and 7:00 PM. "
        "Opposite-gender visitors restricted to ground-floor reception. "
        "All visitors must sign the visitor register at the security post. No overnight visitors."
    ),
    prohibited_items=(
        "No smoking or alcohol on the premises. No gas cylinders or open-flame cooking in rooms. "
        "No pets. No loud music or entertainment systems after 10:00 PM."
    ),
    emergency_contacts=(
        "Sunrise Security Desk (24/7): +233 55 312 7733. Manager (Yaw): +233 55 312 7733. "
        "Kotei Police Post: +233 32 202 7100. Emergency: 112."
    ),
    cancellation_policy="Full refund 10 days before semester. 50% within 5 days. No refund after move-in.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole with Overhead Tank (24/7)",
    electricity_stab="Medium (Generator, 10 min switchover)",
    internet_avail="Wi-Fi — Ground & 1st Floor",
    utility_billing="INCLUDED_IN_RENT", fire_safety=False, safety_score=7,
    smoking=False, pets=False, guests=True, max_guests=1,
    stu=True, wkr=True, is_featured=False,
)
add_ams(p4, [W,SE,WA,GN,CC,FE,KI,FA])
add_pi(p4, cp("images (7).jpeg",  "HST-KMS-SOH-004_ext_main.jpeg",  MEDIA_P), "EXTERIOR", "Sunrise Orange Hostel — Exterior View",  True,  1)
add_pi(p4, cp("images (18).jpeg", "HST-KMS-SOH-004_ext_2.jpeg",     MEDIA_P), "EXTERIOR", "Hostel Compound & Entrance",             False, 2)
add_pi(p4, cp("images (17).jpeg", "HST-KMS-SOH-004_int_room.jpeg",  MEDIA_P), "INTERIOR", "Student Room — Wardrobe & Bunk",         False, 3)
add_pi(p4, cp("images (20).jpeg", "HST-KMS-SOH-004_int_room2.jpeg", MEDIA_P), "INTERIOR", "Double Bed Room Interior",               False, 4)

rt4s = add_rt(p4, "Single Room (1-in-room)", "SEMESTER_BASED", "SINGLE", 8, 1, 8, 8,
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 5 Rooms",
              gender="ANY", lifestyle="QUIET", srating=4)
add_pricing(rt4s, "SEMESTER", sem=2400.00, mon=600.00, dep=350.00, reg=100.00)

rt4d = add_rt(p4, "Double Room (2-in-room)", "SEMESTER_BASED", "DOUBLE", 16, 2, 32, 32,
              fan=True, wifi=True, desk=True, ward=False, pbath=False, sbath="1 per 4 Rooms",
              gender="ANY", lifestyle="BALANCED", srating=3)
add_pricing(rt4d, "SEMESTER", sem=1700.00, mon=425.00, dep=250.00, reg=80.00)

r4s1 = add_room(p4, rt4s, "S101", "1st Floor", 1)
add_ri(r4s1, cp("images (19).jpeg", "HST-KMS-SOH-004_rm_S101_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r4s1, cp("images.jpeg",      "HST-KMS-SOH-004_rm_S101_2.jpeg", MEDIA_R), "BEDROOM", False)

r4d1 = add_room(p4, rt4d, "D201", "2nd Floor", 2)
add_ri(r4d1, cp("images (17).jpeg", "HST-KMS-SOH-004_rm_D201_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r4d1, cp("images (15).jpeg", "HST-KMS-SOH-004_rm_D201_2.jpeg", MEDIA_R), "BEDROOM", False)

r4d2 = add_room(p4, rt4d, "D202", "2nd Floor", 2)
add_ri(r4d2, cp("images (4).jpeg",  "HST-KMS-SOH-004_rm_D202_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r4d2, cp("images (3).jpeg",  "HST-KMS-SOH-004_rm_D202_2.jpeg", MEDIA_R), "BEDROOM", False)

add_prox(p4, "Kotei Market",          "MARKET",      0.2, 3,  "WALK",   1)
add_prox(p4, "Kotei Trotro Stop",     "TRANSPORT",   0.3, 4,  "WALK",   2)
add_prox(p4, "Deduako Health Centre", "HOSPITAL",    1.0, 5,  "TAXI",   3)
add_prox(p4, "KNUST (Kumasi)",        "INSTITUTION", 3.2, 12, "TROTRO", 4)
conn.commit()
print(f"  [OK] p4 id={p4}")


# ════════════════════════════════════════════════════════════════════════
# HOSTEL 5 — White Block Executive Hostel (Kumasi / KNUST Extension)
# ════════════════════════════════════════════════════════════════════════
print("\n[5/5] White Block Executive Hostel...")
p5 = insert_property(
    code="HST-KMS-WBE-005", title="White Block Executive Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc=(
        "White Block Executive Hostel is a premium student accommodation facility near KNUST, designed "
        "for students who value quality and modern amenities. The newly-built white-plastered four-storey "
        "building features air-conditioned rooms, tiled floors, 24-hour fibre Wi-Fi, and private ensuite "
        "bathrooms for executive single occupants. A 60KVA generator provides uninterrupted electricity, "
        "and triple-filtered borehole water ensures clean water at all times. Each room features a study "
        "desk, wardrobe, reading lamp, and window blinds. The hostel also features a dedicated car park, "
        "communal lounge with TV, and weekly room cleaning service included in the rent."
    ),
    address="KNUST Extension Road, Off Bomso Junction", city="Kumasi", region="Ashanti",
    postal_code="AK-780", digital_address="AK-780-3321",
    lat=6.671800, lon=-1.562400, total_area=900.0, total_floors=4,
    nearest_inst="KNUST", distance=1.5, walking_time=18,
    nearby_landmarks="Bomso Junction, KNUST Extension, Asokwa Market",
    hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Dr. Kofi Owusu-Mensah", owner_email="admin@whiteblockexecutive.com", owner_phone="+233 20 977 4456",
    house_rules=(
        "Absolute quiet hours from 11:00 PM to 7:00 AM. All tenants sign a lease on check-in. "
        "Monthly room inspections. No cooking in rooms — use the communal kitchenette. "
        "AC must be switched off when leaving the room."
    ),
    visitor_policy=(
        "Visitors allowed between 10:00 AM and 8:00 PM. Sign in at reception with valid photo ID. "
        "Visitors use the ground-floor lounge only. No overnight visitors."
    ),
    prohibited_items=(
        "No smoking anywhere in the building. No alcohol or drug use. "
        "No gas cylinders or hot plates in rooms. No pets. "
        "No modification to furniture, fixtures, or room layout without approval."
    ),
    emergency_contacts=(
        "White Block Reception (24/7): +233 20 977 4456. "
        "Building Manager (Dr. Kofi): +233 20 977 4456. "
        "KNUST Security: +233 32 206 0555. KATH: +233 32 202 2301. Emergency: 112."
    ),
    cancellation_policy="Full refund 21 days before semester start. No refund after move-in.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Triple-Filtered Borehole (24/7)",
    electricity_stab="Very High (60KVA Generator)",
    internet_avail="Fibre Wi-Fi — All Rooms & Common Areas",
    utility_billing="INCLUDED_IN_RENT", fire_safety=True, safety_score=9,
    smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, wkr=True, sp=True, is_featured=True,
)
add_ams(p5, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK,LA])
add_pi(p5, cp("images (12).jpeg", "HST-KMS-WBE-005_ext_main.jpeg",   MEDIA_P), "EXTERIOR", "White Block Executive Hostel — Exterior", True,  1)
add_pi(p5, cp("images (10).jpeg", "HST-KMS-WBE-005_ext_2.jpeg",      MEDIA_P), "EXTERIOR", "Hostel Campus — Full Block View",         False, 2)
add_pi(p5, cp("images (15).jpeg", "HST-KMS-WBE-005_int_room.jpeg",   MEDIA_P), "INTERIOR", "Executive Room — AC & Study Desk",        False, 3)
add_pi(p5, cp("images (16).jpeg", "HST-KMS-WBE-005_int_lounge.jpeg", MEDIA_P), "INTERIOR", "Communal Lounge Area",                    False, 4)
add_pi(p5, cp("images (14).jpeg", "HST-KMS-WBE-005_int_bedroom.jpeg",MEDIA_P), "INTERIOR", "Executive Single Bedroom",                False, 5)

rt5e = add_rt(p5, "Executive Single (1-in-room Ensuite)", "SEMESTER_BASED", "SINGLE", 20, 1, 20, 20,
              ac=True, wifi=True, desk=True, ward=True, pbath=True, sbath="",
              gender="ANY", lifestyle="QUIET", srating=5)
add_pricing(rt5e, "SEMESTER", sem=4500.00, mon=1125.00, dep=700.00, reg=200.00)
add_pricing(rt5e, "YEARLY",   yr=8200.00, ayr=8200.00, dep=700.00, reg=200.00)

rt5d = add_rt(p5, "Standard Double (2-in-room)", "SEMESTER_BASED", "DOUBLE", 15, 2, 30, 30,
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 Ensuite per 2 Rooms",
              gender="ANY", lifestyle="BALANCED", srating=4)
add_pricing(rt5d, "SEMESTER", sem=3000.00, mon=750.00, dep=450.00, reg=150.00)

r5e1 = add_room(p5, rt5e, "E101", "1st Floor", 1)
add_ri(r5e1, cp("images (15).jpeg", "HST-KMS-WBE-005_rm_E101_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r5e1, cp("images (14).jpeg", "HST-KMS-WBE-005_rm_E101_2.jpeg", MEDIA_R), "BEDROOM", False)

r5e2 = add_room(p5, rt5e, "E201", "2nd Floor", 1)
add_ri(r5e2, cp("images (16).jpeg", "HST-KMS-WBE-005_rm_E201_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r5e2, cp("images.jpeg",      "HST-KMS-WBE-005_rm_E201_2.jpeg", MEDIA_R), "BEDROOM", False)

r5d1 = add_room(p5, rt5d, "D301", "3rd Floor", 2)
add_ri(r5d1, cp("images (5).jpeg",  "HST-KMS-WBE-005_rm_D301_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r5d1, cp("images (3).jpeg",  "HST-KMS-WBE-005_rm_D301_2.jpeg", MEDIA_R), "BEDROOM", False)

r5d2 = add_room(p5, rt5d, "D302", "3rd Floor", 2)
add_ri(r5d2, cp("images (4).jpeg",  "HST-KMS-WBE-005_rm_D302_1.jpeg", MEDIA_R), "BEDROOM", True)
add_ri(r5d2, cp("images (17).jpeg", "HST-KMS-WBE-005_rm_D302_2.jpeg", MEDIA_R), "BEDROOM", False)

add_prox(p5, "KNUST Main Campus",               "INSTITUTION", 1.5, 6,  "TAXI",   1)
add_prox(p5, "Bomso Junction",                  "TRANSPORT",   0.3, 4,  "WALK",   2)
add_prox(p5, "Asokwa Market",                   "MARKET",      1.0, 5,  "TROTRO", 3)
add_prox(p5, "Komfo Anokye Teaching Hospital",  "HOSPITAL",    4.5, 15, "TAXI",   4)
add_prox(p5, "Asokwa Shopping Mall",            "SHOPPING",    1.2, 6,  "TROTRO", 5)
conn.commit()
print(f"  [OK] p5 id={p5}")


# ─── Final Summary ────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
codes = ["HST-ACC-MLH-001","HST-ACC-PRH-002","HST-KMS-AMH-003","HST-KMS-SOH-004","HST-KMS-WBE-005"]
for code in codes:
    cur.execute("SELECT id,title,city,status FROM properties WHERE property_code=%s;", (code,))
    r = cur.fetchone()
    if not r:
        print(f"  [{code}] NOT FOUND")
        continue
    pid, title, city, status = r
    cur.execute("SELECT COUNT(*) FROM rooms WHERE accommodation_property_id=%s;", (pid,))
    rc = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM property_images WHERE accommodation_property_id=%s;", (pid,))
    pc = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM properties_roomimage WHERE room_id IN (SELECT id FROM rooms WHERE accommodation_property_id=%s);", (pid,))
    rmc = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM property_amenities WHERE accommodation_property_id=%s;", (pid,))
    amc = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM proximity_destinations WHERE accommodation_property_id=%s;", (pid,))
    prc = cur.fetchone()[0]
    print(f"\n  [{code}] {title} ({city}) — {status}")
    print(f"    Rooms:{rc} | PropImgs:{pc} | RoomImgs:{rmc} | Amenities:{amc} | Proximity:{prc}")

conn.close()
print("\n✅ ALL 5 HOSTELS SEEDED SUCCESSFULLY!")
