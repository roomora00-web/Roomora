from django import forms
from .models import Property, Amenity


class PropertySearchForm(forms.Form):
    """Property search form with advanced filters - Phase 3"""
    
    # Search query
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by area, institution, or property name'
        }),
        label='Search'
    )
    
    # Location filters
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='City'
    )
    
    nearest_institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nearest Institution'
    )
    
    distance_to_campus = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'range'}),
        label='Distance to Campus (km)'
    )
    
    # Property type filters
    property_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-group'}),
        choices=[
            ('HOSTEL', 'Hostel'),
            ('APARTMENT', 'Apartment'),
        ],
        label='Accommodation Type'
    )
    
    # Price range
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=50000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min'}),
        label='Minimum Price (GH₵)'
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=50000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max'}),
        label='Maximum Price (GH₵)'
    )
    
    rental_period = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'}),
        choices=[
            ('monthly', 'Per month'),
            ('semester', 'Per semester'),
            ('yearly', 'Per year'),
        ],
        label='Rental Period',
        initial='monthly'
    )
    
    # Room type filters (for hostels)
    occupancy_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-group'}),
        choices=[
            ('SINGLE', 'Single'),
            ('DOUBLE', 'Double'),
            ('TRIPLE', 'Triple'),
            ('QUAD', 'Quad'),
        ],
        label='Room Type'
    )
    
    # Unit type filters (for apartments)
    unit_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-group'}),
        choices=[
            ('STUDIO', 'Studio'),
            ('1_BEDROOM', '1 Bedroom'),
            ('2_BEDROOM', '2 Bedroom'),
            ('3_BEDROOM', '3 Bedroom'),
        ],
        label='Unit Type'
    )
    
    # Furnishing status (for apartments)
    furnished_status = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-group'}),
        choices=[
            ('FURNISHED', 'Furnished'),
            ('SEMI_FURNISHED', 'Semi-Furnished'),
            ('UNFURNISHED', 'Unfurnished'),
        ],
        label='Furnishing Status'
    )
    
    # Availability
    show_available_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Show only available properties',
        initial=True
    )
    
    minimum_available_slots = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'range'}),
        label='Minimum Available Slots'
    )
    
    # Target audience
    target_audience = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-group'}),
        choices=[
            ('students', 'Students'),
            ('workers', 'Workers'),
            ('families', 'Families'),
            ('couples', 'Couples'),
        ],
        label='Target Audience'
    )
    
    # Sort options
    sort_by = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=[
            ('relevance', 'Relevance'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('availability', 'Availability: Most Available First'),
            ('distance', 'Distance: Closest First'),
        ],
        label='Sort By',
        initial='relevance'
    )
