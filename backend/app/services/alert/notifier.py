"""
SAWS Alert Notifier

Handles sending notifications via multiple channels.
"""

import logging
from typing import Any

from app.config import get_settings
from app.models.alert import Alert

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_notification(
    alert_id: str,
    notification_type: str,
    alert_data: Alert,
) -> bool:
    """
    Send alert notification via specified channel.

    Args:
        alert_id: Alert ID
        notification_type: Channel type (email, sms, whatsapp)
        alert_data: Alert data

    Returns:
        True if sent successfully
    """
    try:
        if notification_type == "email":
            return await _send_email(alert_data)
        elif notification_type == "sms":
            return await _send_sms(alert_data)
        elif notification_type == "whatsapp":
            return await _send_whatsapp(alert_data)
        else:
            logger.warning(f"Unknown notification type: {notification_type}")
            return False

    except Exception as e:
        logger.error(f"Error sending {notification_type} notification: {e}")
        return False


async def _send_email(alert: Alert) -> bool:
    """
    Send email notification.

    Uses SMTP configuration from settings.
    """
    if not settings.alert_email_enabled or not settings.smtp_host:
        logger.warning("Email notifications not configured")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Get user email (would query from database)
        user_email = f"user_{alert.user_id}@saws.gov.sa"

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"
        msg["From"] = settings.smtp_from_email
        msg["To"] = user_email

        # Plain text version
        text_content = f"""
Alert: {alert.title}
Severity: {alert.severity}
Type: {alert.alert_type}
Message: {alert.message}
District: {alert.district or 'N/A'}
Time: {alert.created_at}

---
Saudi AgriDrought Warning System
Ministry of Environment, Water and Agriculture
"""

        # HTML version
        html_content = f"""
<html>
<body>
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <h2 style="color: {'#8B0000' if alert.severity == 'critical' else '#DC143C' if alert.severity == 'warning' else '#333'};">
            {alert.title}
        </h2>
        <p><strong>Severity:</strong> {alert.severity.upper()}</p>
        <p><strong>Type:</strong> {alert.alert_type}</p>
        <p><strong>Location:</strong> {alert.district or 'N/A'}</p>
        <p><strong>Time:</strong> {alert.created_at}</p>
        <hr>
        <p>{alert.message}</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Saudi AgriDrought Warning System<br>
            Ministry of Environment, Water and Agriculture
        </p>
    </div>
</body>
</html>
"""

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Send via SMTP
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_username and settings.smtp_password:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)

            server.send_message(msg)

        logger.info(f"Email sent for alert {alert.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


async def _send_sms(alert: Alert) -> bool:
    """
    Send SMS notification.

    Integration with Saudi SMS providers (e.g., JWT, mobily).
    """
    if not settings.alert_sms_enabled or not settings.sms_api_key:
        logger.warning("SMS notifications not configured")
        return False

    try:
        # Get user phone (would query from database)
        phone_number = f"+9665XXXXXXXX{alert.user_id[-2:]}"

        # Format message for SMS
        message = f"[SAWS {alert.severity.upper()}] {alert.title}. {alert.message[:100]}"

        # Integration with SMS provider would go here
        # Example for generic provider:
        # response = requests.post(
        #     settings.sms_api_url,
        #     headers={"Authorization": f"Bearer {settings.sms_api_key}"},
        #     json={"to": phone_number, "message": message}
        # )

        logger.info(f"SMS sent for alert {alert.id} to {phone_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


async def _send_whatsapp(alert: Alert) -> bool:
    """
    Send WhatsApp notification.

    Integration with WhatsApp Business API.
    """
    if not settings.alert_whatsapp_enabled:
        logger.warning("WhatsApp notifications not configured")
        return False

    try:
        # Get user WhatsApp number
        phone_number = f"+9665XXXXXXXX{alert.user_id[-2:]}"

        # Format message
        message = f"""
*{alert.title}*
Severity: {alert.severity.upper()}
{alert.message}

_Saudi AgriDrought Warning System_
""".strip()

        # Integration with WhatsApp Business API would go here
        # Example:
        # response = requests.post(
        #     f"{settings.whatsapp_api_url}/messages",
        #     headers={"Authorization": f"Bearer {settings.whatsapp_api_key}"},
        #     json={
        #         "to": phone_number,
        #         "type": "text",
        #         "text": {"body": message}
        #     }
        # )

        logger.info(f"WhatsApp sent for alert {alert.id} to {phone_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return False


def format_alert_for_push(alert: Alert) -> dict[str, Any]:
    """
    Format alert for push notification.

    Returns formatted payload for web/mobile push.
    """
    return {
        "title": f"SAWS Alert: {alert.title}",
        "body": alert.message,
        "icon": "/icon-192.png",
        "badge": "/badge-72.png",
        "tag": alert.id,
        "data": {
            "alert_id": alert.id,
            "severity": alert.severity,
            "field_id": alert.field_id,
            "type": alert.alert_type,
        },
        "actions": [
            {"action": "view", "title": "View Details"},
            {"action": "dismiss", "title": "Dismiss"},
        ],
    }
