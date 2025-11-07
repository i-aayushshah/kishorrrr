from flask import url_for
from flask_mail import Message
from config import Config

def send_verification_email(mail, user, code):
    """Send email verification code to user"""
    subject = "Verify your Unmask.AI account"
    body = f"""
Hello {user.first_name},

Welcome to Unmask.AI! Please verify your email address by entering the following code:

Verification Code: {code}

This code will expire in 15 minutes.

If you didn't create an account with Unmask.AI, please ignore this email.

Best regards,
The Unmask.AI Team
"""
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body,
        sender=Config.MAIL_DEFAULT_SENDER
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_password_reset_email(mail, user, code):
    """Send password reset code to user"""
    subject = "Reset your Unmask.AI password"
    body = f"""
Hello {user.first_name},

You requested to reset your password for your Unmask.AI account.

Reset Code: {code}

This code will expire in 15 minutes.

If you didn't request a password reset, please ignore this email and your password will remain unchanged.

Best regards,
The Unmask.AI Team
"""
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body,
        sender=Config.MAIL_DEFAULT_SENDER
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False

