import django, os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()

from accounts.models import User
from django.db import connection, transaction

users = list(User.objects.filter(is_superuser=False))
print(f"Found {len(users)} non-admin users to delete.")

for u in users:
    try:
        # Re-establish connection just in case it dropped
        connection.ensure_connection()
        print(f"Deleting user: {u.email}...")
        u.delete()
        print(f"  -> Deleted {u.email}")
    except Exception as e:
        print(f"  -> Failed to delete {u.email}: {e}")
        time.sleep(1)

print("Done.")
