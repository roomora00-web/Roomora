import os

VIEWS_FILE = '/home/gazy-johnson/Downloads/school/ROOMORA/accounts/views.py'

with open(VIEWS_FILE, 'r') as f:
    content = f.read()

# 1. Add imports
if 'from django.core.mail import EmailMultiAlternatives' not in content:
    content = content.replace(
        'from django.core.mail import send_mail',
        'from django.core.mail import send_mail, EmailMultiAlternatives\nfrom django.template.loader import render_to_string\nfrom django.utils.html import strip_tags'
    )

# 2. Add helper function at the top (after normalize_ghana_phone)
helper_func = """
def send_html_email(subject, template_name, context, recipient_email):
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [recipient_email])
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        pass
"""
if 'def send_html_email' not in content:
    content = content.replace(
        'def check_email_view(request, email):',
        helper_func + '\ndef check_email_view(request, email):'
    )

# 3. Replace resend verification send_mail
resend_old = """            # Send verification email with OTP
            try:
                send_mail(
                    'Verify your Roomora account',
                    f'Hi {user.first_name},\\n\\nYour verification code is: {otp}\\n\\nThis code expires in 24 hours.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                pass"""

resend_new = """            # Send verification email with OTP
            send_html_email(
                'Verify your Roomora account',
                'accounts/emails/verification.html',
                {'user': user, 'otp': otp},
                user.email
            )"""

content = content.replace(resend_old, resend_new)

# 4. Replace forgot password send_mail
forgot_old = """            # Send password reset email
            try:
                reset_url = f"http://{request.get_host()}/accounts/reset-password/{reset_token}/"
                send_mail(
                    'Reset your Roomora password',
                    f'Hi {user.first_name},\\n\\nClick the link below to reset your password:\\n\\n{reset_url}\\n\\nThis link expires in 1 hour.\\n\\nIf you didn\\'t request a password reset, you can ignore this email.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                pass"""

forgot_new = """            # Send password reset email
            reset_url = f"http://{request.get_host()}/accounts/reset-password/{reset_token}/"
            send_html_email(
                'Reset your Roomora password',
                'accounts/emails/reset_password.html',
                {'user': user, 'reset_url': reset_url},
                user.email
            )"""

content = content.replace(forgot_old, forgot_new)

# 5. Replace registration send_mail
register_old = """            # Send verification email
            try:
                send_mail(
                    'Verify your Roomora account',
                    f'Hi {user.first_name},\\n\\nYour verification code is: {otp}\\n\\nThis code expires in 24 hours.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                pass"""

register_new = """            # Send verification email
            send_html_email(
                'Verify your Roomora account',
                'accounts/emails/verification.html',
                {'user': user, 'otp': otp},
                user.email
            )"""

content = content.replace(register_old, register_new)

with open(VIEWS_FILE, 'w') as f:
    f.write(content)

print("Email logic updated successfully in accounts/views.py!")
