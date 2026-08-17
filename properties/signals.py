from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RoomType, UnitType, Room

@receiver(post_save, sender=RoomType)
def auto_create_rooms_for_room_type(sender, instance, created, **kwargs):
    """Automatically generate physical Room instances for a new RoomType."""
    if created:
        for i in range(instance.total_rooms):
            Room.objects.create(
                accommodation_property=instance.accommodation_property,
                room_type=instance,
                room_number=f"{instance.room_type_name[:3].upper()}-{i+1}",
                total_slots=instance.beds_per_room,
                status='AVAILABLE'
            )
    else:
        # If total_rooms is updated to be larger, we could add rooms,
        # but for simplicity, we only auto-generate on creation right now.
        pass

@receiver(post_save, sender=UnitType)
def auto_create_units_for_unit_type(sender, instance, created, **kwargs):
    """Automatically generate physical Room (Unit) instances for a new UnitType."""
    if created:
        for i in range(instance.number_of_units):
            # If it's a shared apartment, slots = capacity. Else 1 slot (the whole unit)
            slots = instance.bedrooms if instance.shared_apartment_allowed else 1
            Room.objects.create(
                accommodation_property=instance.accommodation_property,
                unit_type=instance,
                room_number=f"UNIT-{instance.unit_name[:3].upper()}-{i+1}",
                total_slots=slots,
                status='AVAILABLE'
            )
