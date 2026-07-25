import logging

logger = logging.getLogger(__name__)

class NoCacheSecurityMiddleware:
    """
    Security Middleware to:
    1. Invalidate browser cache on authenticated pages, login, and logout so pressing 
       the browser 'Back' button after logging out forces a fresh request and redirects to login.
    2. Add standard HTTP security headers to responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Enforce Cache-Control on authenticated users or auth-sensitive pages
        if hasattr(request, 'user') and request.user.is_authenticated or request.path.startswith('/accounts/') or request.path.startswith('/bookings/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        # Security Headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
