# notifications/twilio_service.py
import os
import logging
import random
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        self.admin_phone = os.environ.get('ADMIN_PHONE')
        self.client = None
        self.is_available = False
        
        # SMS message variations for natural language
        self._setup_message_variations()
        self._initialize_client()
    
    def _setup_message_variations(self):
        """Setup natural language variations for different SMS events"""
        self.message_variations = {
            'booking_created': [
                "Hi {name}! Thanks for booking {service} with Capitol City Contracting. We'll contact you within 24 hours to confirm your {date} appointment.",
                "Hello {name}! Your {service} booking is received. We'll confirm your {date} appointment soon. Thank you!",
                "Hey {name}! We got your {service} booking for {date}. Our team will reach out within 24 hours to confirm details.",
                "Thanks {name}! Your {service} project is booked for {date}. We'll contact you shortly to finalize everything."
            ],
            'booking_confirmed': [
                "Great news {name}! Your {service} is confirmed for {date} at {time}. See you then!",
                "Confirmed! Your {service} is scheduled for {date} at {time}. We're excited to work with you!",
                "Hello {name}! Your {service} appointment is confirmed for {date} at {time}. Looking forward to it!",
                "All set {name}! Your {service} is booked for {date} at {time}. We'll see you there!"
            ],
            'booking_cancelled': [
                "Hi {name}. Your {service} booking for {date} has been cancelled as requested.",
                "Hello {name}. We've cancelled your {service} appointment for {date}. Hope to serve you another time!",
                "Hi {name}. Your {service} booking on {date} is now cancelled. Let us know if you need to reschedule!",
                "Cancellation confirmed {name}. Your {service} for {date} has been cancelled."
            ],
            'booking_completed': [
                "Hi {name}! Your {service} project is complete! Thanks for choosing Capitol City Contracting.",
                "Project complete! Your {service} is finished. Thank you for trusting us with your project!",
                "Hello {name}! We've successfully completed your {service}. Hope you love the results!",
                "All done {name}! Your {service} project is finished. Thank you for your business!"
            ]
        }
    
    def _initialize_client(self):
        """Initialize Twilio client with proper validation"""
        try:
            from twilio.rest import Client
            self.twilio_module_available = True
        except ImportError:
            logger.warning("Twilio Python library not installed.")
            self.twilio_module_available = False
            return
        
        # Check if credentials are configured
        if not all([self.account_sid, self.auth_token, self.twilio_phone]):
            logger.warning("Twilio credentials not fully configured in environment variables.")
            self._log_missing_credentials()
            return
        
        # Check for placeholder values
        placeholder_indicators = ['your_account_sid', 'your_auth_token', 'your_twilio_phone', 'your_admin_phone', 'example']
        if any(any(indicator in str(cred) for indicator in placeholder_indicators) 
               for cred in [self.account_sid, self.auth_token, self.twilio_phone, self.admin_phone]):
            logger.warning("Twilio credentials contain placeholder values.")
            self._log_credential_status()
            return
        
        try:
            # Test authentication by creating client
            self.client = Client(self.account_sid, self.auth_token)
            
            # Make a test API call to verify credentials
            test_account = self.client.api.accounts(self.account_sid).fetch()
            logger.info(f"Twilio authenticated successfully for account: {test_account.friendly_name}")
            self.is_available = True
            
        except Exception as e:
            logger.error(f"Twilio authentication failed: {str(e)}")
            self._handle_auth_error(e)
    
    def _log_missing_credentials(self):
        """Log which credentials are missing"""
        missing = []
        if not self.account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.twilio_phone:
            missing.append("TWILIO_PHONE_NUMBER")
        
        logger.warning(f"Missing Twilio credentials: {', '.join(missing)}")
    
    def _log_credential_status(self):
        """Log the status of each credential"""
        def check_placeholder(value):
            if not value:
                return "✗ Not set"
            placeholders = ['your_account_sid', 'your_auth_token', 'your_twilio_phone', 'your_admin_phone', 'example']
            if any(placeholder in value for placeholder in placeholders):
                return "✗ Using placeholder"
            return "✓ Configured"
        
        credentials_status = {
            "TWILIO_ACCOUNT_SID": check_placeholder(self.account_sid),
            "TWILIO_AUTH_TOKEN": "✓ Set" if self.auth_token and 'your_' not in self.auth_token else "✗ Using placeholder", 
            "TWILIO_PHONE_NUMBER": check_placeholder(self.twilio_phone),
            "ADMIN_PHONE": check_placeholder(self.admin_phone) if self.admin_phone else "✗ Not set"
        }
        
        logger.info("Twilio Credential Status:")
        for cred, status in credentials_status.items():
            value_preview = self.account_sid[:10] + '...' if cred == 'TWILIO_ACCOUNT_SID' and self.account_sid else 'Not set'
            if cred == 'TWILIO_AUTH_TOKEN' and self.auth_token:
                value_preview = '***' + self.auth_token[-4:] if len(self.auth_token) > 4 else '***'
            elif cred == 'TWILIO_PHONE_NUMBER' and self.twilio_phone:
                value_preview = self.twilio_phone
            elif cred == 'ADMIN_PHONE' and self.admin_phone:
                value_preview = self.admin_phone
            else:
                value_preview = 'Not set'
                
            logger.info(f"  {cred}: {status} | Value: {value_preview}")
    
    def _handle_auth_error(self, error):
        """Handle specific Twilio authentication errors"""
        error_str = str(error)
        
        if 'Authentication Error' in error_str or '20003' in error_str:
            logger.error("Twilio Authentication Error - Invalid Account SID or Auth Token")
            logger.error("Please verify your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
            logger.error("Make sure you're using the exact values from Twilio console")
        elif 'not found' in error_str:
            logger.error("Twilio Account Not Found - Invalid Account SID")
        elif 'permission' in error_str.lower():
            logger.error("Twilio Permission Error - Check account permissions")
        else:
            logger.error(f"Twilio Error: {error_str}")
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Ensure phone number has proper E.164 format"""
        if not phone_number:
            return phone_number
        
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # If no country code, assume US/Canada (+1)
        if not cleaned.startswith('+'):
            if len(cleaned) == 10:  # US/Canada number without country code
                cleaned = '+1' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = '+' + cleaned
            else:
                logger.warning(f"Phone number may not be in E.164 format: {phone_number}")
        
        return cleaned
    
    def _get_message_variation(self, event_type: str, **kwargs) -> str:
        """Get a random message variation for the event type"""
        variations = self.message_variations.get(event_type, [])
        if variations:
            chosen = random.choice(variations)
            return chosen.format(**kwargs)
        return f"Booking {event_type.replace('_', ' ')}: {kwargs.get('service', 'Service')}"
    
    def send_sms(self, message_body: str, to_phone: str) -> Dict[str, Any]:
        """
        Send SMS message via Twilio
        
        Args:
            message_body: The SMS message content
            to_phone: Recipient phone number
        
        Returns:
            Dict with success status and message/details
        """
        if not self.is_available or not self.client:
            return {
                'success': False,
                'error': 'Twilio service not available',
                'details': 'Credentials not configured or authentication failed'
            }
        
        try:
            formatted_phone = self._format_phone_number(to_phone)
            
            if not formatted_phone:
                return {
                    'success': False,
                    'error': 'Invalid recipient phone number'
                }
            
            logger.info(f"Sending SMS to {formatted_phone}: {message_body}")
            
            # Send the message
            message = self.client.messages.create(
                body=message_body,
                from_=self._format_phone_number(self.twilio_phone),
                to=formatted_phone
            )
            
            logger.info(f"SMS sent successfully: {message.sid}")
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': formatted_phone,
                'from': self.twilio_phone
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'details': 'Check Twilio credentials and phone number formatting'
            }
    
    def send_booking_sms(self, booking, service, event_type: str) -> Dict[str, Any]:
        """
        Send booking notification SMS to customer
        
        Args:
            booking: Booking object
            service: Service object  
            event_type: booking_created, booking_confirmed, booking_cancelled, booking_completed
        """
        # Get customer's first name
        customer_first_name = booking.customer_name.split()[0] if booking.customer_name else booking.customer_name
        
        # Generate message with variation
        message_body = self._get_message_variation(
            event_type,
            name=customer_first_name,
            service=service.name,
            date=booking.preferred_date,
            time=booking.preferred_time
        )
        
        # Send to customer's phone
        return self.send_sms(message_body, booking.customer_phone)
    
    def send_admin_alert(self, booking, service, event_type: str) -> Dict[str, Any]:
        """Send internal admin alert SMS"""
        if not self.admin_phone:
            return {'success': False, 'error': 'Admin phone not configured'}
        
        message_body = f"ADMIN: {event_type.replace('_', ' ').title()} - {booking.customer_name} - {service.name} on {booking.preferred_date}"
        return self.send_sms(message_body, self.admin_phone)
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Twilio account information for debugging"""
        if not self.is_available or not self.client:
            return {'error': 'Twilio not available'}
        
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            return {
                'friendly_name': account.friendly_name,
                'status': account.status,
                'type': account.type,
                'created': account.date_created.isoformat() if account.date_created else None
            }
        except Exception as e:
            return {'error': f'Failed to get account info: {str(e)}'}
    
    def validate_credentials(self) -> Dict[str, Any]:
        """Validate Twilio credentials and return detailed status"""
        status = {
            'twilio_module_installed': self.twilio_module_available,
            'credentials_configured': all([self.account_sid, self.auth_token, self.twilio_phone]),
            'using_placeholders': any(any(indicator in str(cred) for indicator in ['your_account_sid', 'your_auth_token', 'your_twilio_phone', 'your_admin_phone', 'example']) 
                                    for cred in [self.account_sid, self.auth_token, self.twilio_phone, self.admin_phone]),
            'authentication_successful': self.is_available,
            'account_sid_preview': self.account_sid[:10] + '...' if self.account_sid and len(self.account_sid) > 10 else self.account_sid,
            'auth_token_set': bool(self.auth_token),
            'twilio_phone': self.twilio_phone,
            'admin_phone': self.admin_phone
        }

        return status