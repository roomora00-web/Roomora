import re

with open('properties/models.py', 'r') as f:
    content = f.read()

# Add RoomImage class after Room class
room_image_class = """
class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='room_images/')
    image_type = models.CharField(max_length=20, choices=[
        ('BEDROOM', 'Bedroom/Interior'),
        ('WASHROOM', 'Washroom'),
        ('KITCHEN', 'Kitchen'),
        ('OTHER', 'Other')
    ], default='BEDROOM')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.room_number} - {self.get_image_type_display()}"
"""

# Find Room class end (it ends around line 735)
# class Room(models.Model):
# ...
#    updated_at = models.DateTimeField(auto_now=True)

content = re.sub(r'(class Room\(models\.Model\):.*?updated_at = models\.DateTimeField\(auto_now=True\)\n)', r'\1' + room_image_class + '\n', content, flags=re.DOTALL)

with open('properties/models.py', 'w') as f:
    f.write(content)

print("Added RoomImage model")
