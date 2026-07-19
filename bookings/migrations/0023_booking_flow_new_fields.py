# Generated migration for new booking flow fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0022_migrate_existing_data'),
        ('accounts', '0016_add_overstay_flag'),
    ]

    operations = [
        # Add new fields to Booking model
        migrations.AddField(
            model_name='booking',
            name='house_rules_acknowledged_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when house rules were acknowledged', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='occupancy_position',
            field=models.PositiveIntegerField(blank=True, help_text='Position in room (1=first occupant, 2=second, etc.)', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='is_first_occupant',
            field=models.BooleanField(default=False, help_text='Whether this is the first occupant in the room'),
        ),
        
        # Create HouseRulesAcknowledgment model
        migrations.CreateModel(
            name='HouseRulesAcknowledgment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, help_text='Session identifier for per-session acknowledgment', max_length=100)),
                ('acknowledged_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('property', models.ForeignKey(on_delete=models.CASCADE, related_name='house_rules_acknowledgments', to='properties.property')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='house_rules_acknowledgments', to='accounts.user')),
            ],
            options={
                'db_table': 'house_rules_acknowledgments',
                'verbose_name': 'House Rules Acknowledgment',
                'verbose_name_plural': 'House Rules Acknowledgments',
                'ordering': ['-acknowledged_at'],
                'indexes': [
                    models.Index(fields=['user', 'property', '-acknowledged_at'], name='idx_user_property_ack'),
                    models.Index(fields=['session_key', '-acknowledged_at'], name='idx_session_ack'),
                ],
            },
        ),
    ]
