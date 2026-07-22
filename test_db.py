import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staymatch.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cursor.fetchall()
    print([t[0] for t in tables if 'prop' in t[0] or 'room' in t[0]])
