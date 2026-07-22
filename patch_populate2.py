with open("properties/management/commands/populate_ghana_properties.py", "r") as f:
    content = f.read()

content = content.replace("self.stdout.write('Clearing existing properties...')\\n        Property.objects.all().delete()\\n        self.create_amenities()", "self.stdout.write('Clearing existing properties...')\n        Property.objects.all().delete()\n        self.create_amenities()")

with open("properties/management/commands/populate_ghana_properties.py", "w") as f:
    f.write(content)
