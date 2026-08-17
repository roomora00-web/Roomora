import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from properties.models import RoomType
RoomType.objects.update(available_slots=10)
print('Reset all RoomType slots to 10!')
