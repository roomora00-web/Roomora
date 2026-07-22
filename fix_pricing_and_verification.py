import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from properties.models import Property, RoomType, UnitType, RoomTypePricing, UnitTypePricing

properties = Property.objects.all()

for prop in properties:
    # Update verification status
    prop.is_verified = True
    prop.save(update_fields=['is_verified'])

    if prop.property_type in ['HOSTEL', 'STUDENT_APARTMENT']:
        for rt in prop.room_types.all():
            if not rt.pricing_models.exists():
                RoomTypePricing.objects.create(
                    room_type=rt,
                    payment_type='SEMESTER',
                    semester_price=Decimal('2500.00'),
                    monthly_price=Decimal('600.00'),
                    yearly_price=Decimal('5000.00'),
                    currency='GHS'
                )
    else:
        for ut in prop.unit_types.all():
            if not ut.pricing_models.exists():
                UnitTypePricing.objects.create(
                    unit_type=ut,
                    payment_type='MONTHLY',
                    monthly_price=Decimal('4500.00'),
                    yearly_price=Decimal('50000.00'),
                    semester_price=Decimal('25000.00'),
                    currency='GHS'
                )

print("Updated verification status and pricing for all properties.")
