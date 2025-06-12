"""
backend/services/email_service.py
Email notification service for pet activity alerts - FIXED VERSION.
"""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import threading
from dataclasses import dataclass


@dataclass
class EmailConfig:
    """Email configuration settings."""
    sender_email: str
    sender_password: str
    recipient_email: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    enabled: bool = True
    notification_types: dict = None
    cooldown_period: int = 300  # seconds
    
    def __post_init__(self):
        """Initialize notification_types if not provided."""
        if self.notification_types is None:
            self.notification_types = {
                "restricted_zone": True,
                "feeding": False,
                "long_absence": True,
                "unusual_activity": False
            }


class EmailNotificationService:
    """Handles email notifications for pet activity alerts."""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config
        self.enabled = config is not None
        self.last_alert_times: Dict[str, float] = {}
        self.cooldown_period = 300  # 5 minutes default cooldown
        
    def configure(self, config: EmailConfig):
        """Configure email settings."""
        self.config = config
        self.enabled = config.enabled
        if hasattr(config, 'cooldown_period'):
            self.cooldown_period = config.cooldown_period
    
    def set_cooldown_period(self, seconds: int):
        """Set the cooldown period between similar alerts."""
        self.cooldown_period = max(30, seconds)  # Minimum 30 seconds
    
    def send_alert(self, alert_type: str, subject: str, message: str, 
                   bypass_cooldown: bool = False) -> bool:
        """
        Send an email alert.
        
        Args:
            alert_type: Type of alert for cooldown tracking
            subject: Email subject
            message: Email message body
            bypass_cooldown: Whether to bypass cooldown period
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled or not self.config:
            return False
        
        # Check cooldown period
        if not bypass_cooldown and self._is_in_cooldown(alert_type):
            return False
        
        # Send email in background thread
        thread = threading.Thread(
            target=self._send_email_async,
            args=(subject, message, alert_type),
            daemon=True
        )
        thread.start()
        
        return True
    
    def _is_in_cooldown(self, alert_type: str) -> bool:
        """Check if alert type is in cooldown period."""
        current_time = time.time()
        last_time = self.last_alert_times.get(alert_type, 0)
        return (current_time - last_time) < self.cooldown_period
    
    def _send_email_async(self, subject: str, message: str, alert_type: str):
        """Send email asynchronously."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = self.config.recipient_email
            msg['Subject'] = subject
            
            # Add timestamp to message
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"Alert Time: {timestamp}\n\n{message}"
            
            msg.attach(MIMEText(full_message, 'plain'))
            
            # Send email with detailed error handling
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            # Update last alert time
            self.last_alert_times[alert_type] = time.time()
            print(f"✓ Email alert sent: {subject}")
            
        except Exception as e:
            print(f"✗ Failed to send email alert: {e}")
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test email connection and credentials.
        
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if not self.config:
            return False, "No email configuration provided"
        
        try:
            # Test SMTP connection with timeout
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
            return True, "Connection successful"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {e}"
        except smtplib.SMTPConnectError as e:
            return False, f"Connection failed: {e}"
        except smtplib.SMTPServerDisconnected as e:
            return False, f"Server disconnected: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def send_test_email(self) -> tuple[bool, str]:
        """
        Send a test email to verify configuration.
        
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if not self.enabled or not self.config:
            return False, "Email service not configured or disabled"
        
        try:
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = self.config.recipient_email
            msg['Subject'] = "Pet Activity Tracker - Test Email"
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            test_message = f"Test Time: {timestamp}\n\nThis is a test email from the Pet Activity Tracker. If you receive this, email notifications are working correctly!"
            
            msg.attach(MIMEText(test_message, 'plain'))
            
            # Send email with detailed error handling and timeout
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            # Update last alert time for test
            self.last_alert_times["test"] = time.time()
            return True, "Test email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Authentication failed: Check your email and password. For Gmail, use an App Password."
            print(f"✗ {error_msg}")
            return False, error_msg
        except smtplib.SMTPConnectError as e:
            error_msg = f"Connection failed: Cannot connect to {self.config.smtp_server}:{self.config.smtp_port}"
            print(f"✗ {error_msg}")
            return False, error_msg
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"Server disconnected: {e}"
            print(f"✗ {error_msg}")
            return False, error_msg
        except ConnectionRefusedError as e:
            error_msg = f"Connection refused: Check SMTP server and port settings"
            print(f"✗ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"✗ {error_msg}")
            return False, error_msg
    
    def send_restricted_zone_alert(self, pet_type: str, zone_name: str) -> bool:
        """Send alert for restricted zone entry."""
        subject = f"Pet Alert: Restricted Zone Entry"
        message = f"A {pet_type} has entered the restricted zone '{zone_name}'. Please check the area."
        
        return self.send_alert("restricted_zone", subject, message)
    
    def send_feeding_alert(self, pet_type: str, activity: str) -> bool:
        """Send alert for feeding activities."""
        subject = f"Pet Alert: Feeding Activity"
        message = f"A {pet_type} is {activity}. This might be of interest."
        
        return self.send_alert("feeding", subject, message)
    
    def send_long_absence_alert(self, duration_hours: float) -> bool:
        """Send alert for long absence of pet activity."""
        subject = f"Pet Alert: Long Absence Detected"
        message = f"No pet activity has been detected for {duration_hours:.1f} hours. Please check on your pet."
        
        return self.send_alert("absence", subject, message)
    
    def send_unusual_activity_alert(self, description: str) -> bool:
        """Send alert for unusual activity patterns."""
        subject = f"Pet Alert: Unusual Activity"
        message = f"Unusual activity pattern detected: {description}"
        
        return self.send_alert("unusual", subject, message)
    
    def get_status(self) -> Dict:
        """Get email service status."""
        return {
            'enabled': self.enabled,
            'configured': self.config is not None,
            'smtp_server': self.config.smtp_server if self.config else None,
            'recipient': self.config.recipient_email if self.config else None,
            'cooldown_period': self.cooldown_period,
            'recent_alerts': len(self.last_alert_times)
        }
    
    def clear_cooldowns(self):
        """Clear all cooldown timers."""
        self.last_alert_times.clear()
    
    def disable(self):
        """Disable email notifications."""
        self.enabled = False
    
    def enable(self):
        """Enable email notifications (if configured)."""
        if self.config:
            self.enabled = True