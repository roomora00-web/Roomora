with open('staymatch/urls.py', 'r') as f:
    content = f.read()

import re
# Remove the broken static(MEDIA_URL) line
content = re.sub(r'urlpatterns \+= static\(settings\.MEDIA_URL, document_root=settings\.MEDIA_ROOT\)\n', '', content)

# Add the proper re_path for media
new_media_url = """from django.urls import re_path
from django.views.static import serve
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
"""
content = content.replace("if settings.DEBUG:", new_media_url + "if settings.DEBUG:")

with open('staymatch/urls.py', 'w') as f:
    f.write(content)
