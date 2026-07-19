from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookingViewSet, PaymentViewSet, RoommateMatchViewSet,
    BookingRequestViewSet, LeaseAgreementViewSet, BookingHistoryViewSet,
    UserConsentView, RoommateConsentView, AdminApprovalDashboardView, AdminBookingDetailView,
    RoommateDashboardView, ReinstateBookingView, RoomSetupDeclarationView, RoomDiscussionView,
    ReportDeclarationView, AdminConflictDashboardView,
)
from .views_roommate import RoommateProfileViewSet

from .views_web import (
    my_bookings_view, booking_detail_view, consent_modal_view,
    accept_consent_view, cancel_booking_view,
    submit_visit_request, report_conflict_view, vacation_reserve_update_view,
)

from .dashboard_views import (
    student_booking_status_cards, grace_period_card, overstay_card, booking_actions
)

from .admin_views import (
    room_occupancy_calendar, vacation_reserve_management, overstay_management,
    admin_booking_queue, admin_assign_room, admin_finalize_booking,
)

from .views_new_booking import (
    initiate_booking, acknowledge_house_rules, booking_initiated,
    save_and_continue_later, resume_booking,
    duration_selection, submit_duration, semester_structure_selection,
    submit_semester_structure, vacation_date_declaration, submit_vacation_date,
    duration_summary, confirm_duration, lifestyle_check, use_existing_lifestyle,
    lifestyle_questionnaire, submit_lifestyle_screen, lifestyle_submit,
        booking_route, compatibility_engine, accept_match, booking_confirmation, submit_booking,
        download_receipt,
    save_lifestyle_progress, load_lifestyle_progress,
    compatibility_result, accept_consent, reject_consent, booking_reinstatement,
    reinstate_booking, permanent_cancel, no_match_found,
)

app_name = 'bookings'

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'roommate-matches', RoommateMatchViewSet, basename='roommatematch')
router.register(r'booking-requests', BookingRequestViewSet, basename='bookingrequest')
router.register(r'lease-agreements', LeaseAgreementViewSet, basename='leaseagreement')
router.register(r'booking-history', BookingHistoryViewSet, basename='bookinghistory')
router.register(r'roommates', RoommateProfileViewSet, basename='roommate-profile')

urlpatterns = [
    # API Routes
    path('', include(router.urls)),

    # Web Routes
    path('visit/request/', submit_visit_request, name='submit-visit-request'),
    path('my-bookings/', my_bookings_view, name='my-bookings'),
    path('booking/<int:booking_id>/', booking_detail_view, name='booking-detail'),
    path('booking/<int:booking_id>/consent/', consent_modal_view, name='consent-modal'),
    path('booking/<int:booking_id>/matching/', consent_modal_view, name='matching-alias'),
    path('booking/<int:booking_id>/accept-consent/', accept_consent_view, name='accept-consent'),
    path('booking/<int:booking_id>/cancel/', cancel_booking_view, name='cancel-booking'),
    path('booking/<int:booking_id>/reinstate/', ReinstateBookingView.as_view(), name='reinstate-booking'),
    path('booking/<int:booking_id>/setup-declaration/', RoomSetupDeclarationView.as_view(), name='setup-declaration'),
    path('booking/<int:booking_id>/room-discussion/', RoomDiscussionView.as_view(), name='room-discussion'),
    path('declaration/<int:declaration_id>/report/', ReportDeclarationView.as_view(), name='report-declaration'),
    path('assignment/<int:assignment_id>/report/', report_conflict_view, name='report-conflict'),

    path('booking/<int:booking_id>/user-consent/', UserConsentView.as_view(), name='user-consent'),
    path('booking/<int:booking_id>/roommate-consent/', RoommateConsentView.as_view(), name='roommate-consent'),
    path('booking/<int:booking_id>/roommate-dashboard/', RoommateDashboardView.as_view(), name='roommate-dashboard'),

    # Admin Routes
    path('admin/approval-dashboard/', AdminApprovalDashboardView.as_view(), name='admin-approval-dashboard'),
    path('admin/booking/<int:booking_id>/', AdminBookingDetailView.as_view(), name='admin-booking-detail'),
    path('admin/conflicts/', AdminConflictDashboardView.as_view(), name='admin-conflict-dashboard'),
    
    # Part 8: Admin Review and Finalization Routes
    path('admin/queue/', admin_booking_queue, name='admin_booking_queue'),
    path('admin/assign-room/<int:booking_id>/', admin_assign_room, name='admin_assign_room'),
    path('admin/finalize/<int:booking_id>/', admin_finalize_booking, name='admin_finalize_booking'),
    
    # Admin Room Status Management Routes
    path('admin/room-occupancy-calendar/', room_occupancy_calendar, name='room_occupancy_calendar'),
    path('admin/vacation-reserve/<int:booking_id>/', vacation_reserve_management, name='vacation_reserve_management'),
    path('admin/overstay/<int:booking_id>/', overstay_management, name='overstay_management'),

    # Dashboard Routes
    path('dashboard/status-cards/', student_booking_status_cards, name='dashboard-status-cards'),
    path('dashboard/grace-period/<int:booking_id>/', grace_period_card, name='dashboard-grace-period'),
    path('dashboard/overstay/<int:booking_id>/', overstay_card, name='dashboard-overstay'),
    path('dashboard/vacation-reserve/<int:booking_id>/update/', vacation_reserve_update_view, name='vacation-reserve-update'),
    path('booking/<int:booking_id>/actions/', booking_actions, name='booking-actions'),

    # New Booking Flow Routes
    path('initiate/<int:property_id>/', initiate_booking, name='initiate_booking'),
    path('acknowledge-house-rules/', acknowledge_house_rules, name='acknowledge_house_rules'),
    path('booking-initiated/<int:booking_id>/', booking_initiated, name='booking_initiated'),
    path('booking/<int:booking_id>/save-and-continue/', save_and_continue_later, name='save_and_continue_later'),
    path('booking/<int:booking_id>/resume/', resume_booking, name='resume_booking'),
    
    # Duration Selection Routes (Part 3)
    path('booking/<int:booking_id>/duration/', duration_selection, name='duration_selection'),
    path('booking/<int:booking_id>/duration/submit/', submit_duration, name='submit_duration'),
    path('booking/<int:booking_id>/semester-structure/', semester_structure_selection, name='semester_structure_selection'),
    path('booking/<int:booking_id>/semester-structure/submit/', submit_semester_structure, name='submit_semester_structure'),
    path('booking/<int:booking_id>/vacation-date/', vacation_date_declaration, name='vacation_date_declaration'),
    path('booking/<int:booking_id>/vacation-date/submit/', submit_vacation_date, name='submit_vacation_date'),
    path('booking/<int:booking_id>/duration-summary/', duration_summary, name='duration_summary'),
    path('booking/<int:booking_id>/duration/confirm/', confirm_duration, name='confirm_duration'),
    
    # Lifestyle Preferences Routes (Part 4)
    path('booking/<int:booking_id>/lifestyle-check/', lifestyle_check, name='lifestyle_check'),
    path('booking/<int:booking_id>/lifestyle/use-existing/', use_existing_lifestyle, name='use_existing_lifestyle'),
    path('booking/<int:booking_id>/lifestyle/<int:screen>/', lifestyle_questionnaire, name='lifestyle_questionnaire'),
    path('booking/<int:booking_id>/lifestyle/<int:screen>/submit/', submit_lifestyle_screen, name='submit_lifestyle_screen'),
    path('booking/<int:booking_id>/lifestyle/submit/', lifestyle_submit, name='lifestyle_submit'),
    
    # Routing Engine Routes (Part 5)
    path('booking/<int:booking_id>/route/', booking_route, name='booking_route'),
    path('booking/<int:booking_id>/compatibility/', compatibility_engine, name='compatibility_engine'),
    path('booking/<int:booking_id>/accept-match/<int:match_booking_id>/', accept_match, name='accept_match'),
    path('booking/<int:booking_id>/receipt/', download_receipt, name='download_receipt'),
    path('booking/<int:booking_id>/confirmation/', booking_confirmation, name='booking_confirmation'),
    path('booking/<int:booking_id>/submit/', submit_booking, name='submit_booking'),
    
    # Progress Saving AJAX Endpoints
    path('booking/<int:booking_id>/lifestyle/save-progress/', save_lifestyle_progress, name='save_lifestyle_progress'),
    path('booking/<int:booking_id>/lifestyle/load-progress/', load_lifestyle_progress, name='load_lifestyle_progress'),
    
    # Part 7: Consent Workflow Routes
    path('booking/<int:booking_id>/compatibility-result/', compatibility_result, name='compatibility_result'),
    path('booking/<int:booking_id>/accept-consent/', accept_consent, name='accept_consent'),
    path('booking/<int:booking_id>/reject-consent/', reject_consent, name='reject_consent'),
    path('booking/<int:booking_id>/reinstatement/', booking_reinstatement, name='booking_reinstatement'),
    path('booking/<int:booking_id>/reinstate/', reinstate_booking, name='reinstate_booking'),
    path('booking/<int:booking_id>/permanent-cancel/', permanent_cancel, name='permanent_cancel'),
    path('booking/<int:booking_id>/no-match/', no_match_found, name='no_match_found'),
]
