"""
Alert handling utilities
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import requests
import json

from app.models.schemas import Alert
from app.config import settings

logger = logging.getLogger(__name__)


class AlertHandler:
    """Handles different types of alert notifications"""
    
    def __init__(self):
        self.smtp_server = None
    
    async def send_alert(self, alert: Alert):
        """Send alert through all configured channels"""
        try:
            # Send email if configured
            if settings.email_enabled:
                await self.send_email_alert(alert)
            
            # Send webhook if configured
            if settings.webhook_url:
                await self.send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def send_email_alert(self, alert: Alert):
        """Send alert via email"""
        try:
            if not all([settings.smtp_server, settings.smtp_username, settings.smtp_password]):
                logger.warning("Email not configured properly")
                return
            
            msg = MIMEMultipart()
            msg['From'] = settings.smtp_username
            msg['To'] = settings.smtp_username  # Send to self for now
            msg['Subject'] = f"VisionFlux Alert: {alert.alert_type.value}"
            
            body = f"""
            Alert Details:
            - Camera: {alert.camera_id}
            - Type: {alert.alert_type.value}
            - Message: {alert.message}
            - Confidence: {alert.confidence:.2%}
            - Timestamp: {alert.timestamp}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            text = msg.as_string()
            server.sendmail(settings.smtp_username, settings.smtp_username, text)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def send_webhook_alert(self, alert: Alert):
        """Send alert via webhook"""
        try:
            payload = {
                "alert_id": alert.id,
                "camera_id": alert.camera_id,
                "alert_type": alert.alert_type.value,
                "message": alert.message,
                "confidence": alert.confidence,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            response = requests.post(
                settings.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook alert sent for {alert.id}")
            else:
                logger.warning(f"Webhook returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
