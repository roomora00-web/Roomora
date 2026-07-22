with open("properties/models.py", "r") as f:
    content = f.read()

# I will move the Meta class back to Room
old_chunk = """class RoomImage(models.Model):
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


    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        unique_together = ['accommodation_property', 'room_number']

    def __str__(self):
        return f"{self.accommodation_property.title} - Room {self.room_number}"
"""

new_chunk = """
    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        unique_together = ['accommodation_property', 'room_number']

    def __str__(self):
        return f"{self.accommodation_property.title} - Room {self.room_number}"

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

# Wait, Room already has:
#    created_at = models.DateTimeField(auto_now_add=True)
#    updated_at = models.DateTimeField(auto_now=True)

# So we can just replace.
content = content.replace(old_chunk, new_chunk)
with open("properties/models.py", "w") as f:
    f.write(content)
print("Done!")
