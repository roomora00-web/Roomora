from django.contrib import admin
from django.shortcuts import redirect
from .models import Booking, AdminBookingQueue

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'accommodation_property', 'room_type', 'status', 'created_at')
    list_filter = ('status', 'payment_status', 'booking_type', 'is_first_occupant')
    search_fields = ('tenant__email', 'tenant__first_name', 'tenant__last_name', 'accommodation_property__title')
    readonly_fields = ('created_at', 'updated_at')
    
    change_list_template = "admin/bookings/booking_changelist.html"

@admin.register(AdminBookingQueue)
class AdminBookingQueueAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('bookings:admin_booking_queue')
