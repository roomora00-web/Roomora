from django.urls import path
from django.http import HttpResponse
from properties.models import Property

def count_props(request):
    return HttpResponse(f"COUNT IS: {Property.objects.count()}")

urlpatterns = [path('debug-count/', count_props)]
