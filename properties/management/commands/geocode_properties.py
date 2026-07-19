"""
Django management command to geocode properties that don't have coordinates.
"""
from django.core.management.base import BaseCommand
from properties.models import Property
from properties.map_utils import geocode_address, validate_coordinates


class Command(BaseCommand):
    help = 'Geocode properties that do not have latitude/longitude coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-geocode all properties, even those with existing coordinates',
        )
        parser.add_argument(
            '--property-id',
            type=int,
            help='Geocode a specific property by ID',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        property_id = options.get('property_id')

        if property_id:
            # Geocode a single property
            try:
                property = Property.objects.get(id=property_id)
                self.geocode_property(property, force)
            except Property.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Property with ID {property_id} does not exist')
                )
        else:
            # Geocode all properties
            if force:
                properties = Property.objects.all()
                self.stdout.write(f'Force geocoding all {properties.count()} properties...')
            else:
                properties = Property.objects.filter(latitude__isnull=True, longitude__isnull=True)
                self.stdout.write(f'Found {properties.count()} properties without coordinates...')

            success_count = 0
            failure_count = 0

            for property in properties:
                if self.geocode_property(property, force):
                    success_count += 1
                else:
                    failure_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Geocoding complete: {success_count} successful, {failure_count} failed'
                )
            )

    def geocode_property(self, property, force=False):
        """Geocode a single property."""
        if not force and property.latitude and property.longitude:
            self.stdout.write(f'Skipping {property.title} (already has coordinates)')
            return True

        self.stdout.write(f'Geocoding: {property.title} - {property.address}, {property.city}')
        
        coordinates = geocode_address(property.address, property.city, property.country)
        
        if coordinates:
            # Validate coordinates are within Ghana bounds
            if validate_coordinates(coordinates['lat'], coordinates['lng']):
                property.latitude = coordinates['lat']
                property.longitude = coordinates['lng']
                property.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Geocoded: {coordinates["lat"]}, {coordinates["lng"]}'
                    )
                )
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Coordinates outside Ghana bounds: {coordinates["lat"]}, {coordinates["lng"]}'
                    )
                )
                return False
        else:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Failed to geocode: {property.address}, {property.city}')
            )
            return False
