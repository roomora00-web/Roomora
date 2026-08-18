"""
Roomora Complete Master Documentation Generator (v4.0 Final Master Edition)
Generates the comprehensive technical, architectural, theoretical, and operational documentation
for the Roomora Student & Young-Professional Accommodation Platform.
"""

import os
import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_callout_box(doc, title, text, bg_hex="F8F8FA", border_hex="111111"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_hex}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r_title = p.add_run(f"📌 {title}\n")
    r_title.bold = True
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(10.5)
    r_title.font.color.rgb = RGBColor(17, 17, 17)
    
    r_text = p.add_run(text)
    r_text.font.name = 'Calibri'
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = RGBColor(60, 60, 60)
    
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(4)

def format_table(table, header_bg="111111", alt_bg="F9F9FB"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
            
            tcPr = cell._element.get_or_add_tcPr()
            tcBorders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:top w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>'
                f'<w:left w:val="none"/>'
                f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>'
                f'<w:right w:val="none"/>'
                f'</w:tcBorders>'
            )
            tcPr.append(tcBorders)
            
            if i == 0:
                set_cell_background(cell, header_bg)
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(4)
                    p.paragraph_format.space_after = Pt(4)
                    for r in p.runs:
                        r.bold = True
                        r.font.name = 'Calibri'
                        r.font.color.rgb = RGBColor(255, 255, 255)
                        r.font.size = Pt(9.5)
            else:
                if i % 2 == 1:
                    set_cell_background(cell, "FFFFFF")
                else:
                    set_cell_background(cell, alt_bg)
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(3)
                    p.paragraph_format.space_after = Pt(3)
                    for r in p.runs:
                        r.font.name = 'Calibri'
                        r.font.size = Pt(9)
                        r.font.color.rgb = RGBColor(40, 40, 40)

def add_heading_styled(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    if level == 1:
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(16)
            r.bold = True
            r.font.color.rgb = RGBColor(17, 17, 17)
    elif level == 2:
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(13)
            r.bold = True
            r.font.color.rgb = RGBColor(30, 41, 59)
    elif level == 3:
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
            r.bold = True
            r.font.color.rgb = RGBColor(51, 65, 85)
    return h

def generate_master_document():
    doc = Document()
    
    # Page setup (Standard A4 / Letter, 1-inch margins)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(40, 40, 40)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(5)

    # =========================================================================
    # COVER / TITLE PAGE
    # =========================================================================
    p_top_spacer = doc.add_paragraph()
    p_top_spacer.paragraph_format.space_before = Pt(72)

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = title_p.add_run("ROOMORA")
    r_title.bold = True
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(36)
    r_title.font.color.rgb = RGBColor(17, 17, 17)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(18)
    r_sub = sub_p.add_run("The Complete Technical, Architectural & Theoretical Master Specification")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)
    r_sub.bold = True

    badge_p = doc.add_paragraph()
    badge_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    badge_p.paragraph_format.space_after = Pt(36)
    r_badge = badge_p.add_run("Official Master Architecture Document • Version 4.0 (Comprehensive Edition)")
    r_badge.font.name = 'Calibri'
    r_badge.font.size = Pt(10)
    r_badge.bold = True
    r_badge.font.color.rgb = RGBColor(5, 150, 105)

    desc_p = doc.add_paragraph()
    desc_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_desc = desc_p.add_run(
        "An absolutely exhaustive, theoretical and technical blueprint of the Roomora Student Accommodation Platform.\n"
        "Meticulously detailing all state-machine logic, algorithmic roommate compatibility mechanics, concurrency control,\n"
        "multi-tiered property architecture, escrow payment pipelines, lifecycle state transitions, and in-stay portal operating systems."
    )
    r_desc.font.name = 'Calibri'
    r_desc.font.size = Pt(10.5)
    r_desc.font.color.rgb = RGBColor(71, 85, 105)

    p_meta_spacer = doc.add_paragraph()
    p_meta_spacer.paragraph_format.space_before = Pt(120)

    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_rows = [
        ("Platform Name", "Roomora Accommodation Platform (StayMatch Engine)"),
        ("Architecture Framework", "Django 5.x / Python 3.14 / PostgreSQL / Capacitor PWA"),
        ("Production URL", "https://roomora-production-cab4.up.railway.app"),
        ("Target Ecosystem", "Higher-Education Student Housing & Young-Professional Sanctuaries")
    ]
    for idx, (label, val) in enumerate(meta_rows):
        row = meta_table.rows[idx]
        cell_l, cell_r = row.cells[0], row.cells[1]
        set_cell_background(cell_l, "F8F8FA")
        set_cell_background(cell_r, "FFFFFF")
        set_cell_margins(cell_l, top=60, bottom=60, left=100, right=100)
        set_cell_margins(cell_r, top=60, bottom=60, left=100, right=100)
        
        pl = cell_l.paragraphs[0]
        pl.paragraph_format.space_before = Pt(2)
        pl.paragraph_format.space_after = Pt(2)
        rl = pl.add_run(label)
        rl.bold = True
        rl.font.size = Pt(9.5)
        
        pr = cell_r.paragraphs[0]
        pr.paragraph_format.space_before = Pt(2)
        pr.paragraph_format.space_after = Pt(2)
        rr = pr.add_run(val)
        rr.font.size = Pt(9.5)

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 1: EXECUTIVE OVERVIEW & SYSTEM PHILOSOPHY
    # =========================================================================
    add_heading_styled(doc, "1. Executive Overview & System Philosophy", 1)
    
    doc.add_paragraph(
        "Roomora is not a conventional classifieds listing board or passive directory. It is an end-to-end, state-driven "
        "Accommodation Operating System engineered specifically to resolve the severe systemic failures prevalent in higher-education "
        "and young-professional housing markets. In emerging university ecosystems, student accommodation is traditionally characterized by "
        "predatory middlemen, fraudulent agent fees, bait-and-switch photography, unvetted and incompatible roommate pairings, opaque billing structures, "
        "and chaotic, unmonitored move-out procedures."
    )

    doc.add_paragraph(
        "Roomora fundamentally transforms this environment by orchestrating the entire lifecycle of a tenancy—from initial discovery, "
        "atomic inventory soft-locking, and multi-factor lifestyle matching, through transparent escrow-backed payment settlement, "
        "continuous stay telemetry, and digitally audited move-out handovers. The platform replaces informal verbal commitments with an uncompromising, "
        "mathematically sound 17-state finite-state machine."
    )

    add_callout_box(
        doc,
        "Core Architectural Tenet: The Dual-Class Accommodation Model",
        "Roomora enforces a strict conceptual divergence between communal student living (Hostels) and private residential spaces (Apartments & Studios). "
        "Hostels operate on slot-based inventory, gender segregation rules, academic semester calendars (17 weeks/semester), split-stay vacation reserves, "
        "and weighted compatibility matching. Conversely, Apartments operate on whole-unit leasing, monthly calendar cycles, and direct self-service lease extension tools without roommate matching."
    )

    # =========================================================================
    # CHAPTER 2: USER ROLES, IDENTITY & SECURITY ECOSYSTEM
    # =========================================================================
    add_heading_styled(doc, "2. User Roles, Identity & Security Ecosystem", 1)
    doc.add_paragraph(
        "The platform is governed by a secure, multi-tiered user architecture designed to uphold community trust, physical safety, and financial integrity."
    )

    add_heading_styled(doc, "2.1 Role Definitions & Separation of Concerns", 2)
    
    role_table = doc.add_table(rows=4, cols=3)
    role_headers = ["Role Tier", "Primary Responsibilities", "Governance & Permissions"]
    for col_idx, text in enumerate(role_headers):
        role_table.rows[0].cells[col_idx].paragraphs[0].text = text

    role_data = [
        (
            "Students / Tenants",
            "Register, complete academic and ID verification, browse inventory, save bookmarks, complete 26-metric lifestyle questionnaires, execute secure payments, manage in-stay residency via the Room Portal, submit maintenance tickets, declare personal appliances, and submit verified post-stay reviews.",
            "Consumer permissions. Restricted to their own bookings, profiles, and authenticated room portal telemetry."
        ),
        (
            "Platform Administrators",
            "The supreme operational authority. Exclusively onboard, inspect, and publish property listings; verify landlord credentials; configure pricing models and room tiers; arbitrate tenant disputes; review compatibility overrides; track overstays; and authorize landlord escrow disbursements.",
            "Full superuser and operational staff permissions. Direct access to platform master controls, escrow ledgers, and inventory audits."
        ),
        (
            "Landlords / Property Owners",
            "Passive stakeholders. Landlords DO NOT create or modify public listings directly (preventing unverified or fraudulent claims). They access a specialized dashboard to view real-time occupancy, receive tenant assignment notifications, review maintenance tickets, and accept disbursed rental proceeds.",
            "Restricted partner permissions. Read-only access to assigned tenant names, emergency contacts, and escrow payout histories."
        )
    ]
    for row_idx, data in enumerate(role_data, start=1):
        for col_idx, text in enumerate(data):
            role_table.rows[row_idx].cells[col_idx].paragraphs[0].text = text
    format_table(role_table)

    add_heading_styled(doc, "2.2 Identity & Academic Verification Pipeline", 2)
    doc.add_paragraph(
        "To ensure property rules (such as 'Student Only' or gender-segregated dormitories) are strictly maintained, all applicants undergo identity auditing. "
        "Tenants upload government IDs (Passport, National ID, Voter Card) or valid Student Identification Cards, declare their academic institution "
        "(e.g., University of Ghana, KNUST, UPSA), specify their field of study, and register their academic level (100–400 or Post-Graduate). "
        "Admins verify these documents before granting full community clearance."
    )

    add_heading_styled(doc, "2.3 Security Protocols & Brute-Force Rate Limiting", 2)
    doc.add_paragraph(
        "Security is implemented at every layer of the network and database stack:"
    )
    sec_points = [
        "256-Bit Cryptographic Encryption: All communication across web and mobile endpoints is enforced over TLS/HTTPS.",
        "Email OTP Verification: Sign-up is gated by a 6-digit Time-Based One-Time Password (OTP) expiring in 15 minutes, with a strict maximum of 3 verification attempts.",
        "Brute-Force Rate Limiter: The LoginAttempt tracker monitors failed authentication events per IP and email. Exceeding 5 consecutive failed attempts results in an automatic 30-minute account lockout (`locked_until`).",
        "CSRF & Secure Session Cookies: Cross-Site Request Forgery tokens are cryptographically evaluated on every modifying state transition."
    ]
    for p in sec_points:
        doc.add_paragraph(p, style='List Bullet')

    # =========================================================================
    # CHAPTER 3: PROPERTY DISCOVERY, GEOSPATIAL INTELLIGENCE & LISTING BROCHURES
    # =========================================================================
    add_heading_styled(doc, "3. Property Discovery, Geospatial Intelligence & Listing Profiles", 1)
    
    doc.add_paragraph(
        "Discovery on Roomora is powered by a multi-faceted search and filtering engine designed to help students pinpoint their optimal living space within seconds."
    )

    add_heading_styled(doc, "3.1 Multi-Parameter Search & Campus Proximity Radius", 2)
    doc.add_paragraph(
        "Tenants can dynamically query inventory across multiple simultaneous dimensions:"
    )
    search_params = [
        "Budget Brackets: Filter by exact minimum and maximum pricing boundaries (in GH₵).",
        "Property Classification: Hostels vs. Entire Apartments vs. Studio Sanctuaries vs. Shared Flats.",
        "Geospatial Coordinates & Campus Proximity: Distance-to-campus calculations based on latitude/longitude coordinates, identifying properties within walking or transit distance of major lecture blocks.",
        "Gender-Segregation Filters: Co-ed, Boys Only, and Girls Only configurations.",
        "Granular Amenity Checklist: Generator backup (Dumsor protection), Borehole / Water reservoir, High-Speed WiFi, Air Conditioning, Study Desks, Private En-Suite Bathrooms, and Balconies."
    ]
    for s in search_params:
        doc.add_paragraph(s, style='List Bullet')

    add_heading_styled(doc, "3.2 Rich Listing Brochures & Verification Badges", 2)
    doc.add_paragraph(
        "Every listing serves as an interactive, highly transparent digital brochure containing:"
    )
    brochure_elements = [
        "Verified Photo Galleries: High-resolution internal room and facility photography physically inspected and approved by Roomora Admins.",
        "Physical House Rules & Regulations: Explicit disclosure of curfews, overnight guest policies, appliance restrictions, and noise rules prior to booking.",
        "Roomora Verification Seal: Visual confirmation that property ownership, safety compliance, and physical facilities have been verified.",
        "Aggregated Tenant Reviews: Real feedback, star ratings, and sub-score metrics from previous tenants who completed verified residencies."
    ]
    for b in brochure_elements:
        doc.add_paragraph(b, style='List Bullet')

    # =========================================================================
    # CHAPTER 4: INVENTORY MANAGEMENT & ATOMIC SOFT-LOCKING MECHANISM
    # =========================================================================
    add_heading_styled(doc, "4. Inventory Management & Atomic Soft-Locking Mechanism", 1)
    
    doc.add_paragraph(
        "In student accommodation, high-demand booking windows (such as university admissions periods) generate massive concurrent traffic surges. "
        "Traditional platforms frequently suffer from race conditions leading to double-booking collisions, where two students pay for the same bed simultaneously."
    )

    add_heading_styled(doc, "4.1 The Atomic Soft-Locking Theorem", 2)
    doc.add_paragraph(
        "Roomora completely eliminates inventory collisions through the `SoftLockService`. When a tenant selects an available room or unit and clicks 'Book Now', "
        "the database executes an atomic transaction utilizing PostgreSQL row-level locks (`SELECT FOR UPDATE`)."
    )

    add_callout_box(
        doc,
        "How Atomic Soft-Locking Works",
        "1. The database row for the chosen Room or UnitType is locked instantaneously.\n"
        "2. The system validates that `available_slots > 0`.\n"
        "3. A `Booking` record is instantiated in `INITIATED` status, assigning `soft_lock_expires_at = now() + 2 hours`.\n"
        "4. The room's pending slots increment and public available slots decrement.\n"
        "5. The slot becomes completely invisible and unavailable to all other browsing users.\n"
        "6. If the user fails to complete checkout within the window, the soft lock expires automatically, and the slot is released back to public inventory."
    )

    add_heading_styled(doc, "4.2 Continuous Single 2-Hour Countdown Lifecycle", 2)
    doc.add_paragraph(
        "Roomora enforces a seamless, continuous 2-hour countdown across the entire initiation and checkout pipeline. "
        "The timer starts upon room reservation and persists across duration selection, lifestyle profiling, and booking confirmation. "
        "When the user proceeds to the final payment gateway, the `PaymentRecord.payment_window_closes_at` inherits the exact remaining time from the soft lock, "
        "preventing artificial timer resets and ensuring genuine inventory fairness."
    )

    # =========================================================================
    # CHAPTER 5: FLEXIBLE TENANCY STRUCTURES, BILLING MODELS & MATHEMATICS
    # =========================================================================
    add_heading_styled(doc, "5. Flexible Tenancy Structures, Billing Models & Mathematics", 1)
    
    doc.add_paragraph(
        "Roomora supports four distinct structural tenancy models tailored to academic calendars and residential leasing requirements:"
    )

    tenancy_table = doc.add_table(rows=5, cols=4)
    tenancy_headers = ["Tenancy Model", "Standard Duration", "Billing Formula", "Target Use Case"]
    for col_idx, text in enumerate(tenancy_headers):
        tenancy_table.rows[0].cells[col_idx].paragraphs[0].text = text

    tenancy_data = [
        (
            "Option A: Full Academic Year (Continuous)",
            "34 Weeks (238 Consecutive Days)",
            "Total = Semester Price x 2 (or Annual Academic Rate)",
            "Students residing continuously throughout the full academic session without leaving for holidays."
        ),
        (
            "Option B: Split-Stay (Vacation Reserve)",
            "Semester 1 (17 Wks) + Vacation Pause + Semester 2 (17 Wks)",
            "Total = Semester 1 Rate + Semester 2 Rate (Zero rent during vacation gap)",
            "Students who vacate during long holidays. Room is locked in `VACATION_RESERVE`, belongings secured, zero rent charged, slot guaranteed for Semester 2."
        ),
        (
            "Option C: Semester-Based Stay",
            "17 Weeks (119 Days Canonical)",
            "Total = Single Semester Flat Rate",
            "Single-term students, exchange students, or final-year students completing one semester."
        ),
        (
            "Option D: Monthly Flex / Annual Lease",
            "1 to 24 Months (Standardized 30-Day Billing)",
            "Total = Monthly Rate x Number of Months Selected",
            "Young professionals, post-graduate researchers, and private apartment tenants."
        )
    ]
    for row_idx, data in enumerate(tenancy_data, start=1):
        for col_idx, text in enumerate(data):
            tenancy_table.rows[row_idx].cells[col_idx].paragraphs[0].text = text
    format_table(tenancy_table)

    add_heading_styled(doc, "5.1 Split-Stay Vacation Gap Mathematics", 2)
    doc.add_paragraph(
        "In Option B (Split-Stay), the `DurationService` calculates distinct stay periods:"
    )
    split_math = [
        "Semester 1 Duration: Move-In Date to Move-In Date + 119 Days (17 Weeks).",
        "Vacation Reserve Window: Semester 1 Move-Out Date to Projected Semester 2 Return Date.",
        "Semester 2 Duration: Semester 2 Return Date to Return Date + 119 Days (17 Weeks).",
        "Financial Billing: The student is billed exclusively for the 34 weeks of actual occupancy. Zero rent is accrued during the holiday gap."
    ]
    for sm in split_math:
        doc.add_paragraph(sm, style='List Bullet')

    # =========================================================================
    # CHAPTER 6: THE 8-DIMENSION ALGORITHMIC ROOMMATE COMPATIBILITY ENGINE
    # =========================================================================
    add_heading_styled(doc, "6. The 8-Dimension AlgorithMIC Roommate Compatibility Engine", 1)
    
    doc.add_paragraph(
        "In communal student accommodation, toxic or incompatible roommate pairings are the single leading cause of lease terminations, "
        "mental distress, and academic disruption. Roomora replaces arbitrary roommate allocation with a proprietary, weighted 8-dimension matching algorithm."
    )

    add_heading_styled(doc, "6.1 The 8 Weighted Profiling Dimensions", 2)
    
    dim_table = doc.add_table(rows=9, cols=3)
    dim_headers = ["Dimension", "Weight", "Evaluated Questionnaire Attributes"]
    for col_idx, text in enumerate(dim_headers):
        dim_table.rows[0].cells[col_idx].paragraphs[0].text = text

    dim_data = [
        ("1. Sleep & Circadian Schedule", "18%", "Sleep time (Very Early to Very Late), Wake-up time, Alarm reliance, Nighttime light and device activity."),
        ("2. Cleanliness & Domestic Habits", "16%", "Cleanliness scale (1–5), chore division preferences, cleaning frequency (Daily, Weekly, Monthly), room tidiness expectations."),
        ("3. Noise Tolerance & Social Rhythms", "15%", "Preferred study acoustics (Absolute silence vs. Ambient music), volume tolerance, introversion vs. extraversion."),
        ("4. Guest & Visitor Protocols", "14%", "Daytime guest frequency, overnight guest policies, advance notice requirements for bringing visitors."),
        ("5. Study Dynamics & Quiet Hours", "13%", "Study location (In-room desk vs. Library), study hours, adherence to mandatory quiet-hour windows."),
        ("6. Kitchen & Food Sharing Ethics", "10%", "Cooking frequency, kitchen sharing comfort, food labeling vs. open-pantry sharing boundaries."),
        ("7. Substance, Alcohol & Smoking", "8%", "Smoking tolerance (Strict Non-Smoking vs. Outdoor Only), alcohol consumption tolerance, party environment comfort."),
        ("8. Thermal Comfort & Room Climate", "6%", "Air conditioning vs. Fan preference, sleeping temperature preferences, window ventilation habits.")
    ]
    for row_idx, data in enumerate(dim_data, start=1):
        for col_idx, text in enumerate(data):
            dim_table.rows[row_idx].cells[col_idx].paragraphs[0].text = text
    format_table(dim_table)

    add_heading_styled(doc, "6.2 Compatibility Scoring Formula & Decision Triaging", 2)
    doc.add_paragraph(
        "The `CompatibilityService` computes a normalized Compatibility Score (S, 0–100%) between applicant profile A and existing room occupant B:\n"
        "S = 100 - SUM( w_i * |A_i - B_i| / max_diff_i ) * 100\n"
        "Where w_i represents the dimension weight and |A_i - B_i| measures the Euclidean/Manhattan distance across normalized categorical answers."
    )

    doc.add_paragraph(
        "The resulting score triggers one of three automated decision pathways:"
    )
    
    decision_points = [
        ("Tier 1: Auto-Assignment (Score >= 85%)", "High compatibility match. The applicant is automatically paired into the room, their profile is temporarily locked, and the booking transitions directly to `PAYMENT_REQUIRED`."),
        ("Tier 2: Manual Consent Flow (50% <= Score < 85%)", "Moderate compatibility match. The applicant is presented with an anonymized Roommate Profile Card showing alignment metrics and common habits. The student has a 2-hour/24-hour decision window to Accept or Reject."),
        ("Tier 3: Fallback & Admin Review (Score < 50%)", "Low compatibility. The system evaluates alternative rooms in the property. If no compatible room exists, the booking is flagged for Admin manual mediation or routing to single occupancy.")
    ]
    for title, desc in decision_points:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(title + ": ").bold = True
        p.add_run(desc)

    # =========================================================================
    # CHAPTER 7: THE 17-STATE BOOKING LIFECYCLE STATE MACHINE
    # =========================================================================
    add_heading_styled(doc, "7. The 17-State Booking Lifecycle State Machine", 1)
    
    doc.add_paragraph(
        "At the architectural core of Roomora is an immutable, mathematically rigorous Finite-State Machine governing every booking record. "
        "Every tenancy transitions strictly through 17 explicit states, recorded in `BookingStatusTimeline` and `BookingHistory`."
    )

    state_table = doc.add_table(rows=18, cols=3)
    state_headers = ["State Identifier", "System Description", "Trigger / Transition Conditions"]
    for col_idx, text in enumerate(state_headers):
        state_table.rows[0].cells[col_idx].paragraphs[0].text = text

    state_data = [
        ("1. INITIATED", "Soft-lock active. Bed/slot reserved for 2 hours.", "User clicks 'Book Now' and acknowledges house rules."),
        ("2. LIFESTYLE_PENDING", "Waiting for questionnaire submission in shared room.", "User advances to lifestyle preference screens."),
        ("3. AWAITING_COMPATIBILITY", "Matching algorithm actively calculating compatibility.", "Lifestyle questionnaire submitted for shared space."),
        ("4. AUTO_ASSIGNED", "Matched at >= 85% compatibility.", "CompatibilityService detects optimal roommate alignment."),
        ("5. CONSENT_PENDING", "Awaiting tenant decision on 50–84% match.", "CompatibilityService generates moderate alignment score."),
        ("6. CONSENT_ACCEPTED", "Tenant agreed to proposed roommate match.", "Tenant clicks 'Accept Match' on consent screen."),
        ("7. ADMIN_PENDING", "Awaiting platform administrator confirmation.", "Manual assignment or special occupancy review."),
        ("8. PAYMENT_REQUIRED", "Checkout session initialized. Awaiting payment.", "Single unit, first occupant, or accepted match routing."),
        ("9. PAYMENT_PROCESSING", "Payment gateway verifying transaction.", "MoMo USSD push sent or Card 3D Secure submitted."),
        ("10. PAYMENT_COMPLETE", "Funds received and held securely in Escrow.", "Paystack webhook confirms successful settlement."),
        ("11. CONFIRMED", "Room officially secured. Awaiting move-in date.", "Payment verified; digital receipt and key code generated."),
        ("12. ACTIVE", "Tenant physically residing in property.", "Move-in date arrives; tenant checks in via Room Portal."),
        ("13. VACATION_RESERVE", "Split-stay holiday pause. Room locked, zero rent.", "Semester 1 ends in Option B; student vacates for break."),
        ("14. GRACE_PERIOD", "5-day penalty-free move-out window.", "Lease/semester ends; student given 5 days to pack."),
        ("15. OVERSTAY", "Tenant failed to vacate post-grace period.", "Grace period expires without departure confirmation; daily penalty accrues."),
        ("16. TEMPORARILY_CANCELLED", "Soft-lock expired or payment failed.", "2-hour window collapses; user given 24h lifeline to reinstate."),
        ("17. PERMANENTLY_CANCELLED", "Finalized irreversible cancellation.", "Reinstatement window expires or Admin authorizes full refund.")
    ]
    for row_idx, data in enumerate(state_data, start=1):
        for col_idx, text in enumerate(data):
            state_table.rows[row_idx].cells[col_idx].paragraphs[0].text = text
    format_table(state_table)

    # =========================================================================
    # CHAPTER 8: FINANCIAL ARCHITECTURE, PAYMENT GATEWAYS & ESCROW SECURITY
    # =========================================================================
    add_heading_styled(doc, "8. Financial Architecture, Payment Gateways & Escrow Security", 1)
    
    doc.add_paragraph(
        "Roomora operates an institutional-grade financial infrastructure designed to deliver 100% transparent billing and absolute anti-fraud protection."
    )

    add_heading_styled(doc, "8.1 Triple-Tier Cost Breakdown & Transparent Billing", 2)
    doc.add_paragraph(
        "Every booking presents an itemized billing schedule before payment authorization:"
    )
    cost_items = [
        ("Base Accommodation Rent", "The net rental charge allocated directly to the property owner/landlord."),
        ("Platform Service Fee (e.g. 2%–10%)", "Explicitly separated fee funding physical property inspections, verification infrastructure, 24/7 emergency support, and escrow management."),
        ("Refundable Security Deposit", "Held in secure escrow to cover potential damages, fully refundable upon verified check-out.")
    ]
    for label, desc in cost_items:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(label + ": ").bold = True
        p.add_run(desc)

    add_heading_styled(doc, "8.2 Multi-Channel Gateway Integration", 2)
    doc.add_paragraph(
        "Transactions are processed through Paystack utilizing 256-bit SSL encryption, supporting:"
    )
    gateways = [
        "Ghana Mobile Money: Instant USSD push to MTN Mobile Money, Telecel / Vodafone Cash, and AirtelTigo Money.",
        "Credit & Debit Cards: Visa, Mastercard, and Verve card processing with 3D-Secure 2.0 fraud protection.",
        "Bank Wire Transfers: Direct bank wire verification with slip uploads and admin reconciliation."
    ]
    for g in gateways:
        doc.add_paragraph(g, style='List Bullet')

    add_heading_styled(doc, "8.3 The Anti-Fraud Escrow Safeguard Protocol", 2)
    doc.add_paragraph(
        "To protect students against accommodation fraud and misrepresentation, tenant payments DO NOT go directly to Landlords upon checkout. "
        "Funds are locked in a Safeguarded Escrow Subaccount. Funds are disbursed to the Landlord ONLY after the student physically arrives, "
        "completes digital move-in key verification, and confirms that the accommodation matches listing specifications. "
        "In the event of physical misrepresentation or structural failure, Admins arbitrate full escrow refunds."
    )

    # =========================================================================
    # CHAPTER 9: THE ROOM PORTAL & IN-STAY OPERATING SYSTEM
    # =========================================================================
    add_heading_styled(doc, "9. The Room Portal & In-Stay Operating System", 1)
    
    doc.add_paragraph(
        "Once a booking is CONFIRMED and ACTIVE, the user experience transitions into the Room Portal—a personalized digital operating hub "
        "for managing their ongoing residency."
    )

    portal_features = [
        ("Real-Time Stay Telemetry", "Visual progress meters tracking 'Days Elapsed vs Days Remaining' in the tenancy."),
        ("Digital Move-In Protocol", "Key collection countdown timers, emergency contact details, and physical room condition sign-off checklists."),
        ("Maintenance Ticketing Subsystem", "Tenants log maintenance requests across categories (Plumbing, Electrical, Furniture, WiFi, Structural) with severity tiers (Low, Medium, Urgent). Landlords and Admins track resolution milestones."),
        ("Personal Appliance Declaration", "Tenants declare high-draw electrical items (Fridges, Microwaves, Electric Cookers) for load auditing and electrical safety compliance."),
        ("Direct Landlord Channel", "Secure disclosure of verified landlord phone numbers and WhatsApp channels for active residents."),
        ("Self-Service Lease Extensions", "Apartment tenants can extend their lease dates directly through the portal, dynamically recalculating pro-rated rent."),
        ("Vacation Date Re-Scheduling", "Hostel split-stay tenants can update their Semester 2 return dates to accommodate university calendar shifts.")
    ]
    for title, desc in portal_features:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(title + ": ").bold = True
        p.add_run(desc)

    # =========================================================================
    # CHAPTER 10: DEPARTURE LOGISTICS, GRACE PERIODS & OVERSTAY MECHANICS
    # =========================================================================
    add_heading_styled(doc, "10. Departure Logistics, Grace Periods & Overstay Mechanics", 1)
    
    doc.add_paragraph(
        "Roomora eliminates chaotic check-outs through automated, mathematically enforced exit protocols."
    )

    add_heading_styled(doc, "10.1 The 5-Day Penalty-Free Grace Period", 2)
    doc.add_paragraph(
        "When the scheduled Move-Out Date arrives, the booking transitions to `GRACE_PERIOD`. The student is granted a 5-day penalty-free window "
        "to finalize packing, complete room cleaning, and execute a digital 'Confirm Departure' action on their portal (surrendering keys digitally)."
    )

    add_heading_styled(doc, "10.2 Automated Overstay Penalty Accrual", 2)
    doc.add_paragraph(
        "If a tenant fails to confirm departure by the conclusion of the Grace Period, the state machine shifts to `OVERSTAY`. "
        "The system initiates automated daily financial penalty accrual:\n"
        "Daily Overstay Penalty = (Standard Daily Rate) x 1.5\n"
        "Penalties are automatically debited against the tenant's ledger and security deposit. Landlords and Admins receive high-priority alerts, "
        "and the tenant's platform rebooking eligibility is suspended until full reconciliation."
    )

    # =========================================================================
    # CHAPTER 11: REPUTATION, VERIFIED REVIEWS & QUALITY ASSURANCE
    # =========================================================================
    add_heading_styled(doc, "11. Reputation, Verified Reviews & Quality Assurance", 1)
    
    doc.add_paragraph(
        "Following departure confirmation, tenants are invited to submit a Verified Property Review across 4 objective pillars:"
    )
    pillars = [
        "Cleanliness & Hygiene: Upkeep of common areas, water availability, and waste disposal.",
        "Listing Accuracy: Alignment between published photos/amenities and physical reality.",
        "Landlord Responsiveness: Speed and professionalism in resolving maintenance requests.",
        "Overall Value for Money: Fairness of pricing relative to living standards."
    ]
    for p in pillars:
        doc.add_paragraph(p, style='List Bullet')
    
    doc.add_paragraph(
        "Only tenants with completed, verified bookings are permitted to post reviews, ensuring complete immunity against fake review manipulation."
    )

    # =========================================================================
    # CHAPTER 12: TECHNICAL ARCHITECTURE, DATA SCHEMAS & MOBILE PWA
    # =========================================================================
    add_heading_styled(doc, "12. Technical Architecture, Data Schemas & Mobile PWA Integration", 1)
    
    doc.add_paragraph(
        "Roomora is built on a scalable, production-grade technology stack:"
    )

    tech_table = doc.add_table(rows=6, cols=2)
    tech_data = [
        ("Backend Framework", "Django 5.x with Python 3.14 (Clean Architecture Service Layer)"),
        ("Database Layer", "PostgreSQL / SQLite with connection pooling, transactional locking, and indexing"),
        ("Frontend & Styling", "Vanilla CSS Design System with glassmorphism tokens, zero-dependency vanilla JS"),
        ("Mobile & PWA", "Capacitor.js Native Android APK wrapper + Progressive Web App (PWA) manifest"),
        ("Task Scheduling", "Asynchronous background task workers for soft-lock and overstay cron monitoring"),
        ("Deployment & Cloud", "Railway Cloud PaaS with Whitenoise static bundling and Paystack webhooks")
    ]
    for idx, (k, v) in enumerate(tech_data):
        row = tech_table.rows[idx]
        row.cells[0].paragraphs[0].text = k
        row.cells[1].paragraphs[0].text = v
    format_table(tech_table)

    # =========================================================================
    # CHAPTER 13: CONCLUSION & ARCHITECTURAL ROADMAP
    # =========================================================================
    add_heading_styled(doc, "13. Conclusion & Architectural Roadmap", 1)
    
    doc.add_paragraph(
        "Roomora represents a comprehensive paradigm shift in real estate technology for emerging student housing markets. "
        "By enforcing a state-driven 17-stage booking machine, atomic concurrency locking, multi-dimensional compatibility matching, "
        "and anti-fraud escrow protection, Roomora completely eliminates the vulnerability, friction, and chaos historically associated "
        "with student accommodation."
    )

    doc.add_paragraph(
        "Future architectural enhancements include IoT smart-lock keyless entry integration, AI-driven predictive roommate conflict detection, "
        "and cross-border multi-currency university tuition-and-housing escrow corridors."
    )

    output_path = r'C:\Users\Gazy\Downloads\school\ROOMORA\Roomora_Complete_Master_Documentation_v3.docx'
    doc.save(output_path)
    print(f"Master documentation successfully generated and saved to: {output_path}")

if __name__ == '__main__':
    generate_master_document()

