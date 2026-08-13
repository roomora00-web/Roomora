"""
Enforces the exact Room Slot Principle across all 7 regional hostels:
1 in a room = 1 bed = 1 slot left (total_capacity = 1, available_slots = 1)
2 in a room = 2 beds = 2 slots left (total_capacity = 2, available_slots = 2)
3 in a room = 3 beds = 3 slots left (total_capacity = 3, available_slots = 3)

Also ensures ALL 7 properties are set to APPROVED & is_available = True across Ghana's 7 key regions.
"""
import os
import sys
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

sys.stdout.reconfigure(encoding='utf-8')

def cp(src, dst, media_dir):
    s = os.path.join(SRC_DIR, src)
    d = os.path.join(media_dir, dst)
    if os.path.exists(s):
        shutil.copy2(s, d)
    else:
        print(f"  [WARN] Missing source: {src}")
    folder = "property_images" if media_dir == MEDIA_P else "room_images"
    return f"{folder}/{dst}"

print("="*70)
print("CONNECTING TO NEON DATABASE...")
print("="*70)
conn = psycopg2.connect(DB_URL, connect_timeout=30)
conn.autocommit = False
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.timezone.utc)
print("Connected successfully!\n")

# Admin user
cur.execute("SELECT id FROM users WHERE is_superuser=TRUE ORDER BY id LIMIT 1;")
admin_id = (cur.fetchone() or [None])[0]

# Amenities
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

# Cascade deletion
def del_property_by_code(code):
    cur.execute("SELECT id FROM properties WHERE property_code=%s;", (code,))
    rows = cur.fetchall()
    for r in rows:
        pid = r[0]
        cur.execute("DELETE FROM properties_roomimage WHERE room_id IN (SELECT id FROM rooms WHERE accommodation_property_id=%s);", (pid,))
        cur.execute("DELETE FROM rooms WHERE accommodation_property_id=%s;", (pid,))
        cur.execute("DELETE FROM room_type_pricing WHERE room_type_id IN (SELECT id FROM room_types WHERE accommodation_property_id=%s);", (pid,))
        cur.execute("DELETE FROM room_types WHERE accommodation_property_id=%s;", (pid,))
        cur.execute("DELETE FROM property_images WHERE accommodation_property_id=%s;", (pid,))
        cur.execute("DELETE FROM property_amenities WHERE accommodation_property_id=%s;", (pid,))
        cur.execute("DELETE FROM proximity_destinations WHERE accommodation_property_id=%s;", (pid,))
        cur.execute("DELETE FROM properties WHERE id=%s;", (pid,))
        print(f"  [DEL] Removed property {code}")

cur.execute("SELECT property_code FROM properties WHERE property_code IS NOT NULL;")
all_codes = [r[0] for r in cur.fetchall()]
for c in set(all_codes):
    del_property_by_code(c)
conn.commit()

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

def add_rt_option(pid, rt_name, billing, occ, beds_per_room, room_num,
                  fan=False, ac=False, wifi=True, desk=True, ward=True,
                  pbath=False, sbath='', gender='ANY', lifestyle='BALANCED', srating=3,
                  sem_price=None, mon_price=None, yr_price=None, dep=None, reg=None,
                  img1=None, img2=None):
    
    # 1 in a room = 1 bed = 1 slot left (total_capacity = 1, available_slots = 1)
    # 2 in a room = 2 beds = 2 slots left (total_capacity = 2, available_slots = 2)
    # 3 in a room = 3 beds = 3 slots left (total_capacity = 3, available_slots = 3)
    total_rooms = 1
    total_capacity = beds_per_room
    available_slots = beds_per_room

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
    """, (pid, rt_name, billing, occ, total_rooms, beds_per_room, total_capacity,
          available_slots, fan, ac, wifi, desk, ward, pbath, sbath, gender, lifestyle, srating, now, now))
    rt_id = cur.fetchone()[0]

    # Add Pricing
    cur.execute("""
        INSERT INTO room_type_pricing(
          room_type_id, payment_type,
          monthly_price, semester_price, yearly_price, academic_year_price,
          daily_price, weekly_price, two_years_price,
          security_deposit, registration_fee, maintenance_fee, utility_fee,
          currency, max_semesters, min_months, max_months,
          grace_period_days, overstay_multiplier,
          allow_two_year_advance, early_checkout_allowed, allow_monthly_extensions
        ) VALUES(%s,'SEMESTER',%s,%s,%s,NULL,NULL,NULL,NULL,%s,%s,NULL,NULL,'GHS',3,1,12,7,1.5,FALSE,TRUE,FALSE);
    """, (rt_id, mon_price, sem_price, yr_price, dep, reg))

    # Create 1 physical room with total_slots = beds_per_room
    cur.execute("""
        INSERT INTO rooms(accommodation_property_id,room_type_id,room_number,floor,
          total_slots,occupied_slots,pending_slots,status,notes,created_at,updated_at)
        VALUES(%s,%s,%s,'1st Floor',%s,0,0,'AVAILABLE','',%s,%s)
        RETURNING id;
    """, (pid, rt_id, room_num, beds_per_room, now, now))
    rid = cur.fetchone()[0]

    if img1:
        cur.execute("""
            INSERT INTO properties_roomimage(room_id,image,image_type,is_primary,created_at)
            VALUES(%s,%s,'BEDROOM',TRUE,%s);
        """, (rid, img1, now))
    if img2:
        cur.execute("""
            INSERT INTO properties_roomimage(room_id,image,image_type,is_primary,created_at)
            VALUES(%s,%s,'BEDROOM',FALSE,%s);
        """, (rid, img2, now))

    return rt_id

def add_prox(pid, name, dtype, dist, ttime, mode, order):
    cur.execute("""
        INSERT INTO proximity_destinations(
          accommodation_property_id,destination_name,destination_type,
          distance_km,travel_time_minutes,travel_mode,notes,"order")
        VALUES(%s,%s,%s,%s,%s,%s,'',%s);
    """, (pid, name, dtype, dist, ttime, mode, order))


# =========================================================================
# 1. ACCRA (Greater Accra Region) — Millennium Light Hostel
# =========================================================================
print("[1/7] Millennium Light Hostel (Accra / Legon)...")
p1 = insert_property(
    code="HST-ACC-MLH-001", title="Millennium Light Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Millennium Light Hostel is a premier student residence located 3 minutes walk from UG Legon campus. Features 24/7 security, standby generator, borehole water system, and fibre Wi-Fi.",
    address="Legon Campus Road, Behind Volta Hall", city="Accra", region="Greater Accra",
    postal_code="GA-489", digital_address="GA-489-2231",
    lat=5.648900, lon=-0.187100, total_area=820.0, total_floors=4,
    nearest_inst="University of Ghana (Legon)", distance=0.3, walking_time=3,
    nearby_landmarks="Volta Hall, Commonwealth Hall, Legon Botanical Gardens",
    hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Nana Kofi Asante", owner_email="manager@millenniumlighthostel.com", owner_phone="+233 20 811 4422",
    house_rules="Quiet hours 10 PM - 6 AM. ID required at gate.", visitor_policy="Visitors 8 AM - 7 PM only.",
    prohibited_items="No smoking, alcohol, narcotics, or pets.", emergency_contacts="Security (24/7): +233 20 811 4422.",
    cancellation_policy="Full refund 14 days before semester start.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole with Overhead Tank (24/7)", electricity_stab="High (Generator Available)",
    internet_avail="Fibre Wi-Fi — All Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=9, smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, ns_=True, is_featured=True,
)
add_ams(p1, [W,SE,WA,GN,CC,FE,KI,FA,ST])
add_pi(p1, cp("images (18).jpeg", "HST-ACC-MLH-001_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Front View", True, 1)
add_pi(p1, cp("images (7).jpeg",  "HST-ACC-MLH-001_ext_2.jpeg",    MEDIA_P), "EXTERIOR", "Exterior & Gated Compound", False, 2)

# 1 in a room option -> 1 bed -> 1 slot left
add_rt_option(p1, "Single Room (1 in a Room)", "SEMESTER_BASED", "SINGLE", 1, "S101",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 4 Rooms",
              sem_price=2800.00, mon_price=700.00, dep=500.00, reg=150.00,
              img1=cp("images (19).jpeg", "HST-ACC-MLH-001_rm_S_1.jpeg", MEDIA_R),
              img2=cp("images (11).jpeg", "HST-ACC-MLH-001_rm_S_2.jpeg", MEDIA_R))

# 2 in a room option -> 2 beds -> 2 slots left
add_rt_option(p1, "Double Room (2 in a Room)", "SEMESTER_BASED", "DOUBLE", 2, "D201",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              sem_price=1800.00, mon_price=450.00, dep=300.00, reg=100.00,
              img1=cp("images (1).jpeg", "HST-ACC-MLH-001_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (4).jpeg", "HST-ACC-MLH-001_rm_D_2.jpeg", MEDIA_R))

add_prox(p1, "University of Ghana Main Gate", "INSTITUTION", 0.3, 3, "WALK", 1)
conn.commit()


# =========================================================================
# 2. MADINA / ACCRA (Greater Accra Region) — Pink Rose Student Hostel
# =========================================================================
print("[2/7] Pink Rose Student Hostel (Madina / Accra)...")
p2 = insert_property(
    code="HST-ACC-PRH-002", title="Pink Rose Student Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Pink Rose Student Hostel is a vibrant female-only student residence in Madina, near UG Legon and UPSA.",
    address="Kotobabi Road, Near Madina Market", city="Madina", region="Greater Accra",
    postal_code="GA-721", digital_address="GA-721-5543",
    lat=5.681200, lon=-0.166900, total_area=600.0, total_floors=3,
    nearest_inst="University of Ghana (Legon)", distance=4.5, walking_time=55,
    nearby_landmarks="Madina Market, UPSA", hostel_type="GIRLS_ONLY", ownership_type="PRIVATE",
    owner_name="Abena Osei-Agyeman", owner_email="info@pinkhostelgh.com", owner_phone="+233 24 533 9900",
    house_rules="Female residents only. Curfew 9:30 PM.", visitor_policy="Female visitors 9 AM - 6 PM.",
    prohibited_items="No males on upper floors.", emergency_contacts="Security (24/7): +233 24 533 9900.",
    cancellation_policy="Full refund 10 days before semester.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole with Storage Tank (24/7)", electricity_stab="Medium (Generator backup)",
    internet_avail="Wi-Fi — All Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=8, smoking=False, pets=False, guests=True, max_guests=1,
    stu=True, wkr=True, ns_=True, is_featured=False,
)
add_ams(p2, [W,SE,WA,GN,CC,FE,KI,FA,LA])
add_pi(p2, cp("images (8).jpeg",  "HST-ACC-PRH-002_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Iconic Pink Building", True, 1)

add_rt_option(p2, "Single Room — Girls Only", "SEMESTER_BASED", "SINGLE", 1, "S101",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 4 Rooms",
              gender="FEMALE_ONLY", sem_price=2500.00, mon_price=625.00, dep=400.00, reg=100.00,
              img1=cp("images (14).jpeg", "HST-ACC-PRH-002_rm_S_1.jpeg", MEDIA_R),
              img2=cp("images (19).jpeg", "HST-ACC-PRH-002_rm_S_2.jpeg", MEDIA_R))

add_rt_option(p2, "Double Room — Girls Only", "SEMESTER_BASED", "DOUBLE", 2, "D201",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              gender="FEMALE_ONLY", sem_price=1600.00, mon_price=400.00, dep=250.00, reg=80.00,
              img1=cp("images (9).jpeg", "HST-ACC-PRH-002_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (6).jpeg", "HST-ACC-PRH-002_rm_D_2.jpeg", MEDIA_R))

add_prox(p2, "Madina Market", "MARKET", 0.3, 4, "WALK", 1)
conn.commit()


# =========================================================================
# 3. KUMASI (Ashanti Region) — Ayeduase Modern Hostel Block
# =========================================================================
print("[3/7] Ayeduase Modern Hostel Block (Kumasi / KNUST)...")
p3 = insert_property(
    code="HST-KMS-AMH-003", title="Ayeduase Modern Hostel Block",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Ayeduase Modern Hostel Block is a 3-storey stone-clad student residence 8 minutes walk from KNUST.",
    address="Ayeduase Road, Off KNUST Main Road", city="Kumasi", region="Ashanti",
    postal_code="AK-541", digital_address="AK-541-6789",
    lat=6.676300, lon=-1.574800, total_area=750.0, total_floors=3,
    nearest_inst="KNUST (Kwame Nkrumah University of Science and Technology)", distance=0.7, walking_time=8,
    nearby_landmarks="KNUST Commercial Area, Ayeduase Market", hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Emmanuel Boateng", owner_email="manager@ayeduasehostel.com", owner_phone="+233 27 644 5511",
    house_rules="Quiet hours 10 PM - 5:30 AM.", visitor_policy="Visitors 8 AM - 8 PM.",
    prohibited_items="No smoking or gas cylinders.", emergency_contacts="Security: +233 27 644 5511.",
    cancellation_policy="Full refund 14 days before semester.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Municipal + Overhead Tank Backup (24/7)", electricity_stab="High (Generator backup)",
    internet_avail="Fibre Wi-Fi — All 3 Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=9, smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, ns_=True, is_featured=True,
)
add_ams(p3, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK])
add_pi(p3, cp("images (2).jpeg", "HST-KMS-AMH-003_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Exterior View", True, 1)

add_rt_option(p3, "Double Room (2 in a Room)", "SEMESTER_BASED", "DOUBLE", 2, "D101",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              sem_price=2200.00, mon_price=550.00, dep=350.00, reg=100.00,
              img1=cp("images (5).jpeg", "HST-KMS-AMH-003_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (16).jpeg", "HST-KMS-AMH-003_rm_D_2.jpeg", MEDIA_R))

add_rt_option(p3, "Triple Room (3 in a Room)", "SEMESTER_BASED", "TRIPLE", 3, "T301",
              fan=True, wifi=True, desk=True, ward=False, pbath=False, sbath="1 per 3 Rooms",
              sem_price=1600.00, mon_price=400.00, dep=250.00, reg=80.00,
              img1=cp("images (1).jpeg", "HST-KMS-AMH-003_rm_T_1.jpeg", MEDIA_R),
              img2=cp("images (9).jpeg", "HST-KMS-AMH-003_rm_T_2.jpeg", MEDIA_R))

add_prox(p3, "KNUST Main Gate", "INSTITUTION", 0.7, 8, "WALK", 1)
conn.commit()


# =========================================================================
# 4. TAKORADI (Western Region) — Atlantic Ocean View Hostel
# =========================================================================
print("[4/7] Atlantic Ocean View Hostel (Takoradi / Western Region)...")
p4 = insert_property(
    code="HST-WST-TKH-004", title="Atlantic Ocean View Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Atlantic Ocean View Hostel is a scenic student residence situated in Takoradi, serving TTU students.",
    address="Beach Road, Near TTU Campus", city="Takoradi", region="Western",
    postal_code="WS-044", digital_address="WS-044-8890",
    lat=4.887200, lon=-1.758100, total_area=700.0, total_floors=3,
    nearest_inst="Takoradi Technical University (TTU)", distance=0.5, walking_time=6,
    nearby_landmarks="Takoradi Harbour, TTU Main Campus", hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Josephine Mensah-Kwofie", owner_email="info@atlantichostel.com", owner_phone="+233 24 311 0022",
    house_rules="Quiet hours 10 PM - 6 AM.", visitor_policy="Visitors 9 AM - 7 PM.",
    prohibited_items="No smoking or alcohol.", emergency_contacts="Security: +233 24 311 0022.",
    cancellation_policy="Full refund 14 days before semester.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole + Municipal Water (24/7)", electricity_stab="High (Generator Backup)",
    internet_avail="Fibre Wi-Fi — All Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=9, smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, wkr=True, ns_=True, is_featured=True,
)
add_ams(p4, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK])
add_pi(p4, cp("images (12).jpeg", "HST-WST-TKH-004_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Exterior View", True, 1)

add_rt_option(p4, "Executive Single Room (Ensuite)", "SEMESTER_BASED", "SINGLE", 1, "E101",
              ac=True, wifi=True, desk=True, ward=True, pbath=True,
              sem_price=3200.00, mon_price=800.00, dep=500.00, reg=150.00,
              img1=cp("images (15).jpeg", "HST-WST-TKH-004_rm_E_1.jpeg", MEDIA_R),
              img2=cp("images (14).jpeg", "HST-WST-TKH-004_rm_E_2.jpeg", MEDIA_R))

add_rt_option(p4, "Standard Double Room", "SEMESTER_BASED", "DOUBLE", 2, "D201",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              sem_price=2000.00, mon_price=500.00, dep=300.00, reg=100.00,
              img1=cp("images (5).jpeg", "HST-WST-TKH-004_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (3).jpeg", "HST-WST-TKH-004_rm_D_2.jpeg", MEDIA_R))

add_prox(p4, "TTU Main Gate", "INSTITUTION", 0.5, 6, "WALK", 1)
conn.commit()


# =========================================================================
# 5. CAPE COAST (Central Region) — Oguaa Premier Student Hostel
# =========================================================================
print("[5/7] Oguaa Premier Student Hostel (Cape Coast / Central Region)...")
p5 = insert_property(
    code="HST-CTR-CCH-005", title="Oguaa Premier Student Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Oguaa Premier Student Hostel is a peaceful accommodation facility located 5 minutes from UCC Science Gate.",
    address="Science Gate Road, UCC North Campus", city="Cape Coast", region="Central",
    postal_code="CC-012", digital_address="CC-012-4432",
    lat=5.105300, lon=-1.284700, total_area=650.0, total_floors=3,
    nearest_inst="University of Cape Coast (UCC)", distance=0.6, walking_time=7,
    nearby_landmarks="UCC Science Complex", hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Kwesi Eduful", owner_email="oguaahostel@gmail.com", owner_phone="+233 20 440 9988",
    house_rules="Quiet hours 10 PM - 6 AM.", visitor_policy="Visitors 8 AM - 8 PM.",
    prohibited_items="No smoking or alcohol.", emergency_contacts="Security: +233 20 440 9988.",
    cancellation_policy="Full refund 14 days before semester start.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole Water System (24/7)", electricity_stab="High (Generator Available)",
    internet_avail="Fibre Wi-Fi — All Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=9, smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, ns_=True, is_featured=True,
)
add_ams(p5, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK])
add_pi(p5, cp("images (7).jpeg", "HST-CTR-CCH-005_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Main View", True, 1)

add_rt_option(p5, "Single Room (1 in a Room)", "SEMESTER_BASED", "SINGLE", 1, "S101",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 4 Rooms",
              sem_price=2600.00, mon_price=650.00, dep=400.00, reg=120.00,
              img1=cp("images (19).jpeg", "HST-CTR-CCH-005_rm_S_1.jpeg", MEDIA_R),
              img2=cp("images.jpeg",      "HST-CTR-CCH-005_rm_S_2.jpeg", MEDIA_R))

add_rt_option(p5, "Double Room (2 in a Room)", "SEMESTER_BASED", "DOUBLE", 2, "D201",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              sem_price=1750.00, mon_price=440.00, dep=250.00, reg=80.00,
              img1=cp("images (17).jpeg", "HST-CTR-CCH-005_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (15).jpeg", "HST-CTR-CCH-005_rm_D_2.jpeg", MEDIA_R))

add_prox(p5, "UCC Science Gate", "INSTITUTION", 0.6, 7, "WALK", 1)
conn.commit()


# =========================================================================
# 6. TAMALE (Northern Region) — Savannah Oasis Student Hostel
# =========================================================================
print("[6/7] Savannah Oasis Student Hostel (Tamale / Northern Region)...")
p6 = insert_property(
    code="HST-NTH-UDH-006", title="Savannah Oasis Student Hostel",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Savannah Oasis Student Hostel is a modern student residence serving UDS Tamale Campus students.",
    address="Hospital Road, Near UDS Tamale Campus", city="Tamale", region="Northern",
    postal_code="NT-102", digital_address="NT-102-7711",
    lat=9.407500, lon=-0.853300, total_area=800.0, total_floors=3,
    nearest_inst="University for Development Studies (UDS Tamale)", distance=0.8, walking_time=10,
    nearby_landmarks="Tamale Teaching Hospital", hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Alhassan Yakubu", owner_email="savannahhostel@yahoo.com", owner_phone="+233 24 998 1122",
    house_rules="Quiet hours 10 PM - 5:30 AM.", visitor_policy="Visitors 8 AM - 8 PM.",
    prohibited_items="No smoking or alcohol.", emergency_contacts="Security: +233 24 998 1122.",
    cancellation_policy="Full refund 14 days before semester start.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole + Large Overhead Tanks (24/7)", electricity_stab="High (Generator Available)",
    internet_avail="Fibre Wi-Fi — All Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=9, smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, ns_=True, is_featured=True,
)
add_ams(p6, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK])
add_pi(p6, cp("images (10).jpeg", "HST-NTH-UDH-006_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Main View", True, 1)

add_rt_option(p6, "Double Room (2 in a Room)", "SEMESTER_BASED", "DOUBLE", 2, "D101",
              fan=True, ac=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              sem_price=1900.00, mon_price=475.00, dep=300.00, reg=100.00,
              img1=cp("images (5).jpeg", "HST-NTH-UDH-006_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (3).jpeg", "HST-NTH-UDH-006_rm_D_2.jpeg", MEDIA_R))

add_rt_option(p6, "Triple Room (3 in a Room)", "SEMESTER_BASED", "TRIPLE", 3, "T301",
              fan=True, wifi=True, desk=True, ward=False, pbath=False, sbath="1 per 3 Rooms",
              sem_price=1400.00, mon_price=350.00, dep=200.00, reg=80.00,
              img1=cp("images (1).jpeg", "HST-NTH-UDH-006_rm_T_1.jpeg", MEDIA_R),
              img2=cp("images (4).jpeg", "HST-NTH-UDH-006_rm_T_2.jpeg", MEDIA_R))

add_prox(p6, "UDS Tamale Campus Gate", "INSTITUTION", 0.8, 10, "WALK", 1)
conn.commit()


# =========================================================================
# 7. HO (Volta Region) — Volta Heights Student Residence
# =========================================================================
print("[7/7] Volta Heights Student Residence (Ho / Volta Region)...")
p7 = insert_property(
    code="HST-VLT-HOH-007", title="Volta Heights Student Residence",
    prop_type="HOSTEL", cat="STUDENT_HOUSING",
    desc="Volta Heights Student Residence is a premium hostel serving UHAS students in Ho.",
    address="Sokode Road, Near UHAS Main Campus", city="Ho", region="Volta",
    postal_code="VH-201", digital_address="VH-201-9944",
    lat=6.600800, lon=0.471200, total_area=680.0, total_floors=3,
    nearest_inst="University of Health and Allied Sciences (UHAS)", distance=0.7, walking_time=9,
    nearby_landmarks="UHAS Permanent Campus", hostel_type="MIXED", ownership_type="PRIVATE",
    owner_name="Sefakor Agbedanu", owner_email="voltaheights@gmail.com", owner_phone="+233 20 771 3344",
    house_rules="Quiet hours 11 PM - 6 AM.", visitor_policy="Visitors 9 AM - 8 PM.",
    prohibited_items="No smoking or gas cylinders.", emergency_contacts="Security: +233 20 771 3344.",
    cancellation_policy="Full refund 14 days before semester start.",
    cctv=True, security_personnel=True, gated_community=True,
    water_avail="Borehole Water System (24/7)", electricity_stab="High (Generator Available)",
    internet_avail="Fibre Wi-Fi — All Floors", utility_billing="INCLUDED_IN_RENT",
    fire_safety=True, safety_score=9, smoking=False, pets=False, guests=True, max_guests=2,
    stu=True, wkr=True, ns_=True, is_featured=True,
)
add_ams(p7, [W,SE,WA,AC,ST,GN,CC,FE,KI,PK,LA])
add_pi(p7, cp("images (18).jpeg", "HST-VLT-HOH-007_ext_main.jpeg", MEDIA_P), "EXTERIOR", "Front View", True, 1)

add_rt_option(p7, "Executive Single Room (Ensuite)", "SEMESTER_BASED", "SINGLE", 1, "E101",
              ac=True, wifi=True, desk=True, ward=True, pbath=True,
              sem_price=3400.00, mon_price=850.00, dep=500.00, reg=150.00,
              img1=cp("images (15).jpeg", "HST-VLT-HOH-007_rm_E_1.jpeg", MEDIA_R),
              img2=cp("images (14).jpeg", "HST-VLT-HOH-007_rm_E_2.jpeg", MEDIA_R))

add_rt_option(p7, "Double Room (2 in a Room)", "SEMESTER_BASED", "DOUBLE", 2, "D201",
              fan=True, wifi=True, desk=True, ward=True, pbath=False, sbath="1 per 3 Rooms",
              sem_price=2100.00, mon_price=525.00, dep=300.00, reg=100.00,
              img1=cp("images (4).jpeg", "HST-VLT-HOH-007_rm_D_1.jpeg", MEDIA_R),
              img2=cp("images (17).jpeg", "HST-VLT-HOH-007_rm_D_2.jpeg", MEDIA_R))

add_prox(p7, "UHAS Main Campus", "INSTITUTION", 0.7, 9, "WALK", 1)
conn.commit()


# ─── VERIFICATION AUDIT ────────────────────────────────────────────────
print("\n" + "="*70)
print("VERIFICATION AUDIT")
print("="*70)

cur.execute("""
    SELECT p.property_code, p.title, rt.room_type_name, rt.occupancy_type,
           rt.beds_per_room, rt.total_capacity, rt.available_slots
    FROM room_types rt
    JOIN properties p ON p.id = rt.accommodation_property_id
    ORDER BY p.id, rt.id;
""")

for r in cur.fetchall():
    print(f"[{r[0]}] {r[1]} -> {r[2]}: {r[3]} ({r[4]} beds, {r[5]} capacity, {r[6]} slot(s) left)")

conn.close()
print("\n✅ PERFECT SLOT PRINCIPLE ENFORCED ACROSS ALL 7 REGIONAL HOSTELS!")
