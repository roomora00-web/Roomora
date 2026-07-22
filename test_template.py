import os
import django
from django.conf import settings
from django.template import Template, Context

settings.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates'}])
django.setup()

class A:
    def m(self):
        return ''
        
t = Template('{% if a.m %}Yes{% else %}No{% endif %}')
c = Context({'a': A()})
print('Result:', t.render(c))
