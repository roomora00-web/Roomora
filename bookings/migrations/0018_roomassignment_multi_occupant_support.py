# Generated migration for multi-occupant roommate support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_roommate_data(apps, schema_editor):
    """Migrate existing single roommate to ManyToMany field"""
    RoomAssignment = apps.get_model('bookings', 'RoomAssignment')
    
    for assignment in RoomAssignment.objects.all():
        if assignment.assigned_roommate:
            # Add the existing roommate to the new ManyToMany field
            assignment.assigned_roommates.add(assignment.assigned_roommate)


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0017_roommessage_is_system_alter_roommessage_sender'),
    ]

    operations = [
        # Step 1: Add the new ManyToMany field (keep it nullable initially)
        migrations.AddField(
            model_name='roomassignment',
            name='assigned_roommates',
            field=models.ManyToManyField(blank=True, related_name='roommate_assignments', to=settings.AUTH_USER_MODEL),
        ),
        
        # Step 2: Migrate existing data from assigned_roommate to assigned_roommates
        migrations.RunPython(
            code=migrate_roommate_data,
            reverse_code=migrations.RunPython.noop
        ),
        
        # Step 3: Remove the old ForeignKey field
        migrations.RemoveField(
            model_name='roomassignment',
            name='assigned_roommate',
        ),
    ]
