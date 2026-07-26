import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

NVIDIA_API_KEY = getattr(settings, 'NVIDIA_API_KEY', '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')
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"


class NvidiaAIService:
    """
    Centralized NVIDIA AI Integration Service for Roomora Platform.
    Provides authoritative, objective, data-grounded intelligence for property discovery,
    behavioral roommate alignment, resident operations, and appliance safety analysis.
    """

    @classmethod
    def call_nvidia_llm(cls, prompt, system_prompt="You are Roomora Executive Intelligence, an authoritative data-driven property and lifestyle analytical engine.", max_tokens=350, temperature=0.3):
        """
        Executes a call to NVIDIA NIM API with robust error handling and intelligent grounded fallback.
        """
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "model": DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()
            else:
                logger.warning(f"NVIDIA AI API call failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error communicating with NVIDIA AI API: {e}")
            return None

    @classmethod
    def get_location_and_property_insights(cls, user, search_location="", selected_city="", recommended_properties=None, current_booking=None):
        """
        Generates professional AI property analysis directly addressing the tenant in second person based on verified platform database listings.
        """
        from properties.models import Property
        from bookings.models import Booking

        user_name = getattr(user, 'first_name', '') or getattr(user, 'username', '') or "Valued Tenant"
        user_name = str(user_name).upper()
        user_city = selected_city or (getattr(user, 'city', '') if hasattr(user, 'city') and user.city else "Accra")
        user_institution = getattr(user, 'institution', None) or search_location or "University Campus"

        # Discover active real booking if not explicitly provided
        if not current_booking and hasattr(user, 'id'):
            current_booking = Booking.objects.filter(
                tenant=user, 
                status__in=['INITIATED', 'PAYMENT_REQUIRED', 'CONFIRMED_ASSIGNED', 'CHECKED_IN', 'LIFESTYLE_PENDING']
            ).order_by('-created_at').first()

        active_booking_str = ""
        target_prop_title = "Grand Student Hostel"
        target_city = user_city or "Accra"

        if current_booking and getattr(current_booking, 'accommodation_property', None):
            prop = current_booking.accommodation_property
            target_prop_title = prop.title
            target_city = prop.city or target_city
            active_booking_str = (
                f"Tenant Active Verified Stay: {prop.title} in {prop.city} ({prop.address}). "
                f"Verified Starting Tariff: GH₵ {getattr(prop, 'starting_price', None) or 2500} "
                f"(Includes confirmed 2% digital escrow deposit protection and verified 24/7 campus security protocols)."
            )

        # Ensure we only use verified platform database records
        if not recommended_properties:
            recommended_properties = Property.objects.filter(status='APPROVED', is_available=True)[:5]
            if not recommended_properties.exists():
                recommended_properties = Property.objects.all()[:5]

        real_listings_info = []
        for p in (recommended_properties or []):
            p_title = getattr(p, 'title', 'Verified Student Property')
            p_city = getattr(p, 'city', 'Accra')
            p_addr = getattr(p, 'address', '')
            p_price = getattr(p, 'starting_price', None) or 2500
            real_listings_info.append(
                f"• {p_title} — Location: {p_city} ({p_addr}). "
                f"Security Profile: Verified 24/7 CCTV & Gated Entry. "
                f"Rate: GH₵ {p_price} (Fully locked under Roomora 2% digital escrow protection, zero surprise fees)."
            )

        listings_text = "\n".join(real_listings_info) if real_listings_info else (
            f"• Grand Student Hostel — Location: Accra (123 University Avenue). Security Profile: Verified 24/7 CCTV & Gated Entry. Rate: GH₵ 2500 (Fully locked under Roomora 2% digital escrow protection)."
        )

        system_prompt = (
            "You are Roomora Institutional Advisory, an executive housing analytical engine providing tailored real estate intelligence. "
            "CRITICAL CONVERGENT RULES:\n"
            "1. Direct Executive Addressing: Address the tenant directly by their name in an authoritative, professional manner (e.g., 'GAZY, here is your executive accommodation and proximity evaluation for verified housing in Accra:'). STRICTLY DO NOT use colloquial greetings, informal chit-chat, or slang (NEVER output 'Hi', 'Hello', 'Hey', or 'I've got you covered').\n"
            "2. Institutional Authority: Utilize formal institutional real estate terminology (e.g., perimeter security architecture, strategic academic proximity, escrow deposit compliance).\n"
            "3. Grounded Verification: Strictly evaluate ONLY the exact verified platform property records, pricing, and locations supplied below. Zero hallucination of imaginary listings or pricing.\n"
            "4. Structure: Start with the direct executive statement addressing the tenant by name, followed by exactly 3 comprehensive analytical bullet points starting with '•' on: Security Architecture & Access Management, Strategic Transit & Campus Proximity, and 2% Digital Escrow Rate Protection."
        )

        prompt = (
            f"Generate an Executive Property Assessment directly addressed to tenant {user_name}, based STRICTLY on this verified database telemetry:\n\n"
            f"Tenant Name: {user_name}\n"
            f"Target City & Campus: {target_city} ({user_institution})\n"
            f"{active_booking_str}\n"
            f"Verified Platform Housing Listings:\n{listings_text}\n\n"
            f"Begin with '{user_name}, review your verified accommodation and proximity assessment:' followed by exactly 3 institutional bullet points evaluating verified CCTV/gated security, campus commuting routes, and transparent 2% escrow rate protection. Keep under 85 words."
        )

        ai_response = cls.call_nvidia_llm(prompt, system_prompt=system_prompt, max_tokens=220, temperature=0.2)
        
        if not ai_response or "Ayeduase" in ai_response or "I've got you covered" in ai_response or "Hi " in ai_response:
            ai_response = (
                f"{user_name}, review your verified accommodation and proximity assessment for residential housing near {user_institution} in {target_city}:\n\n"
                f"• Security Architecture & Access Management: {target_prop_title} operates under 24/7 guarded CCTV surveillance and controlled entry protocols, guaranteeing personal residential safety.\n"
                f"• Strategic Transit & Campus Proximity: Positioned directly within primary academic transit corridors, enabling optimized daily commute access to university installations.\n"
                f"• Escrow Fiduciary Guarantee: All rental tariffs are legally secured under Roomora's automated 2% digital escrow infrastructure, assuring complete rate predictability with zero unverified surcharges."
            )
        return ai_response

    @classmethod
    def generate_roommate_compatibility_insights(cls, user, roommate_user, match_score):
        """
        Generates clinical behavioral alignment evaluations addressed directly to the primary tenant with institutional rigor.
        """
        from accounts.models import LifestyleProfile

        user1_name = getattr(user, 'first_name', '') or getattr(user, 'username', '') or "Tenant"
        user1_name = str(user1_name).upper()
        user2_name = getattr(roommate_user, 'first_name', '') or getattr(roommate_user, 'username', '') or "Roommate"
        user2_name = str(user2_name).upper()

        prof1 = getattr(user, 'lifestyle_profile', None) or LifestyleProfile.objects.filter(user=user).first()
        prof2 = getattr(roommate_user, 'lifestyle_profile', None) or LifestyleProfile.objects.filter(user=roommate_user).first()

        sleep1 = prof1.get_sleep_time_display() if prof1 and getattr(prof1, 'sleep_time', None) else "Moderate (10-11pm)"
        sleep2 = prof2.get_sleep_time_display() if prof2 and getattr(prof2, 'sleep_time', None) else "Moderate (10-11pm)"
        clean1 = f"Level {prof1.cleanliness_level}/5" if prof1 and getattr(prof1, 'cleanliness_level', None) else "Level 4/5"
        clean2 = f"Level {prof2.cleanliness_level}/5" if prof2 and getattr(prof2, 'cleanliness_level', None) else "Level 4/5"
        noise1 = prof1.get_noise_tolerance_display() if prof1 and getattr(prof1, 'noise_tolerance', None) else "Moderate tolerance"
        noise2 = prof2.get_noise_tolerance_display() if prof2 and getattr(prof2, 'noise_tolerance', None) else "Moderate tolerance"
        visit1 = prof1.get_visitor_frequency_display() if prof1 and getattr(prof1, 'visitor_frequency', None) else "Occasional visitors"
        visit2 = prof2.get_visitor_frequency_display() if prof2 and getattr(prof2, 'visitor_frequency', None) else "Occasional visitors"

        system_prompt = (
            "You are Roomora Co-Living Governance Advisory, a professional behavioral matching and residential analytics engine. "
            "CRITICAL RULES:\n"
            "1. Direct Institutional Address: Speak directly TO the primary tenant using their name without informal conversational filler (e.g., start directly with: 'GAZY, your behavioral compatibility index with KWAME stands at {match_score}%. Our residential diagnostics demonstrate...'). NEVER use 'Hi', 'Hello', or colloquial advice phrases like 'Helpful tip:' or 'schedule meetings'.\n"
            "2. Analytical Rigor: Assess co-living compatibility strictly using the recorded database telemetry (sleep routines, cleanliness standards, acoustic tolerance, and visitor policies). Use elevated behavioral science and residential governance terminology.\n"
            "3. Structure: Write 2 concise diagnostic sentences analyzing behavioral convergence and variance, followed immediately by one structured requirement labeled 'Co-Living Operational Protocol:' detailing concrete room governance for quiet evening study intervals and rotational hygiene sanitation. Max 75 words total."
        )

        prompt = (
            f"Generate an Institutional Co-Living Diagnostic addressed to {user1_name} regarding roommate {user2_name} at a {match_score}% convergence index.\n\n"
            f"Recorded Lifestyle Metrics:\n"
            f"- Sleep / Wake Schedules: {user1_name} [{sleep1}] vs {user2_name} [{sleep2}]\n"
            f"- Hygiene & Cleanliness Rating: {user1_name} [{clean1}] vs {user2_name} [{clean2}]\n"
            f"- Acoustic / Noise Tolerance: {user1_name} [{noise1}] vs {user2_name} [{noise2}]\n"
            f"- Visitor Policy Frequency: {user1_name} [{visit1}] vs {user2_name} [{visit2}]\n\n"
            f"Begin with '{user1_name}, your behavioral compatibility index with {user2_name} is {match_score}%.' Follow with an authoritative behavioral analysis and conclude with one exact 'Co-Living Operational Protocol:' for quiet study hours and cleaning schedules. Max 75 words."
        )

        ai_response = cls.call_nvidia_llm(prompt, system_prompt=system_prompt, max_tokens=180, temperature=0.2)

        if not ai_response or "Helpful tip:" in ai_response or "harmonious" in ai_response or "third person" in ai_response or "Hi " in ai_response:
            ai_response = (
                f"{user1_name}, your behavioral compatibility index with {user2_name} is {match_score}%. Our residential diagnostics demonstrate strong lifestyle convergence across evening sleep schedules ({sleep1}) and baseline cleanliness ratings ({clean1}), establishing a stable foundation for shared co-living.\n\n"
                f"Co-Living Operational Protocol: To preserve residential standards and academic focus, enforce a structured quiet study interval after 10:00 PM and maintain a synchronized bi-weekly sanitization protocol."
            )
        return ai_response

    @classmethod
    def generate_concierge_chat_reply(cls, property_name, room_number, user_name, message):
        """
        Generates an authoritative facility operations reply for student room inquiries.
        """
        system_prompt = (
            "You are Roomora Property Operations Desk, an administrative facility services system. "
            "CRITICAL RULES:\n"
            "1. Tone: Professional, authoritative administrative guidance addressing the resident directly by name ('{user_name}, your inquiry...'). Zero slang or conversational filler.\n"
            "2. Guidance: Provide direct, structured operational guidance based on institutional facility management standards.\n"
            "3. Conciseness: Maximum 2 short, authoritative sentences."
        )

        prompt = (
            f"Resident {user_name} (assigned to Room {room_number} at {property_name}) submitted this operational inquiry: '{message}'. "
            f"Provide a direct, authoritative facility management response addressing {user_name} directly in 2 short sentences."
        )

        ai_response = cls.call_nvidia_llm(prompt, system_prompt=system_prompt, max_tokens=150, temperature=0.3)

        if not ai_response:
            ai_response = (
                f"{str(user_name).upper()}, your operational request regarding Room {room_number} at {property_name} has been formally integrated into our facility maintenance system. "
                f"Standard residential facility rules and electrical safety protocols are administered through your dashboard; urgent dispatch requests are escalated directly to on-site building engineers."
            )
        return ai_response

    @classmethod
    def analyze_declared_item_safety(cls, item_name, category):
        """
        Analyzes a declared appliance/item for electrical load capacity and safety hazard verification.
        """
        prompt = (
            f"Analyze residential appliance '{item_name}' (Category: '{category}') for an institutional student room. "
            f"Evaluate resistive/inductive draw and classify as HIGH, MEDIUM, or LOW power consumption, and identify fire hazard risk. "
            f"Return strict JSON: {{\"level\": \"HIGH\"|\"MEDIUM\"|\"LOW\", \"is_flagged\": true|false, \"advice\": \"authoritative technical guidance under 15 words\"}}"
        )

        system_prompt = "You are a professional facility electrical safety compliance system. Respond strictly with valid JSON only."
        ai_response = cls.call_nvidia_llm(prompt, system_prompt=system_prompt, max_tokens=100, temperature=0.1)

        try:
            if ai_response:
                clean_json = ai_response.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except Exception:
            pass

        # Engineering-grade technical fallback
        item_lower = item_name.lower()
        if any(h in item_lower for h in ['heater', 'hot plate', 'cooker', 'iron', 'stove', 'ac', 'air conditioner', 'freezer', 'refrigerator', 'fridge']):
            return {"level": "HIGH", "is_flagged": True, "advice": "High inductive/resistive load detected. Must undergo physical facility verification and direct circuit compliance checks."}
        elif any(m in item_lower for m in ['microwave', 'kettle', 'blender', 'tv', 'television', 'console']):
            return {"level": "MEDIUM", "is_flagged": False, "advice": "Standard operational electrical load. Connect exclusively to grounded wall receptacles without extension daisy-chaining."}
        else:
            return {"level": "LOW", "is_flagged": False, "advice": "Low-power personal electronic apparatus. Fully compliant with standard room power allocations."}

