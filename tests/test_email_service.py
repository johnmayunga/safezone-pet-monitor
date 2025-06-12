"""
Unit tests for email notification service.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import smtplib
from email.mime.multipart import MIMEMultipart

from backend.services.email_service import EmailNotificationService, EmailConfig


class TestEmailConfig(unittest.TestCase):
    """Test EmailConfig dataclass."""
    
    def test_email_config_creation(self):
        """Test creating EmailConfig with required fields."""
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="password123",
            recipient_email="recipient@example.com"
        )
        
        self.assertEqual(config.sender_email, "test@example.com")
        self.assertEqual(config.sender_password, "password123")
        self.assertEqual(config.recipient_email, "recipient@example.com")
        self.assertEqual(config.smtp_server, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.enabled)
        self.assertIsNotNone(config.notification_types)
    
    def test_email_config_with_custom_settings(self):
        """Test EmailConfig with custom SMTP settings."""
        config = EmailConfig(
            sender_email="test@outlook.com",
            sender_password="password123",
            recipient_email="recipient@outlook.com",
            smtp_server="smtp.outlook.com",
            smtp_port=587,
            enabled=False,
            cooldown_period=600
        )
        
        self.assertEqual(config.smtp_server, "smtp.outlook.com")
        self.assertFalse(config.enabled)
        self.assertEqual(config.cooldown_period, 600)
    
    def test_notification_types_default(self):
        """Test default notification types."""
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="password123",
            recipient_email="recipient@example.com"
        )
        
        expected_types = {
            "restricted_zone": True,
            "feeding": False,
            "long_absence": True,
            "unusual_activity": False
        }
        
        self.assertEqual(config.notification_types, expected_types)


class TestEmailNotificationService(unittest.TestCase):
    """Test EmailNotificationService functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.email_service = EmailNotificationService()
        self.test_config = EmailConfig(
            sender_email="test@example.com",
            sender_password="testpassword",
            recipient_email="recipient@example.com",
            smtp_server="smtp.gmail.com",
            smtp_port=587
        )
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNone(self.email_service.config)
        self.assertFalse(self.email_service.enabled)
        self.assertEqual(self.email_service.cooldown_period, 300)
        self.assertEqual(len(self.email_service.last_alert_times), 0)
    
    def test_configure_service(self):
        """Test configuring the email service."""
        self.email_service.configure(self.test_config)
        
        self.assertEqual(self.email_service.config, self.test_config)
        self.assertTrue(self.email_service.enabled)
    
    def test_configure_service_with_disabled_config(self):
        """Test configuring with disabled email."""
        disabled_config = EmailConfig(
            sender_email="test@example.com",
            sender_password="testpassword",
            recipient_email="recipient@example.com",
            enabled=False
        )
        
        self.email_service.configure(disabled_config)
        
        self.assertEqual(self.email_service.config, disabled_config)
        self.assertFalse(self.email_service.enabled)
    
    def test_set_cooldown_period(self):
        """Test setting cooldown period."""
        self.email_service.set_cooldown_period(600)
        self.assertEqual(self.email_service.cooldown_period, 600)
        
        # Test minimum cooldown
        self.email_service.set_cooldown_period(10)
        self.assertEqual(self.email_service.cooldown_period, 30)  # Should be clamped to 30
    
    def test_cooldown_checking(self):
        """Test alert cooldown functionality."""
        self.email_service.configure(self.test_config)
        self.email_service.set_cooldown_period(60)
        
        # First alert should not be in cooldown
        self.assertFalse(self.email_service._is_in_cooldown("test_alert"))
        
        # Simulate sending an alert
        self.email_service.last_alert_times["test_alert"] = time.time()
        
        # Immediate subsequent alert should be in cooldown
        self.assertTrue(self.email_service._is_in_cooldown("test_alert"))
        
        # Simulate time passing
        self.email_service.last_alert_times["test_alert"] = time.time() - 70
        self.assertFalse(self.email_service._is_in_cooldown("test_alert"))
    
    @patch('backend.services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Configure mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        self.email_service.configure(self.test_config)
        
        # Send alert
        result = self.email_service.send_alert(
            "test_alert",
            "Test Subject",
            "Test message content"
        )
        
        self.assertTrue(result)
        
        # Verify SMTP calls
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "testpassword")
        mock_server.send_message.assert_called_once()
    
    @patch('backend.services.email_service.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure."""
        # Configure mock to raise exception
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
        
        self.email_service.configure(self.test_config)
        
        # Send alert should fail gracefully
        result = self.email_service.send_alert(
            "test_alert",
            "Test Subject",
            "Test message content"
        )
        
        self.assertTrue(result)  # Should still return True (sent to background thread)
    
    def test_send_alert_without_config(self):
        """Test sending alert without configuration."""
        result = self.email_service.send_alert(
            "test_alert",
            "Test Subject",
            "Test message content"
        )
        
        self.assertFalse(result)
    
    def test_send_alert_with_cooldown(self):
        """Test sending alert during cooldown period."""
        self.email_service.configure(self.test_config)
        self.email_service.set_cooldown_period(60)
        
        # Send first alert
        result1 = self.email_service.send_alert(
            "test_alert",
            "Test Subject",
            "Test message content"
        )
        self.assertTrue(result1)
        
        # Simulate that the alert was "sent" by setting the time
        self.email_service.last_alert_times["test_alert"] = time.time()
        
        # Try to send same alert type immediately
        result2 = self.email_service.send_alert(
            "test_alert",
            "Test Subject 2",
            "Test message content 2"
        )
        self.assertFalse(result2)  # Should be blocked by cooldown
    
    def test_bypass_cooldown(self):
        """Test bypassing cooldown period."""
        self.email_service.configure(self.test_config)
        self.email_service.last_alert_times["test_alert"] = time.time()
        
        # Should bypass cooldown
        result = self.email_service.send_alert(
            "test_alert",
            "Test Subject",
            "Test message content",
            bypass_cooldown=True
        )
        
        self.assertTrue(result)
    
    @patch('backend.services.email_service.smtplib.SMTP')
    def test_connection_test(self, mock_smtp):
        """Test email connection testing."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        self.email_service.configure(self.test_config)
        
        result = self.email_service.test_connection()
        
        self.assertTrue(result)
        # Fix: Include timeout parameter in assertion
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "testpassword")

    @patch('backend.services.email_service.smtplib.SMTP')
    def test_connection_test_failure(self, mock_smtp):
        """Test email connection test failure."""
        mock_smtp.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        
        self.email_service.configure(self.test_config)
        
        result = self.email_service.test_connection()
        
        # Fix: Check for tuple return value
        self.assertFalse(result[0] if isinstance(result, tuple) else result)

    
    def test_specific_alert_methods(self):
        """Test specific alert type methods."""
        self.email_service.configure(self.test_config)
        
        # Test each specific alert method
        with patch.object(self.email_service, 'send_alert') as mock_send:
            self.email_service.send_restricted_zone_alert("cat", "kitchen")
            mock_send.assert_called_with(
                "restricted_zone",
                "Pet Alert: Restricted Zone Entry",
                "A cat has entered the restricted zone 'kitchen'. Please check the area."
            )
            
            self.email_service.send_feeding_alert("dog", "eating")
            mock_send.assert_called_with(
                "feeding",
                "Pet Alert: Feeding Activity",
                "A dog is eating. This might be of interest."
            )
            
            self.email_service.send_long_absence_alert(2.5)
            mock_send.assert_called_with(
                "absence",
                "Pet Alert: Long Absence Detected",
                "No pet activity has been detected for 2.5 hours. Please check on your pet."
            )
            
            self.email_service.send_unusual_activity_alert("Excessive movement at night")
            mock_send.assert_called_with(
                "unusual",
                "Pet Alert: Unusual Activity",
                "Unusual activity pattern detected: Excessive movement at night"
            )
    
    def test_get_status(self):
        """Test service status reporting."""
        # Test unconfigured status
        status = self.email_service.get_status()
        expected = {
            'enabled': False,
            'configured': False,
            'smtp_server': None,
            'recipient': None,
            'cooldown_period': 300,
            'recent_alerts': 0
        }
        self.assertEqual(status, expected)
        
        # Test configured status
        self.email_service.configure(self.test_config)
        self.email_service.last_alert_times["test"] = time.time()
        
        status = self.email_service.get_status()
        self.assertTrue(status['enabled'])
        self.assertTrue(status['configured'])
        self.assertEqual(status['smtp_server'], "smtp.gmail.com")
        self.assertEqual(status['recipient'], "recipient@example.com")
        self.assertEqual(status['recent_alerts'], 1)
    
    def test_clear_cooldowns(self):
        """Test clearing cooldown timers."""
        self.email_service.last_alert_times = {
            "alert1": time.time(),
            "alert2": time.time() - 100
        }
        
        self.email_service.clear_cooldowns()
        
        self.assertEqual(len(self.email_service.last_alert_times), 0)
    
    def test_enable_disable(self):
        """Test enabling and disabling the service."""
        self.email_service.configure(self.test_config)
        self.assertTrue(self.email_service.enabled)
        
        self.email_service.disable()
        self.assertFalse(self.email_service.enabled)
        
        self.email_service.enable()
        self.assertTrue(self.email_service.enabled)
    
    def test_enable_without_config(self):
        """Test enabling service without configuration."""
        self.email_service.enable()
        self.assertFalse(self.email_service.enabled)  # Should remain disabled


class TestEmailServiceIntegration(unittest.TestCase):
    """Integration tests for email service."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.email_service = EmailNotificationService()
    
    def test_complete_workflow(self):
        """Test complete email service workflow."""
        # 1. Start with unconfigured service
        self.assertFalse(self.email_service.enabled)
        
        # 2. Configure service
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="testpassword",
            recipient_email="recipient@example.com"
        )
        self.email_service.configure(config)
        self.assertTrue(self.email_service.enabled)
        
        # 3. Test cooldown behavior
        with patch.object(self.email_service, '_send_email_async'):
            # First alert should work
            result1 = self.email_service.send_alert("test", "Subject", "Message")
            self.assertTrue(result1)
            
            # Set up cooldown
            self.email_service.last_alert_times["test"] = time.time()
            
            # Second alert should be blocked
            result2 = self.email_service.send_alert("test", "Subject", "Message")
            self.assertFalse(result2)
            
            # Different alert type should work
            result3 = self.email_service.send_alert("other", "Subject", "Message")
            self.assertTrue(result3)
        
        # 4. Test service status
        status = self.email_service.get_status()
        self.assertTrue(status['enabled'])
        self.assertTrue(status['configured'])


if __name__ == '__main__':
    unittest.main()