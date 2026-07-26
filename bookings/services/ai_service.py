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
    Provides intelligent location-based property recommendations,
    roommate compatibility insights, room concierge assistance, and safety analysis.
    """

    @classmethod
    def call_nvidia_llm(cls, prompt, system_prompt="You are Roomora AI, an intelligent AI assistant for student housing and roommate matching in Ghana.", max_tokens=350, temperature=0.6):
        """
        Executes a call to NVIDIA NIM API with robust error handling and fallback.
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
    def get_location_and_property_insights(cls, user, search_location="", selected_city=""):
        """
        Generates AI recommendations & location insights based on student location,
        institution, budget, and city.
        """
        user_city = selected_city or (user.city if hasattr(user, 'city') and user.city else "Accra")
        user_institution = getattr(user, 'institution', None) or "University Campus"
        user_name = user.first_name if hasattr(user, 'first_name') and user.first_name else "Student"

        prompt = (
            f"Generate 3 short, punchy AI property recommendations and location insights for a student named {user_name} "
            f"who is looking for accommodation near {search_location or user_institution} in {user_city}, Ghana. "
            f"Focus on proximity to campus, security, quiet study environments, and budget friendliness. "
            f"Return clean bullet points under 80 words."
        )

        ai_response = cls.call_nvidia_llm(prompt, max_tokens=200)
        
        if not ai_response:
            ai_response = (
                f"• High Proximity: Verified properties within 5–10 mins of {search_location or user_institution}.\n"
                f"• Verified Security: 24/7 personnel, CCTV coverage, and gated entry for peace of mind.\n"
                f"• Student Friendly: Includes high-speed Wi-Fi and dedicated study spaces."
            )
        return ai_response

    @classmethod
    def generate_roommate_compatibility_insights(cls, user, roommate_user, match_score):
        """
        Generates AI roommate compatibility summary and proactive conflict prevention advice.
        """
        user1_name = user.first_name if hasattr(user, 'first_name') and user.first_name else "Tenant"
        user2_name = roommate_user.first_name if hasattr(roommate_user, 'first_name') and roommate_user.first_name else "Roommate"

        prompt = (
            f"Analyze roommate pairing for {user1_name} and {user2_name} with a compatibility score of {match_score}%. "
            f"Provide a 2-sentence positive lifestyle match summary, followed by 1 helpful tip for smooth co-living. "
            f"Keep it professional, encouraging, and under 70 words."
        )

        ai_response = cls.call_nvidia_llm(prompt, max_tokens=150)

        if not ai_response:
            ai_response = (
                f"{user1_name} and {user2_name} show strong alignment on quiet study schedules and shared living habits ({match_score}% Match). "
                f"Proactive Tip: Agree on preferred air conditioning/fan settings and guest visit times early on to ensure seamless co-living."
            )
        return ai_response

    @classmethod
    def generate_concierge_chat_reply(cls, property_name, room_number, user_name, message):
        """
        Generates an AI Concierge response to student inquiries in the Room Portal chat.
        """
        prompt = (
            f"You are the Roomora AI Concierge assisting student {user_name} in Room {room_number} at {property_name}. "
            f"Answer this student question concisely and politely in 2-3 sentences: '{message}'"
        )

        ai_response = cls.call_nvidia_llm(prompt, max_tokens=150)

        if not ai_response:
            ai_response = (
                f"Hello {user_name}! Your inquiry regarding Room {room_number} at {property_name} has been logged. "
                f"Property management has been notified, and item declarations/room rules are active in your portal."
            )
        return ai_response

    @classmethod
    def analyze_declared_item_safety(cls, item_name, category):
        """
        Analyzes a declared appliance/item for power consumption and safety risks.
        """
        prompt = (
            f"Analyze electrical appliance/item '{item_name}' under category '{category}' for a student room. "
            f"Determine if it is HIGH, MEDIUM, or LOW power consumption, and whether it poses a safety/fire hazard. "
            f"Return JSON format: {{\"level\": \"HIGH\"|\"MEDIUM\"|\"LOW\", \"is_flagged\": true|false, \"advice\": \"short advice\"}}"
        )

        system_prompt = "You are a safety expert system. Respond strictly with valid JSON only."
        ai_response = cls.call_nvidia_llm(prompt, system_prompt=system_prompt, max_tokens=100, temperature=0.2)

        try:
            if ai_response:
                # Clean code blocks if present
                clean_json = ai_response.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except Exception:
            pass

        # Smart fallback
        item_lower = item_name.lower()
        if any(h in item_lower for h in ['heater', 'hot plate', 'cooker', 'iron', 'stove', 'ac', 'air conditioner']):
            return {"level": "HIGH", "is_flagged": True, "advice": "High power consumption appliance. Ensure property power limit compliance."}
        elif any(m in item_lower for m in ['fridge', 'microwave', 'kettle', 'blender', 'tv']):
            return {"level": "MEDIUM", "is_flagged": False, "advice": "Standard household appliance. Keep plugged into grounded wall socket."}
        else:
            return {"level": "LOW", "is_flagged": False, "advice": "Low power personal equipment."}
