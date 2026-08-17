from django.urls import path
from .views import (
    PaystackWebhookView,
    InitiatePaymentView,
    PaymentStatusView,
    InitializeGatewayTransactionView,
    BankTransferClaimView,
    AdminVerifyTransferView,
    AdminInitiateRefundView,
    AdminDisburseView,
    PaymentReceiptView
)
from . import template_views

app_name = 'payments'

urlpatterns = [
    # Webhook endpoint (no authentication required)
    path('webhook/paystack/', PaystackWebhookView.as_view(), name='paystack_webhook'),
    
    # User payment endpoints
    path('initiate/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('<uuid:payment_id>/status/', PaymentStatusView.as_view(), name='payment_status'),
    path('<uuid:payment_id>/initialize/', InitializeGatewayTransactionView.as_view(), name='initialize_gateway'),
    path('<uuid:payment_id>/bank-transfer-claim/', BankTransferClaimView.as_view(), name='bank_transfer_claim'),
    path('<uuid:payment_id>/receipt/', PaymentReceiptView.as_view(), name='payment_receipt'),
    
    # Admin endpoints
    path('admin/<uuid:payment_id>/verify-transfer/', AdminVerifyTransferView.as_view(), name='admin_verify_transfer'),
    path('admin/<uuid:payment_id>/refund/', AdminInitiateRefundView.as_view(), name='admin_refund'),
    path('admin/<uuid:payment_id>/disburse/', AdminDisburseView.as_view(), name='admin_disburse'),
    
    # UI template views
    path('<uuid:payment_id>/payment/', template_views.payment_screen_view, name='payment_screen'),
    path('<uuid:payment_id>/confirmation/', template_views.payment_confirmation_view, name='payment_confirmation'),
    path('<uuid:payment_id>/bank-transfer/', template_views.bank_transfer_view, name='bank_transfer'),
    path('<uuid:payment_id>/failed/', template_views.payment_failed_view, name='payment_failed'),
    path('<uuid:payment_id>/official-receipt/', template_views.official_receipt_view, name='official_receipt'),
]
