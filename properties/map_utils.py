"""
Map utilities for geocoding and location-related operations.
"""
import requests
from django.conf import settings
from typing import Optional, Tuple, Dict


def geocode_address(address: str, city: str, country: str = 'Ghana') -> Optional[Dict[str, float]]:
    """
    Geocode an address to get latitude and longitude coordinates.
    
    Args:
        address: The street address
        city: The city name
        country: The country name (default: Ghana)
    
    Returns:
        Dictionary with 'lat' and 'lng' keys, or None if geocoding fails
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        print("Warning: GOOGLE_MAPS_API_KEY not configured")
        return None
    
    # Build full address string
    full_address = f"{address}, {city}, {country}"
    
    # Google Maps Geocoding API
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': full_address,
        'key': settings.GOOGLE_MAPS_API_KEY,
        'region': 'GH'  # Bias results to Ghana
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            return {
                'lat': location['lat'],
                'lng': location['lng']
            }
        else:
            print(f"Geocoding failed for address: {full_address}. Status: {data['status']}")
            return None
            
    except requests.RequestException as e:
        print(f"Error geocoding address: {e}")
        return None


def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Reverse geocode coordinates to get an address.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Formatted address string, or None if reverse geocoding fails
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return None
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'latlng': f"{lat},{lng}",
        'key': settings.GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            return data['results'][0]['formatted_address']
        return None
            
    except requests.RequestException as e:
        print(f"Error reverse geocoding: {e}")
        return None


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate that coordinates are within Ghana's approximate bounds.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        True if coordinates are valid, False otherwise
    """
    # Ghana approximate bounds
    # Latitude: 4.7 to 11.1
    # Longitude: -3.3 to 1.2
    GHANA_BOUNDS = {
        'min_lat': 4.0,
        'max_lat': 12.0,
        'min_lng': -3.5,
        'max_lng': 1.5
    }
    
    return (GHANA_BOUNDS['min_lat'] <= lat <= GHANA_BOUNDS['max_lat'] and
            GHANA_BOUNDS['min_lng'] <= lng <= GHANA_BOUNDS['max_lng'])


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the distance between two coordinates using the Haversine formula.
    
    Args:
        lat1, lng1: First coordinate
        lat2, lng2: Second coordinate
    
    Returns:
        Distance in kilometers
    """
    import math
    
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r


def get_map_embed_url(lat: float, lng: float, zoom: int = 15) -> str:
    """
    Generate a Google Maps embed URL for a location.
    
    Args:
        lat: Latitude
        lng: Longitude
        zoom: Zoom level (default: 15)
    
    Returns:
        Embed URL string
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return ""
    
    return f"https://www.google.com/maps/embed/v1/view?key={settings.GOOGLE_MAPS_API_KEY}&center={lat},{lng}&zoom={zoom}"


def get_directions_url(destination_lat: float, destination_lng: float, 
                       origin_lat: float = None, origin_lng: float = None) -> str:
    """
    Generate a Google Maps directions URL.
    
    Args:
        destination_lat, destination_lng: Destination coordinates
        origin_lat, origin_lng: Optional origin coordinates (if not provided, uses current location)
    
    Returns:
        Directions URL string
    """
    base_url = "https://www.google.com/maps/dir/?api=1"
    
    if origin_lat and origin_lng:
        url = f"{base_url}&origin={origin_lat},{origin_lng}&destination={destination_lat},{destination_lng}"
    else:
        url = f"{base_url}&destination={destination_lat},{destination_lng}"
    
    return url
