import logging
from django.core.mail import send_mail
from django.core.mail import BadHeaderError
from django.conf import settings
import smtplib
import socket

logger = logging.getLogger(__name__)


class EmailService:
    """
    Wraps Django's send_mail with explicit error handling.
    Returns a result dict so the dispatcher can write a consistent
    NotificationLog entry regardless of channel.
    """

    def send(self, notification) -> dict:
        """
        Attempt to send an email for the given Notification instance.
        Always returns:
            {
                'success': bool,
                'response': str,   # human-readable outcome
                'error': str|None  # exception message if failed
            }
        """
        try:
            sent = send_mail(
                subject      = notification.title,
                message      = notification.message,          # plain text fallback
                html_message = self._build_html(notification),
                from_email   = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [self._resolve_recipient(notification)],
                fail_silently = False,  # we want exceptions — we'll catch them ourselves
            )

            if sent == 1:
                logger.info(f"Email sent successfully | notification={notification.id}")
                return {
                    'success': True,
                    'response': f"Email delivered to {self._resolve_recipient(notification)}",
                    'error': None,
                }
            else:
                # send_mail returns 0 if no recipients accepted — shouldn't happen but guard it
                return {
                    'success': False,
                    'response': None,
                    'error': 'SMTP accepted connection but reported 0 messages sent.',
                }

        except BadHeaderError:
            # Injection attack protection — Django raises this if subject contains newlines
            msg = "Invalid email header detected. Possible header injection attempt."
            logger.error(f"{msg} | notification={notification.id}")
            return {'success': False, 'response': None, 'error': msg}

        except smtplib.SMTPAuthenticationError:
            msg = "SMTP authentication failed. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD."
            logger.error(f"{msg} | notification={notification.id}")
            return {'success': False, 'response': None, 'error': msg}

        except smtplib.SMTPRecipientsRefused as e:
            msg = f"Recipient refused by SMTP server: {e.recipients}"
            logger.error(f"{msg} | notification={notification.id}")
            return {'success': False, 'response': None, 'error': msg}

        except smtplib.SMTPException as e:
            msg = f"SMTP error: {str(e)}"
            logger.error(f"{msg} | notification={notification.id}")
            return {'success': False, 'response': None, 'error': msg}

        except socket.gaierror:
            # DNS lookup failure — usually means EMAIL_HOST is wrong or no internet
            msg = "Network error: could not reach SMTP host. Check EMAIL_HOST setting."
            logger.error(f"{msg} | notification={notification.id}")
            return {'success': False, 'response': None, 'error': msg}

        except Exception as e:
            msg = f"Unexpected error during email send: {str(e)}"
            logger.exception(f"{msg} | notification={notification.id}")
            return {'success': False, 'response': None, 'error': msg}

    def _resolve_recipient(self, notification) -> str:
        """
        In a real system, you'd look up the user's email address from
        an identity service or a passed-in metadata field.
        For now, we use user_id directly if it looks like an email,
        or fall back to a placeholder so development doesn't break.
        """
        uid = notification.user_id
        if '@' in uid:
            return uid
        # TODO Phase 9: resolve via Tixora/Scott user lookup
        logger.warning(
            f"user_id '{uid}' is not an email address. "
            f"Using placeholder. Implement identity resolution in Phase 9."
        )
        return f"{uid}@placeholder.notiflow.dev"

    def _build_html(self, notification) -> str:
        """
        Minimal branded HTML email.
        Replace with a proper template engine (Django templates or mjml) in production.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #fff;
                          border-radius: 8px; overflow: hidden; }}
            .header {{ background: #1a1a2e; color: #fff; padding: 24px 32px; }}
            .header h1 {{ margin: 0; font-size: 22px; }}
            .header span {{ font-size: 12px; opacity: 0.6; }}
            .body {{ padding: 32px; color: #333; line-height: 1.6; }}
            .body h2 {{ margin-top: 0; color: #1a1a2e; }}
            .footer {{ background: #f4f4f4; padding: 16px 32px;
                       font-size: 11px; color: #999; text-align: center; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Notiflow</h1>
              <span>Unified Notifications Infrastructure</span>
            </div>
            <div class="body">
              <h2>{notification.title}</h2>
              <p>{notification.message}</p>
            </div>
            <div class="footer">
              Sent via Notiflow &mdash; {notification.app_id} &middot;
              Notification ID: {notification.id}
            </div>
          </div>
        </body>
        </html>
        """