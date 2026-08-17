"""
CompatibilityService - Roommate matching and compatibility scoring.
Handles lifestyle profile comparison and compatibility calculation.
"""

from django.db import transaction
from django.utils import timezone

from bookings.exceptions import CompatibilityError


class CompatibilityService:
    """Service for roommate compatibility matching."""
    
    def __init__(self):
        pass
    
    def calculate_compatibility(self, user_profile, other_profiles):
        """
        Calculate compatibility score between user and other profiles.
        
        Args:
            user_profile: LifestyleProfile of the user
            other_profiles: QuerySet of LifestyleProfile objects to compare against
            
        Returns:
            list: List of matches sorted by compatibility score
        """
        matches = []
        
        for other_profile in other_profiles:
            if other_profile.user == user_profile.user:
                continue
            
            score_data = self._calculate_score(user_profile, other_profile)
            matches.append({
                'tenant': other_profile.user,
                'profile': other_profile,
                'compatibility_score': score_data['total_score'],
                'score_data': score_data,
            })
        
        # Sort by compatibility score (highest first)
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return matches
    
    def _calculate_score(self, profile1, profile2):
        """
        Calculate detailed compatibility score between two profiles.
        
        Args:
            profile1: First LifestyleProfile
            profile2: Second LifestyleProfile
            
        Returns:
            dict: Detailed score breakdown
        """
        # High priority factors (weight: 40%)
        high_priority_score = self._calculate_high_priority(profile1, profile2)
        
        # Medium priority factors (weight: 35%)
        medium_priority_score = self._calculate_medium_priority(profile1, profile2)
        
        # Low priority factors (weight: 25%)
        low_priority_score = self._calculate_low_priority(profile1, profile2)
        
        # Total score
        total_score = (high_priority_score * 0.4) + (medium_priority_score * 0.35) + (low_priority_score * 0.25)
        
        # Generate alignment/difference summaries
        alignments, differences = self._generate_summaries(profile1, profile2)
        
        return {
            'total_score': round(total_score, 2),
            'high_priority_score': round(high_priority_score, 2),
            'medium_priority_score': round(medium_priority_score, 2),
            'low_priority_score': round(low_priority_score, 2),
            'alignments': alignments,
            'differences': differences,
        }
    
    def _calculate_high_priority(self, profile1, profile2):
        """
        Calculate high priority compatibility score.
        Factors: Sleep schedule, smoking, drinking.
        """
        score = 100
        
        # Sleep schedule compatibility
        if profile1.sleep_schedule != profile2.sleep_schedule:
            score -= 20
        
        # Smoking compatibility
        if profile1.smoking_preference != profile2.smoking_preference:
            score -= 30
        
        # Drinking compatibility
        if profile1.drinking_preference != profile2.drinking_preference:
            score -= 20
        
        return max(0, score)
    
    def _calculate_medium_priority(self, profile1, profile2):
        """
        Calculate medium priority compatibility score.
        Factors: Cleanliness, study habits, guests policy.
        """
        score = 100
        
        # Cleanliness compatibility
        cleanliness_diff = abs(profile1.cleanliness_level - profile2.cleanliness_level)
        score -= cleanliness_diff * 10
        
        # Study habits
        if profile1.study_preference != profile2.study_preference:
            score -= 15
        
        # Guests policy
        if profile1.guests_preference != profile2.guests_preference:
            score -= 15
        
        return max(0, score)
    
    def _calculate_low_priority(self, profile1, profile2):
        """
        Calculate low priority compatibility score.
        Factors: Social preferences, music/noise tolerance, hobbies.
        """
        score = 100
        
        # Social preference
        social_diff = abs(profile1.social_preference - profile2.social_preference)
        score -= social_diff * 5
        
        # Noise tolerance
        if profile1.noise_tolerance != profile2.noise_tolerance:
            score -= 10
        
        # Hobbies overlap (positive factor)
        hobbies1 = set(profile1.hobbies or [])
        hobbies2 = set(profile2.hobbies or [])
        if hobbies1 & hobbies2:  # If there's overlap
            score += 10
        
        return min(100, max(0, score))
    
    def _generate_summaries(self, profile1, profile2):
        """
        Generate alignment and difference summaries.
        """
        alignments = []
        differences = []
        
        # Check alignments
        if profile1.sleep_schedule == profile2.sleep_schedule:
            alignments.append(f"Both prefer {profile1.get_sleep_schedule_display()} sleep schedule")
        
        if profile1.smoking_preference == profile2.smoking_preference:
            alignments.append(f"Both have same smoking preference")
        
        if profile1.cleanliness_level == profile2.cleanliness_level:
            alignments.append(f"Both maintain similar cleanliness level")
        
        # Check differences
        if profile1.sleep_schedule != profile2.sleep_schedule:
            differences.append(f"Different sleep schedules: {profile1.get_sleep_schedule_display()} vs {profile2.get_sleep_schedule_display()}")
        
        if profile1.smoking_preference != profile2.smoking_preference:
            differences.append("Different smoking preferences")
        
        if profile1.guests_preference != profile2.guests_preference:
            differences.append("Different guest policies")
        
        return alignments, differences
    
    def find_compatible_matches(self, booking, user_profile):
        """
        Find compatible roommates for a booking.
        
        Args:
            booking: Booking object
            user_profile: LifestyleProfile of the user
            
        Returns:
            list: List of compatible matches with room information
        """
        from properties.models import Room
        from bookings.models import Booking
        
        # Find existing bookings in the same property and room type
        existing_bookings = Booking.objects.filter(
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type,
            status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
        ).exclude(tenant=booking.tenant)
        
        # Get lifestyle profiles of existing tenants
        from accounts.models import LifestyleProfile
        other_profiles = LifestyleProfile.objects.filter(
            user__in=existing_bookings.values('tenant')
        ).select_related('user')
        
        # Calculate compatibility
        matches = self.calculate_compatibility(user_profile, other_profiles)
        
        # Add room information to matches
        for match in matches:
            existing_booking = existing_bookings.filter(tenant=match['tenant']).first()
            if existing_booking and existing_booking.assigned_room:
                match['room'] = existing_booking.assigned_room
                match['room_id'] = existing_booking.assigned_room.id
                # Get other occupants in the same room
                match['occupants'] = Booking.objects.filter(
                    assigned_room=existing_booking.assigned_room,
                    status__in=['ACTIVE', 'CONFIRMED_ASSIGNED']
                ).exclude(tenant=match['tenant']).values_list('tenant', flat=True)
        
        return matches
    
    def save_compatibility_score(self, booking, roommate, score_data, routing_decision):
        """
        Save compatibility score to database.
        
        Args:
            booking: Booking object
            roommate: User object (potential roommate)
            score_data: Score calculation result
            routing_decision: 'AUTO_ASSIGN' or 'CONSENT_REQUIRED'
            
        Returns:
            CompatibilityScore object
        """
        from bookings.models import CompatibilityScore
        
        comp_score = CompatibilityScore.objects.create(
            booking=booking,
            roommate=roommate,
            score=score_data['total_score'],
            high_priority_score=score_data['high_priority_score'],
            medium_priority_score=score_data['medium_priority_score'],
            low_priority_score=score_data['low_priority_score'],
            alignment_summary='\n'.join(score_data['alignments']),
            difference_summary='\n'.join(score_data['differences']),
            routing_decision=routing_decision
        )
        
        return comp_score
    
    def get_routing_decision(self, compatibility_score):
        """
        Get routing decision based on compatibility score.
        
        Args:
            compatibility_score: Float score (0-100)
            
        Returns:
            str: 'AUTO_ASSIGN' or 'CONSENT_REQUIRED'
        """
        if compatibility_score >= 85:
            return 'AUTO_ASSIGN'
        return 'CONSENT_REQUIRED'
