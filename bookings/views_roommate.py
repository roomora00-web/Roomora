"""Phase 7 Roommate Profile API Views"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from accounts.models import User, LifestyleProfile
from bookings.models import Booking, RoommateMatch


class RoommateProfileViewSet(viewsets.ViewSet):
    """
    Phase 7: Roommate Profile Page
    
    Provides detailed roommate information including:
    - Profile photo & basic info
    - Living preferences breakdown by category
    - Compatibility score with current user
    - Areas of alignment & difference
    - Suggested conversation starters
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Not used - profiles are accessed via booking or user_id"""
        return Response({'detail': 'Use retrieve() with booking_id or user_id'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_booking(self, request):
        """
        GET /api/roommates/by_booking/?booking_id={id}
        Get roommate profile for a specific booking
        """
        booking_id = request.query_params.get('booking_id')
        
        if not booking_id:
            return Response({'error': 'booking_id required'}, status=400)
        
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Access control: Only booking tenant can view
        if booking.tenant != request.user:
            return Response({'error': 'Access denied'}, status=403)
        
        roommates = []
        
        # Get roommates from assignment or match
        if hasattr(booking, 'room_assignment') and booking.room_assignment.assigned_roommates.exists():
            roommates = list(booking.room_assignment.assigned_roommates.all())
        elif booking.preferred_roommates.exists():
            roommates = list(booking.preferred_roommates.all())
        
        if not roommates:
            return Response({'error': 'No roommates assigned yet'}, status=404)
        
        # Return profiles for all roommates
        roommates_data = []
        for roommate in roommates:
            # Get match score
            match = booking.roommate_matches.filter(user=roommate).first()
            if match:
                match_score = match.compatibility_score or 0
            else:
                match_score = booking.compatibility_score or 0
            
            # Get roommate lifestyle profile
            lifestyle = getattr(roommate, 'lifestyle_profile', None)
            
            roommates_data.append(self._format_roommate_profile(
                roommate, lifestyle, match_score, request.user
            ))
        
        return Response({'roommates': roommates_data})
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """
        GET /api/roommates/by_user/{user_id}/
        Get public roommate profile (lite version without compatibility)
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=400)
        
        roommate = get_object_or_404(User, id=user_id)
        lifestyle = getattr(roommate, 'lifestyle_profile', None)
        
        # Return lite profile (no compatibility scores)
        return Response({
            'user': {
                'id': roommate.id,
                'name': roommate.full_name,
                'email': roommate.email,
                'user_type': roommate.get_user_type_display(),
                'profile_picture': roommate.profile_picture.url if roommate.profile_picture else None,
                'joined': roommate.date_joined.date(),
            },
            'profile': getattr(roommate, 'profile', None).__dict__ if hasattr(roommate, 'profile') else {},
            'preferences': self._format_lifestyle_preferences(lifestyle) if lifestyle else {},
        })
    
    def _format_roommate_profile(self, roommate, lifestyle, match_score, request_user):
        """Format complete roommate profile with compatibility details"""
        
        # Basic info
        profile_data = {
            'user': {
                'id': roommate.id,
                'name': roommate.full_name,
                'email': roommate.email,
                'user_type': roommate.get_user_type_display(),
                'profile_picture': roommate.profile_picture.url if roommate.profile_picture else None,
                'joined': roommate.date_joined.date(),
                'phone_verified': roommate.phone_verified,
            },
            'compatibility': {
                'score': int(match_score),
                'verdict': self._get_compatibility_verdict(match_score),
                'color': self._get_score_color(match_score),
            }
        }
        
        # User profile info
        if hasattr(roommate, 'profile'):
            user_profile = roommate.profile
            profile_data['profile'] = {
                'institution': user_profile.institution,
                'location_preference': user_profile.location_preference,
                'bio': user_profile.bio,
                'verification_status': user_profile.verification_status,
            }
        
        # Lifestyle preferences breakdown
        if lifestyle:
            profile_data['preferences'] = self._format_lifestyle_preferences(lifestyle)
            
            # Calculate alignment/differences vs. request user
            request_user_lifestyle = getattr(request_user, 'lifestyle_profile', None)
            if request_user_lifestyle:
                alignment_data = self._calculate_alignment(
                    request_user_lifestyle, lifestyle, match_score
                )
                profile_data['alignment'] = alignment_data
        
        return profile_data
    
    def _format_lifestyle_preferences(self, lifestyle):
        """Format lifestyle preferences by category"""
        
        return {
            'sleep': {
                'schedule': lifestyle.get_sleep_schedule_display() if lifestyle.sleep_schedule else 'Not specified',
                'wake_time': lifestyle.get_wake_time_display() if lifestyle.wake_time else 'Not specified',
            },
            'cleanliness': {
                'rating': lifestyle.cleanliness_rating if lifestyle.cleanliness_rating else 'Not specified',
                'frequency': f"{lifestyle.cleaning_frequency} per week" if lifestyle.cleaning_frequency else 'Not specified',
            },
            'study_work': {
                'habits': lifestyle.get_study_habits_display() if lifestyle.study_habits else 'Not specified',
                'focus_time': f"{lifestyle.study_focus_time} hours/day" if lifestyle.study_focus_time else 'Not specified',
            },
            'social': {
                'personality': lifestyle.get_social_personality_display() if lifestyle.social_personality else 'Not specified',
                'visitors': lifestyle.get_visitor_preference_display() if lifestyle.visitor_preference else 'Not specified',
            },
            'noise_comfort': {
                'tolerance': lifestyle.get_noise_tolerance_display() if lifestyle.noise_tolerance else 'Not specified',
                'music': lifestyle.music_preference if lifestyle.music_preference else 'Not specified',
            },
            'living_space': {
                'shared_spaces': lifestyle.shared_spaces_comfort if lifestyle.shared_spaces_comfort else 'Not specified',
                'temperature': lifestyle.temperature_preference if lifestyle.temperature_preference else 'Not specified',
            },
            'boundaries': {
                'guest_access': lifestyle.guest_access_policy if lifestyle.guest_access_policy else 'Not specified',
                'kitchen_shared': lifestyle.kitchen_shared if lifestyle.kitchen_shared is not None else 'Not specified',
                'bathroom_shared': lifestyle.bathroom_shared if lifestyle.bathroom_shared is not None else 'Not specified',
            },
        }
    
    def _calculate_alignment(self, my_lifestyle, roommate_lifestyle, match_score):
        """Calculate where preferences align & differ"""
        
        alignment_factors = []
        difference_factors = []
        
        # Sleep schedule alignment
        if my_lifestyle.sleep_schedule == roommate_lifestyle.sleep_schedule:
            alignment_factors.append({
                'category': 'Sleep Schedule',
                'alignment': f"Both {my_lifestyle.get_sleep_schedule_display().lower()}",
            })
        else:
            difference_factors.append({
                'category': 'Sleep Schedule',
                'your_preference': my_lifestyle.get_sleep_schedule_display(),
                'roommate_preference': roommate_lifestyle.get_sleep_schedule_display(),
                'tip': 'Agree on quiet hours and respect each other\'s sleep times',
            })
        
        # Cleanliness alignment
        if my_lifestyle.cleanliness_rating == roommate_lifestyle.cleanliness_rating:
            alignment_factors.append({
                'category': 'Cleanliness Standards',
                'alignment': f"Both rate cleanliness as {my_lifestyle.cleanliness_rating}/5",
            })
        elif abs((my_lifestyle.cleanliness_rating or 3) - (roommate_lifestyle.cleanliness_rating or 3)) <= 1:
            alignment_factors.append({
                'category': 'Cleanliness Standards',
                'alignment': 'Very similar standards',
            })
        else:
            difference_factors.append({
                'category': 'Cleanliness Standards',
                'your_preference': f"{my_lifestyle.cleanliness_rating or 'Not set'}/5",
                'roommate_preference': f"{roommate_lifestyle.cleanliness_rating or 'Not set'}/5",
                'tip': 'Set up a cleaning schedule and discuss standards upfront',
            })
        
        # Visitor preferences
        if my_lifestyle.visitor_preference == roommate_lifestyle.visitor_preference:
            alignment_factors.append({
                'category': 'Visitor Preferences',
                'alignment': f"Both prefer {my_lifestyle.get_visitor_preference_display().lower()}",
            })
        else:
            difference_factors.append({
                'category': 'Visitor Preferences',
                'your_preference': my_lifestyle.get_visitor_preference_display(),
                'roommate_preference': roommate_lifestyle.get_visitor_preference_display(),
                'tip': 'Establish a notice period policy (e.g., 24 hours for overnight guests)',
            })
        
        # Noise tolerance
        if my_lifestyle.noise_tolerance == roommate_lifestyle.noise_tolerance:
            alignment_factors.append({
                'category': 'Noise Tolerance',
                'alignment': f"Both have {my_lifestyle.get_noise_tolerance_display().lower()} tolerance",
            })
        else:
            difference_factors.append({
                'category': 'Noise Tolerance',
                'your_preference': my_lifestyle.get_noise_tolerance_display(),
                'roommate_preference': roommate_lifestyle.get_noise_tolerance_display(),
                'tip': 'Use headphones, agree on study/quiet hours, warn about gatherings',
            })
        
        # Social personality
        if my_lifestyle.social_personality == roommate_lifestyle.social_personality:
            alignment_factors.append({
                'category': 'Social Style',
                'alignment': f"Both are {my_lifestyle.get_social_personality_display().lower()}",
            })
        else:
            difference_factors.append({
                'category': 'Social Style',
                'your_preference': my_lifestyle.get_social_personality_display(),
                'roommate_preference': roommate_lifestyle.get_social_personality_display(),
                'tip': 'Respect each other\'s need for social time vs. alone time',
            })
        
        return {
            'alignment_count': len(alignment_factors),
            'difference_count': len(difference_factors),
            'alignment': alignment_factors[:3],  # Top 3
            'differences': difference_factors[:3],  # Top 3
            'suggestion_count': min(3, len(difference_factors)),
        }
    
    def _get_compatibility_verdict(self, score):
        """Get verdict based on score"""
        if score >= 90:
            return 'Excellent match'
        elif score >= 80:
            return 'Great match'
        elif score >= 70:
            return 'Good match'
        elif score >= 60:
            return 'Acceptable match'
        else:
            return 'Challenging match'
    
    def _get_score_color(self, score):
        """Get color code for score"""
        if score >= 90:
            return '#28a745'  # green
        elif score >= 80:
            return '#20c997'  # teal
        elif score >= 70:
            return '#0dcaf0'  # cyan
        elif score >= 60:
            return '#ffc107'  # yellow
        else:
            return '#dc3545'  # red
