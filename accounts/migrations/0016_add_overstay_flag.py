# Generated migration for overstay flag

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_lifestyleprofile_privacy_meaning_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_unresolved_overstay',
            field=models.BooleanField(default=False, help_text='User has unresolved overstay on any booking'),
        ),
    ]
