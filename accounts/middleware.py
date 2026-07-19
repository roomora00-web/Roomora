
from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedRedirectionMiddleware:
    """
    Middleware to enforce role-based redirection.
    Ensures that Admin users cannot access standard user booking/app flows,
    and regular users cannot access Admin flows.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info.lower()
            
            # Auth pages protection
            if path in ['/login/', '/register/']:
                if request.user.user_type == 'ADMIN':
                    return redirect('bookings:admin-approval-dashboard')
                return redirect('accounts:dashboard')
                
            # Admin users cannot access non-admin app pages, except api and accounts
            if request.user.user_type == 'ADMIN' or request.user.is_staff:
                if not path.startswith('/admin/') and not path.startswith('/api/') and not path.startswith('/accounts/logout') and '/admin' not in path:
                    return redirect('bookings:admin-approval-dashboard')
                    
        return self.get_response(request)
