from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking

class Command(BaseCommand):
    help = 'Releases expired soft-locks for incomplete bookings.'

    def handle(self, *args, **options):
        self.stdout.write("Checking for expired soft-locks...")
        now = timezone.now()
        
        # Find bookings that have a soft lock which has expired,
        # and are still in the SUBMITTED state (i.e. abandoned)
        expired_bookings = Booking.objects.filter(
            status='SUBMITTED',
            soft_lock_expires_at__lt=now
        )
        
        count = expired_bookings.count()
        
        if count > 0:
            self.stdout.write(f"Found {count} abandoned bookings. Releasing locks...")
            for booking in expired_bookings:
                booking.release_soft_lock()
                booking.set_status('CANCELLED', note='System automatically cancelled booking due to soft-lock expiration (abandoned checkout).')
                self.stdout.write(f"  - Released booking ID {booking.id} ({booking.reference_number})")
                
        # Phase 12: Handle Temporarily Cancelled 24h expiration
        expired_temp_cancellations = Booking.objects.filter(
            status='TEMPORARILY_CANCELLED',
            temp_cancel_expires_at__lt=now
        )
        
        temp_count = expired_temp_cancellations.count()
        if temp_count > 0:
            self.stdout.write(f"Found {temp_count} expired temporarily cancelled bookings. Releasing slots...")
            
            from accounts.models import User, Notification
            # Get an admin user to send notifications to
            admin_users = User.objects.filter(user_type='ADMIN')
            
            for booking in expired_temp_cancellations:
                # The 6h soft lock already expired earlier, but if it didn't, we release it
                booking.release_soft_lock()
                
                # Permanently cancel
                booking.status = 'CANCELLED'
                booking.cancellation_reason = '24-hour temporary cancellation window expired without reinstatement.'
                booking.save()
                
                # Notify Admins (Phase 12)
                for admin in admin_users:
                    Notification.objects.create(
                        user=admin,
                        title='Slot Released (24h Window Expired)',
                        message=f"Booking {booking.reference_number} for {booking.tenant.email} has been permanently cancelled as their 24h reinstatement window expired. The room slot has been released back into the pool.",
                    )
                
                self.stdout.write(f"  - Permanently cancelled booking ID {booking.id}")
                
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} abandoned checkouts and {temp_count} expired temporary cancellations.'))
