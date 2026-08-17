"""
Compatibility Service

Calculates compatibility scores between lifestyle profiles for roommate matching.
Uses weighted multi-factor model with high/medium/low priority tiers.

PART 6: THE COMPATIBILITY ENGINE
- High-Priority Factors (70%): Sleep, Wake, Cleanliness, Noise, Visitors, Smoking, Privacy
- Medium-Priority Factors (20%): Study, Cooking, Temperature
- Low-Priority Factors (10%): Social, Food Sharing, Borrowing
- Multi-occupancy: Averages pairwise scores for triple/quad rooms
- Generates alignment and difference summaries
"""

from typing import Dict, List, Tuple
from accounts.models import LifestyleProfile


class CompatibilityService:
    """Service for calculating compatibility between lifestyle profiles"""
    
    # Enum mappings for distance calculations
    SLEEP_TIME_MAP = {'VERY_EARLY': 1, 'EARLY': 2, 'MODERATE': 3, 'LATE': 4, 'VERY_LATE': 5}
    WAKE_TIME_MAP = {'VERY_EARLY': 1, 'EARLY': 2, 'MODERATE': 3, 'LATE': 4, 'VERY_LATE': 5}
    NOISE_TOLERANCE_MAP = {'LOW': 1, 'MODERATE': 2, 'HIGH': 3, 'VERY_HIGH': 4}
    VISITOR_FREQUENCY_MAP = {'RARELY': 1, 'OCCASIONALLY': 2, 'FREQUENTLY': 3, 'VERY_FREQUENTLY': 4}
    PRIVACY_IMPORTANCE_MAP = {'VERY_IMPORTANT': 1, 'IMPORTANT': 2, 'SOMEWHAT': 3, 'NOT_IMPORTANT': 4}
    STUDY_LOCATION_MAP = {'MAINLY_OUTSIDE': 1, 'MIXED': 2, 'MAINLY_IN_ROOM': 3}
    COOKING_FREQUENCY_MAP = {'NEVER': 1, 'WEEKLY': 2, 'FREQUENTLY': 3, 'DAILY': 4}
    TEMPERATURE_MAP = {'VERY_COLD': 1, 'COOL': 2, 'MODERATE': 3, 'WARM': 4, 'VERY_WARM': 5}
    FOOD_SHARING_MAP = {'ASK_FIRST': 1, 'SHARE_FREELY': 2, 'OWN_ITEMS': 3}
    BORROWING_MAP = {'ALWAYS': 1, 'ASK_FIRST': 2, 'RARELY': 3, 'NEVER': 4}
    
    # Distance scoring for high-priority factors
    SLEEP_TIME_DISTANCE = {0: 100, 1: 85, 2: 70, 3: 50, 4: 30}
    WAKE_TIME_DISTANCE = {0: 100, 1: 88, 2: 72, 3: 55, 4: 35}
    CLEANLINESS_DISTANCE = {0: 100, 1: 80, 2: 60, 3: 40, 4: 20}
    NOISE_TOLERANCE_DISTANCE = {0: 100, 1: 80, 2: 60, 3: 35}
    VISITOR_FREQUENCY_DISTANCE = {0: 100, 1: 82, 2: 60, 3: 30}
    PRIVACY_IMPORTANCE_DISTANCE = {0: 100, 1: 82, 2: 65, 3: 40}
    
    # Distance scoring for medium-priority factors
    STUDY_LOCATION_SCORE = {0: 100, 1: 70}  # 0 = same, 1 = one step diff
    COOKING_FREQUENCY_DISTANCE = {0: 100, 1: 85, 2: 70, 3: 50}
    TEMPERATURE_DISTANCE = {0: 100, 1: 88, 2: 72, 3: 55, 4: 35}
    
    # Distance scoring for low-priority factors
    FOOD_SHARING_SCORE = {0: 100, 1: 80, 2: 50}  # 0 = same, 1 = adjacent, 2 = opposite
    BORROWING_SCORE = {0: 100, 1: 85, 2: 55}  # 0 = same, 1 = adjacent, 2 = opposite
    
    # Routing threshold
    ROUTING_THRESHOLD = 85
    
    @staticmethod
    def calculate_compatibility(profile1: LifestyleProfile, profile2: LifestyleProfile) -> Dict:
        """
        Calculate overall compatibility score between two profiles using weighted multi-factor model.
        Returns a dict with score, breakdown, alignments, and differences.
        """
        if not profile1 or not profile2:
            return {'score': 0, 'error': 'Profiles not found'}
        
        # Calculate high-priority factor scores (70% weight)
        high_priority_scores = {
            'sleep_time': CompatibilityService._calculate_sleep_time_score(profile1, profile2),
            'wake_time': CompatibilityService._calculate_wake_time_score(profile1, profile2),
            'cleanliness': CompatibilityService._calculate_cleanliness_score(profile1, profile2),
            'noise_tolerance': CompatibilityService._calculate_noise_score(profile1, profile2),
            'visitor_frequency': CompatibilityService._calculate_visitor_score(profile1, profile2),
            'smoking': CompatibilityService._calculate_smoking_score(profile1, profile2),
            'privacy': CompatibilityService._calculate_privacy_score(profile1, profile2),
        }
        high_avg = sum(high_priority_scores.values()) / len(high_priority_scores)
        high_weighted = high_avg * 0.70
        
        # Calculate medium-priority factor scores (20% weight)
        medium_priority_scores = {
            'study_location': CompatibilityService._calculate_study_score(profile1, profile2),
            'cooking_frequency': CompatibilityService._calculate_cooking_score(profile1, profile2),
            'temperature': CompatibilityService._calculate_temperature_score(profile1, profile2),
        }
        medium_avg = sum(medium_priority_scores.values()) / len(medium_priority_scores)
        medium_weighted = medium_avg * 0.20
        
        # Calculate low-priority factor scores (10% weight)
        low_priority_scores = {
            'social': CompatibilityService._calculate_social_score(profile1, profile2),
            'food_sharing': CompatibilityService._calculate_food_sharing_score(profile1, profile2),
            'borrowing': CompatibilityService._calculate_borrowing_score(profile1, profile2),
        }
        low_avg = sum(low_priority_scores.values()) / len(low_priority_scores)
        low_weighted = low_avg * 0.10
        
        # Final score
        final_score = round(high_weighted + medium_weighted + low_weighted)
        
        # Generate alignments and differences
        all_scores = {**high_priority_scores, **medium_priority_scores, **low_priority_scores}
        alignments = CompatibilityService._generate_alignments(profile1, profile2, all_scores)
        differences = CompatibilityService._generate_differences(profile1, profile2, all_scores)
        
        return {
            'score': final_score,
            'high_priority': {
                'scores': high_priority_scores,
                'average': round(high_avg, 1),
                'weighted': round(high_weighted, 1)
            },
            'medium_priority': {
                'scores': medium_priority_scores,
                'average': round(medium_avg, 1),
                'weighted': round(medium_weighted, 1)
            },
            'low_priority': {
                'scores': low_priority_scores,
                'average': round(low_avg, 1),
                'weighted': round(low_weighted, 1)
            },
            'alignments': alignments,
            'differences': differences,
            'auto_assign': final_score >= CompatibilityService.ROUTING_THRESHOLD
        }
    
    @staticmethod
    def calculate_room_compatibility(new_profile: LifestyleProfile, existing_profiles: List[LifestyleProfile]) -> Dict:
        """
        Calculate room-level compatibility for multi-occupancy rooms.
        Averages pairwise scores between new user and all existing occupants.
        """
        if not existing_profiles:
            return {'score': 0, 'error': 'No existing profiles'}
        
        pairwise_scores = []
        all_alignments = []
        all_differences = []
        
        for existing_profile in existing_profiles:
            result = CompatibilityService.calculate_compatibility(new_profile, existing_profile)
            pairwise_scores.append(result['score'])
            all_alignments.extend(result['alignments'])
            all_differences.extend(result['differences'])
        
        room_score = round(sum(pairwise_scores) / len(pairwise_scores))
        
        return {
            'score': room_score,
            'pairwise_scores': pairwise_scores,
            'auto_assign': room_score >= CompatibilityService.ROUTING_THRESHOLD,
            'alignments': all_alignments,
            'differences': all_differences
        }
    
    # HIGH-PRIORITY FACTOR CALCULATIONS
    
    @staticmethod
    def _calculate_sleep_time_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate sleep time compatibility using distance scoring"""
        s1 = CompatibilityService.SLEEP_TIME_MAP.get(getattr(p1, 'sleep_time', 'MODERATE'), 3)
        s2 = CompatibilityService.SLEEP_TIME_MAP.get(getattr(p2, 'sleep_time', 'MODERATE'), 3)
        diff = abs(s1 - s2)
        return float(CompatibilityService.SLEEP_TIME_DISTANCE.get(diff, 30))
    
    @staticmethod
    def _calculate_wake_time_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate wake time compatibility using distance scoring"""
        w1 = CompatibilityService.WAKE_TIME_MAP.get(getattr(p1, 'wake_time', 'MODERATE'), 3)
        w2 = CompatibilityService.WAKE_TIME_MAP.get(getattr(p2, 'wake_time', 'MODERATE'), 3)
        diff = abs(w1 - w2)
        return float(CompatibilityService.WAKE_TIME_DISTANCE.get(diff, 35))
    
    @staticmethod
    def _calculate_cleanliness_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate cleanliness compatibility using distance scoring"""
        c1 = getattr(p1, 'personal_cleanliness_level', 3)
        c2 = getattr(p2, 'personal_cleanliness_level', 3)
        # Convert to 1-5 scale if needed
        if isinstance(c1, str):
            c1 = int(c1) if c1.isdigit() else 3
        if isinstance(c2, str):
            c2 = int(c2) if c2.isdigit() else 3
        diff = abs(int(c1) - int(c2))
        return float(CompatibilityService.CLEANLINESS_DISTANCE.get(diff, 20))
    
    @staticmethod
    def _calculate_noise_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate noise tolerance compatibility using distance scoring"""
        n1 = CompatibilityService.NOISE_TOLERANCE_MAP.get(getattr(p1, 'noise_tolerance', 'MODERATE'), 2)
        n2 = CompatibilityService.NOISE_TOLERANCE_MAP.get(getattr(p2, 'noise_tolerance', 'MODERATE'), 2)
        diff = abs(n1 - n2)
        return float(CompatibilityService.NOISE_TOLERANCE_DISTANCE.get(diff, 35))
    
    @staticmethod
    def _calculate_visitor_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate visitor frequency compatibility using distance scoring"""
        v1 = CompatibilityService.VISITOR_FREQUENCY_MAP.get(getattr(p1, 'visitor_frequency', 'OCCASIONALLY'), 2)
        v2 = CompatibilityService.VISITOR_FREQUENCY_MAP.get(getattr(p2, 'visitor_frequency', 'OCCASIONALLY'), 2)
        diff = abs(v1 - v2)
        return float(CompatibilityService.VISITOR_FREQUENCY_DISTANCE.get(diff, 30))
    
    @staticmethod
    def _calculate_smoking_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate smoking compatibility (binary/special scoring)"""
        s1 = getattr(p1, 'smoking_tolerance', 'NON_SMOKER')
        s2 = getattr(p2, 'smoking_tolerance', 'NON_SMOKER')
        
        # Both non-smokers
        if s1 == 'NON_SMOKER' and s2 == 'NON_SMOKER':
            return 100.0
        # Any smoker vs non-smoker
        elif (s1 == 'NON_SMOKER') != (s2 == 'NON_SMOKER'):
            return 25.0
        # Both smokers
        else:
            return 85.0
    
    @staticmethod
    def _calculate_privacy_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate privacy importance compatibility using distance scoring"""
        p1_val = CompatibilityService.PRIVACY_IMPORTANCE_MAP.get(getattr(p1, 'privacy_preference', 'IMPORTANT'), 2)
        p2_val = CompatibilityService.PRIVACY_IMPORTANCE_MAP.get(getattr(p2, 'privacy_preference', 'IMPORTANT'), 2)
        diff = abs(p1_val - p2_val)
        return float(CompatibilityService.PRIVACY_IMPORTANCE_DISTANCE.get(diff, 40))
    
    # MEDIUM-PRIORITY FACTOR CALCULATIONS
    
    @staticmethod
    def _calculate_study_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate study location compatibility"""
        s1 = CompatibilityService.STUDY_LOCATION_MAP.get(getattr(p1, 'study_location', 'MIXED'), 2)
        s2 = CompatibilityService.STUDY_LOCATION_MAP.get(getattr(p2, 'study_location', 'MIXED'), 2)
        diff = abs(s1 - s2)
        return float(CompatibilityService.STUDY_LOCATION_SCORE.get(diff, 70))
    
    @staticmethod
    def _calculate_cooking_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate cooking frequency compatibility using distance scoring"""
        c1 = CompatibilityService.COOKING_FREQUENCY_MAP.get(getattr(p1, 'cooking_frequency', 'WEEKLY'), 2)
        c2 = CompatibilityService.COOKING_FREQUENCY_MAP.get(getattr(p2, 'cooking_frequency', 'WEEKLY'), 2)
        diff = abs(c1 - c2)
        return float(CompatibilityService.COOKING_FREQUENCY_DISTANCE.get(diff, 50))
    
    @staticmethod
    def _calculate_temperature_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate temperature preference compatibility using distance scoring"""
        t1 = CompatibilityService.TEMPERATURE_MAP.get(getattr(p1, 'preferred_temperature', 'MODERATE'), 3)
        t2 = CompatibilityService.TEMPERATURE_MAP.get(getattr(p2, 'preferred_temperature', 'MODERATE'), 3)
        diff = abs(t1 - t2)
        return float(CompatibilityService.TEMPERATURE_DISTANCE.get(diff, 35))
    
    # LOW-PRIORITY FACTOR CALCULATIONS
    
    @staticmethod
    def _calculate_social_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate social lifestyle compatibility (proxy via noise tolerance)"""
        # Use noise tolerance as proxy for social lifestyle
        n1 = CompatibilityService.NOISE_TOLERANCE_MAP.get(getattr(p1, 'noise_tolerance', 'MODERATE'), 2)
        n2 = CompatibilityService.NOISE_TOLERANCE_MAP.get(getattr(p2, 'noise_tolerance', 'MODERATE'), 2)
        diff = abs(n1 - n2)
        # Similar to noise but slightly different weights
        return max(30.0, 100.0 - (diff * 25.0))
    
    @staticmethod
    def _calculate_food_sharing_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate food sharing comfort compatibility"""
        f1 = CompatibilityService.FOOD_SHARING_MAP.get(getattr(p1, 'food_sharing_comfort', 'ASK_FIRST'), 2)
        f2 = CompatibilityService.FOOD_SHARING_MAP.get(getattr(p2, 'food_sharing_comfort', 'ASK_FIRST'), 2)
        diff = abs(f1 - f2)
        return float(CompatibilityService.FOOD_SHARING_SCORE.get(diff, 50))
    
    @staticmethod
    def _calculate_borrowing_score(p1: LifestyleProfile, p2: LifestyleProfile) -> float:
        """Calculate borrowing comfort compatibility"""
        b1 = CompatibilityService.BORROWING_MAP.get(getattr(p1, 'shared_items_comfort', 'ASK_FIRST'), 2)
        b2 = CompatibilityService.BORROWING_MAP.get(getattr(p2, 'shared_items_comfort', 'ASK_FIRST'), 2)
        diff = abs(b1 - b2)
        return float(CompatibilityService.BORROWING_SCORE.get(diff, 55))
    
    # ALIGNMENT AND DIFFERENCE GENERATION
    
    @staticmethod
    def _generate_alignments(p1: LifestyleProfile, p2: LifestyleProfile, scores: Dict) -> List[Dict]:
        """Generate alignment summaries for factors scoring 85% or above"""
        alignments = []
        
        if scores.get('cleanliness', 0) >= 85:
            c1 = getattr(p1, 'personal_cleanliness_level', 3)
            alignments.append({
                'factor': 'Cleanliness Standards',
                'score': scores['cleanliness'],
                'description': f'You both maintain {c1}/5 cleanliness standards'
            })
        
        if scores.get('visitor_frequency', 0) >= 85:
            v1 = getattr(p1, 'visitor_frequency', 'OCCASIONALLY')
            alignments.append({
                'factor': 'Visitor Policies',
                'score': scores['visitor_frequency'],
                'description': f'You both have {str(v1).lower()} visitors with similar policies'
            })
        
        if scores.get('smoking', 0) >= 85:
            alignments.append({
                'factor': 'Non-Smoking',
                'score': scores['smoking'],
                'description': 'Your room will be completely smoke-free'
            })
        
        if scores.get('cooking_frequency', 0) >= 85:
            c1 = getattr(p1, 'cooking_frequency', 'WEEKLY')
            alignments.append({
                'factor': 'Kitchen and Cooking',
                'score': scores['cooking_frequency'],
                'description': f'You both cook {str(c1).lower()} and are comfortable sharing the kitchen'
            })
        
        if scores.get('temperature', 0) >= 85:
            t1 = getattr(p1, 'preferred_temperature', 'MODERATE')
            t1_display = f"{t1}°C" if isinstance(t1, (int, float)) or (isinstance(t1, str) and t1.isdigit()) else str(t1).lower()
            alignments.append({
                'factor': 'Temperature',
                'score': scores['temperature'],
                'description': f'You both prefer {t1_display} temperatures'
            })
        
        if scores.get('borrowing', 0) >= 85:
            b1 = getattr(p1, 'shared_items_comfort', 'ASK_FIRST')
            alignments.append({
                'factor': 'Shared Items',
                'score': scores['borrowing'],
                'description': f'You both use {str(b1).lower().replace("_", " ")} for shared items'
            })
        
        return alignments
    
    @staticmethod
    def _generate_differences(p1: LifestyleProfile, p2: LifestyleProfile, scores: Dict) -> List[Dict]:
        """Generate difference summaries for factors scoring below 85%"""
        differences = []
        
        if scores.get('sleep_time', 100) < 85:
            s1 = CompatibilityService._get_sleep_display(getattr(p1, 'sleep_time', 'MODERATE'))
            s2 = CompatibilityService._get_sleep_display(getattr(p2, 'sleep_time', 'MODERATE'))
            diff = abs(CompatibilityService.SLEEP_TIME_MAP.get(getattr(p1, 'sleep_time', 'MODERATE'), 3) - 
                       CompatibilityService.SLEEP_TIME_MAP.get(getattr(p2, 'sleep_time', 'MODERATE'), 3))
            differences.append({
                'factor': 'Sleep Schedule',
                'score': scores['sleep_time'],
                'your_value': s1,
                'roommate_value': s2,
                'difference': f'{diff} category levels',
                'implication': 'Your roommate will be asleep while you may still be active. This could cause disturbance through light or noise.',
                'suggestion': 'Can we agree on a lights-down rule after 10pm? I\'m happy to use headphones.'
            })
        
        if scores.get('noise_tolerance', 100) < 85:
            n1 = getattr(p1, 'noise_tolerance', 'MODERATE')
            n2 = getattr(p2, 'noise_tolerance', 'MODERATE')
            differences.append({
                'factor': 'Noise Tolerance',
                'score': scores['noise_tolerance'],
                'your_value': str(n1).lower().replace('_', ' '),
                'roommate_value': str(n2).lower().replace('_', ' '),
                'difference': 'Different tolerance levels',
                'implication': 'You are naturally comfortable with more background noise than your roommate prefers.',
                'suggestion': 'Let me know if anything I do is too loud — I want us both to be comfortable.'
            })
        
        if scores.get('privacy', 100) < 85:
            p1_val = getattr(p1, 'privacy_preference', 'IMPORTANT')
            p2_val = getattr(p2, 'privacy_preference', 'IMPORTANT')
            differences.append({
                'factor': 'Privacy Preferences',
                'score': scores['privacy'],
                'your_value': str(p1_val).lower().replace('_', ' '),
                'roommate_value': str(p2_val).lower().replace('_', ' '),
                'difference': 'Different privacy needs',
                'implication': 'You may have different expectations around personal space and alone time.',
                'suggestion': 'Let\'s discuss what privacy means to each of us so we can respect both perspectives.'
            })
        
        return differences
    
    @staticmethod
    def _get_sleep_display(sleep_time: str) -> str:
        """Get human-readable sleep time display"""
        display_map = {
            'VERY_EARLY': 'Before 9pm',
            'EARLY': 'Around 9-10pm',
            'MODERATE': 'Around 10-11pm',
            'LATE': 'After 11pm',
            'VERY_LATE': 'Midnight or later'
        }
        return display_map.get(sleep_time, sleep_time)
