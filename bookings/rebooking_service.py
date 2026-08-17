"""
Rebooking and Continuity Service

Handles rebooking and continuity options as per Part 11.
Students can rebook during grace period with priority.
"""

from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from .constants import BillingModel, SEMESTER_DAYS, DAYS_PER_MONTH, DAYS_PER_YEAR
from .billing_service import BillingService
from .grace_period_service import GracePeriodService


class RebookingService:
    """Service for rebooking and continuity management"""
    
    @staticmethod
    def check_rebooking_eligibility(booking, current_date=None):
        """
        Check if student is eligible for priority rebooking
        
        Returns:
            dict with eligibility status and available options
        """
        if current_date is None:
            current_date = date.today()
        
        # Check grace period eligibility
        grace_eligibility = GracePeriodService.check_rebooking_eligibility(booking, current_date)
        
        if not grace_eligibility['eligible']:
            return {
                'eligible': False,
                'reason': grace_eligibility['reason'],
                'options': []
            }
        
        # Get available rebooking options based on billing model
        options = RebookingService._get_rebooking_options(booking)
        
        return {
            'eligible': True,
            'reason': 'In grace period and room available',
            'days_remaining': grace_eligibility['days_remaining'],
            'slot_available_date': grace_eligibility['slot_available_date'],
            'options': options
        }
    
    @staticmethod
    def _get_rebooking_options(booking):
        """
        Get available rebooking options based on current booking's billing model
        
        Returns:
            list of rebooking options
        """
        billing_model = booking.billing_model
        room_type = booking.room_type
        unit_type = booking.unit_type
        
        if not room_type and not unit_type:
            return []
        
        # Get pricing configuration
        if room_type:
            pricing = room_type.pricing_models.filter(
                payment_type__icontains=billing_model.lower()
            ).first()
        else:
            pricing = unit_type.pricing_models.filter(
                payment_type__icontains=billing_model.lower()
            ).first()
        
        if not pricing:
            return []
        
        options = []
        
        if billing_model == BillingModel.SEMESTER_BASED.value:
            # Offer 1-3 semesters
            for num_semesters in range(1, pricing.max_semesters + 1):
                semester_price = pricing.semester_price or Decimal('0')
                total_price = semester_price * num_semesters
                
                # Calculate new move-out date
                new_move_in = booking.move_out_date + timedelta(days=1)
                new_move_out = new_move_in + timedelta(days=num_semesters * SEMESTER_DAYS)
                
                options.append({
                    'type': 'SEMESTER',
                    'num_semesters': num_semesters,
                    'price': total_price,
                    'move_in_date': new_move_in,
                    'move_out_date': new_move_out,
                    'description': f'{num_semesters} semester(s) - {total_price}'
                })
        
        elif billing_model == BillingModel.MONTHLY_BASED.value:
            # Offer monthly extensions
            for num_months in range(pricing.min_months, pricing.max_months + 1):
                monthly_price = pricing.monthly_price or Decimal('0')
                total_price = monthly_price * num_months
                
                new_move_in = booking.move_out_date + timedelta(days=1)
                new_move_out = new_move_in + timedelta(days=num_months * DAYS_PER_MONTH)
                
                options.append({
                    'type': 'MONTHLY',
                    'num_months': num_months,
                    'price': total_price,
                    'move_in_date': new_move_in,
                    'move_out_date': new_move_out,
                    'description': f'{num_months} month(s) - {total_price}'
                })
        
        elif billing_model == BillingModel.ANNUAL_BASED.value:
            # Offer 1 or 2 years
            yearly_price = pricing.yearly_price or Decimal('0')
            
            # 1 year option
            new_move_in = booking.move_out_date + timedelta(days=1)
            new_move_out = new_move_in + timedelta(days=DAYS_PER_YEAR)
            
            options.append({
                'type': 'ANNUAL',
                'num_years': 1,
                'price': yearly_price,
                'move_in_date': new_move_in,
                'move_out_date': new_move_out,
                'description': f'1 year - {yearly_price}'
            })
            
            # 2 year option if available
            if pricing.allow_two_year_advance:
                two_years_price = pricing.two_years_price or (yearly_price * 2)
                new_move_out_2yr = new_move_in + timedelta(days=DAYS_PER_YEAR * 2)
                
                options.append({
                    'type': 'ANNUAL',
                    'num_years': 2,
                    'price': two_years_price,
                    'move_in_date': new_move_in,
                    'move_out_date': new_move_out_2yr,
                    'description': f'2 years - {two_years_price}'
                })
        
        elif billing_model == BillingModel.ACADEMIC_YEAR.value:
            # Academic year rebooking
            academic_year_price = pricing.academic_year_price
            semester_price = pricing.semester_price or Decimal('0')
            
            if academic_year_price:
                total_price = academic_year_price
            else:
                total_price = semester_price * 2 * Decimal('0.9')
            
            new_move_in = booking.move_out_date + timedelta(days=1)
            new_move_out = new_move_in + timedelta(days=SEMESTER_DAYS * 2)
            
            options.append({
                'type': 'ACADEMIC_YEAR',
                'num_semesters': 2,
                'price': total_price,
                'move_in_date': new_move_in,
                'move_out_date': new_move_out,
                'description': f'Academic Year (2 semesters) - {total_price}'
            })
        
        return options
    
    @staticmethod
    def create_continuity_booking(booking, selected_option, requested_by=None):
        """
        Create a continuity booking (priority rebooking during grace period)
        
        Args:
            booking: The existing booking
            selected_option: The selected rebooking option
            requested_by: User requesting the rebooking
        
        Returns:
            dict with new booking information
        """
        from .models import Booking
        
        # Check eligibility
        eligibility = RebookingService.check_rebooking_eligibility(booking)
        
        if not eligibility['eligible']:
            raise ValidationError(eligibility['reason'])
        
        # Create new booking
        new_booking = Booking.objects.create(
            tenant=booking.tenant,
            accommodation_property=booking.accommodation_property,
            room_type=booking.room_type,
            unit_type=booking.unit_type,
            booking_type='DIRECT',
            status='INITIATED',
            payment_status='PENDING',
            billing_model=booking.billing_model,
            move_in_date=selected_option['move_in_date'],
            move_out_date=selected_option['move_out_date'],
            monthly_rent=booking.monthly_rent,
            security_deposit=booking.security_deposit,
            total_amount=selected_option['price'],
            amount_paid=Decimal('0')
        )
        
        # Set duration fields based on option type
        if selected_option['type'] == 'SEMESTER':
            new_booking.num_semesters = selected_option['num_semesters']
        elif selected_option['type'] == 'MONTHLY':
            new_booking.num_months = selected_option['num_months']
        elif selected_option['type'] == 'ANNUAL':
            new_booking.num_years = selected_option['num_years']
        elif selected_option['type'] == 'ACADEMIC_YEAR':
            new_booking.num_semesters = 2
        
        new_booking.save()
        
        # Log booking history
        from .models import BookingHistory
        BookingHistory.objects.create(
            booking=new_booking,
            action='CREATED',
            description=f'Continuity booking created from previous booking {booking.id}',
            performed_by=requested_by or booking.tenant
        )
        
        return {
            'success': True,
            'new_booking_id': new_booking.id,
            'move_in_date': new_booking.move_in_date,
            'move_out_date': new_booking.move_out_date,
            'total_amount': new_booking.total_amount,
            'continuity': True
        }
    
    @staticmethod
    def confirm_departure(booking, confirmed_by=None):
        """
        Confirm student departure (end of stay)
        
        Args:
            booking: The booking to confirm departure for
            confirmed_by: User confirming departure
        
        Returns:
            dict with departure confirmation
        """
        # Update booking status
        booking.status = 'COMPLETED'
        booking.room_status = 'AVAILABLE'
        booking.save()
        
        # Release room slot
        if booking.room_type:
            booking.room_type.occupied_slots = max(0, booking.room_type.occupied_slots - 1)
            booking.room_type.available_slots += 1
            booking.room_type.save()
        elif booking.unit_type:
            booking.unit_type.occupied_units = max(0, booking.unit_type.occupied_units - 1)
            booking.unit_type.available_units += 1
            booking.unit_type.save()
        
        # Log booking history
        from .models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            action='DEPARTURE_CONFIRMED',
            description='Student confirmed departure',
            performed_by=confirmed_by or booking.tenant
        )
        
        return {
            'success': True,
            'booking_id': booking.id,
            'departure_confirmed': True,
            'room_released': True
        }
    
    @staticmethod
    def request_monthly_extension(booking, additional_months, requested_by=None):
        """
        Request monthly extension for Monthly-Based booking
        
        Args:
            booking: The booking to extend
            additional_months: Number of months to add
            requested_by: User requesting extension
        
        Returns:
            dict with extension information
        """
        from .billing_service import BillingService
        
        if booking.billing_model != BillingModel.MONTHLY_BASED.value:
            raise ValidationError("Only Monthly-Based bookings can be extended")
        
        # Check if extensions are allowed
        if booking.room_type:
            pricing = booking.room_type.pricing_models.filter(
                payment_type='MONTHLY'
            ).first()
            if not pricing or not pricing.allow_monthly_extensions:
                raise ValidationError("Monthly extensions are not available for this room type")
        else:
            raise ValidationError("Room type not found")
        
        # Calculate new move-out date
        new_move_out_date = BillingService.extend_monthly_booking(booking, additional_months)
        
        # Calculate additional cost
        monthly_price = pricing.monthly_extension_rate or pricing.monthly_price
        additional_cost = monthly_price * additional_months
        
        # Update total amount
        booking.total_amount += additional_cost
        booking.save()
        
        # Log booking history
        from .models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            action='EXTENDED',
            description=f'Extended by {additional_months} months. Additional cost: {additional_cost}',
            performed_by=requested_by or booking.tenant
        )
        
        return {
            'success': True,
            'additional_months': additional_months,
            'new_move_out_date': new_move_out_date,
            'additional_cost': additional_cost,
            'new_total_amount': booking.total_amount
        }
