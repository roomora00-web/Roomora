"""
URL configuration for staymatch project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse

def healthcheck(request):
    return JsonResponse({'status': 'healthy'})

def debug_home(request):
    """Debug endpoint to test home page rendering"""
    try:
        from django.test import RequestFactory
        from landing.views import HomeView
        factory = RequestFactory()
        test_request = factory.get('/')
        test_request.user = request.user
        view = HomeView.as_view()
        response = view(test_request)
        # Render the response if it's a TemplateResponse
        if hasattr(response, 'render'):
            response.render()
        return JsonResponse({
            'status': 'success',
            'response_status': response.status_code,
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
            'content_preview': response.content[:500].decode('utf-8', errors='ignore') if hasattr(response, 'content') else 'no content'
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

urlpatterns = [
    path('health/', healthcheck),
    path('debug-home/', debug_home),
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/feedback/', include('feedback.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('profile/', lambda request: redirect('/accounts/profile/')),
]

from django.urls import re_path
from django.views.static import serve
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
