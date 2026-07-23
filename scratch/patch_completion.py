import re

path = '/home/gazy-johnson/Downloads/school/ROOMORA/accounts/models.py'
with open(path, 'r') as f:
    content = f.read()

old_func = """    def calculate_completion(self):
        \"\"\"Calculate profile completion percentage\"\"\"
        required_fields = []
        
        # Base fields for all users
        required_fields.extend([
            self.user.profile_picture if self.user.profile_picture else 'HAS_DEFAULT_AVATAR',
            self.bio,
            self.address,
            self.city,
        ])"""

new_func = """    def calculate_completion(self):
        \"\"\"Calculate profile completion percentage\"\"\"
        required_fields = []
        
        # Base fields for all users
        required_fields.extend([
            self.user.profile_picture if self.user.profile_picture else 'HAS_DEFAULT_AVATAR',
            self.user.phone_number,
            self.user.gender,
            self.user.date_of_birth,
            self.bio,
            self.address,
            self.city,
            self.emergency_contact_name,
            self.emergency_contact_phone,
            self.emergency_contact_relationship,
        ])"""

if old_func in content:
    content = content.replace(old_func, new_func)
    with open(path, 'w') as f:
        f.write(content)
    print("Patched calculate_completion successfully")
else:
    print("Could not find exact text to replace")

