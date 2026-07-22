import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from properties.models import Property

for p in Property.objects.all()[:5]:
    print(f"Prop: {p.title}, Type: {p.property_type}")
    if p.property_type == 'HOSTEL':
        if p.room_types.exists():
            rt = p.room_types.first()
            if rt.pricing_models.exists():
                pm = rt.pricing_models.first()
                print(f"  HOSTEL pricing: {pm.semester_price}, {pm.monthly_price}")
            else:
                print("  HOSTEL pricing_models: 0")
        else:
            print("  HOSTEL room_types: 0")
    else:
        if p.unit_types.exists():
            ut = p.unit_types.first()
            if ut.pricing_models.exists():
                pm = ut.pricing_models.first()
                print(f"  APT pricing: {pm.monthly_price}, {pm.yearly_price}, {pm.semester_price}")
            else:
                print("  APT pricing_models: 0")
        else:
            print("  APT unit_types: 0")
