# notifications/email_service.py
import os
import smtplib
import random
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("MAIL_USERNAME")
        self.sender_password = os.getenv("MAIL_PASSWORD")
        self.sender_name = os.getenv("MAIL_SENDER_NAME", "Capitol City Contracting")

        # Set up template environment
        template_dir = os.path.join(os.path.dirname(__file__), '../templates/emails')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Email variations for natural language
        self._setup_variations()

    def _setup_variations(self):
        """Setup natural language variations for different email events"""
        self.variations = {
            'greetings': [
                "Hi {name},",
                "Hello {name},",
                "Dear {name},",
                "Good day {name},"
            ],
            'booking_created_intro': [
                "Thanks for choosing Capitol City Contracting!",
                "We're thrilled to help with your next project!",
                "Your request has been received and is in progress.",
                "Thank you for trusting us with your project!"
            ],
            'booking_confirmed_intro': [
                "Great news! Your booking has been confirmed.",
                "We're excited to confirm your upcoming project!",
                "Your booking is now confirmed and scheduled.",
                "Everything is set for your project!"
            ],
            'booking_cancelled_intro': [
                "We've processed your cancellation request.",
                "Your booking cancellation has been confirmed.",
                "We've cancelled your booking as requested.",
                "Your cancellation has been processed."
            ],
            'booking_completed_intro': [
                "Your project has been successfully completed!",
                "We're happy to announce your project is finished!",
                "Your construction project is now complete!",
                "The work on your project has been finished!"
            ],
            'closings': [
                "Best regards,",
                "Sincerely,",
                "Thank you,",
                "Warm regards,",
                "Respectfully,"
            ]
        }

    def _get_subject_variation(self, event_type, service_name):
        """Generate varied subject lines based on event type"""
        subjects = {
            'booking_created': [
                f"Capitol City - {service_name} Booking Received",
                f"Your {service_name} Project Request",
                f"Booking Confirmation - {service_name}",
                f"Thank You for Your {service_name} Booking"
            ],
            'booking_confirmed': [
                f"Booking Confirmed - {service_name}",
                f"Your {service_name} Project is Scheduled",
                f"Project Scheduled - {service_name}",
                f"Ready to Start Your {service_name} Project"
            ],
            'booking_cancelled': [
                f"Booking Cancelled - {service_name}",
                f"Cancellation Confirmation - {service_name}",
                f"{service_name} Booking Cancelled",
                f"Booking Update - Cancellation"
            ],
            'booking_completed': [
                f"Project Complete - {service_name}",
                f"Your {service_name} Project is Finished!",
                f"Work Completed - {service_name}",
                f"Project Successfully Delivered - {service_name}"
            ]
        }
        return random.choice(subjects.get(event_type, [f"Booking {event_type.replace('_', ' ').title()}"]))

    def _get_random_variation(self, variation_type, **kwargs):
        """Get a random variation for the given type"""
        variations = self.variations.get(variation_type, [])
        if variations:
            chosen = random.choice(variations)
            return chosen.format(**kwargs) if kwargs else chosen
        return ""

    def send_booking_email(self, booking, service, event_type):
        """
        Send email notification for booking events
        
        Args:
            booking: Booking model instance
            service: Service model instance  
            event_type: One of 'booking_created', 'booking_confirmed', 
                       'booking_cancelled', 'booking_completed'
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured. Email skipped.")
            return False

        try:
            # Load appropriate template
            template_name = f"{event_type}.html"
            template = self.env.get_template(template_name)
            
            # Prepare dynamic content with variations
            context = {
                'booking': booking,
                'service': service,
                'greeting': self._get_random_variation('greetings', name=booking.customer_name.split()[0]),
                'intro_message': self._get_random_variation(f'{event_type}_intro'),
                'closing': self._get_random_variation('closings'),
                'sender_name': self.sender_name,
                'sender_email': self.sender_email,
                'current_year': datetime.now().year,
                'customer_first_name': booking.customer_name.split()[0] if booking.customer_name else booking.customer_name
            }
            
            # Generate HTML body
            html_body = template.render(**context)
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_subject_variation(event_type, service.name)
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = booking.customer_email
            
            # Attach HTML content
            message.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"{event_type.replace('_', ' ').title()} email sent to {booking.customer_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send {event_type} email to {booking.customer_email}: {str(e)}")
            return False

    def send_admin_notification(self, booking, service, event_type):
        """Send internal admin notifications for important events"""
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            return False
            
        try:
            subject = f"ADMIN: Booking {event_type.replace('_', ' ').title()} - {service.name}"
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = admin_email
            
            html_content = f"""
            <html>
                <body>
                    <h3>Booking {event_type.replace('_', ' ').title()}</h3>
                    <p><strong>Customer:</strong> {booking.customer_name}</p>
                    <p><strong>Email:</strong> {booking.customer_email}</p>
                    <p><strong>Phone:</strong> {booking.customer_phone}</p>
                    <p><strong>Service:</strong> {service.name}</p>
                    <p><strong>Date:</strong> {booking.preferred_date} at {booking.preferred_time}</p>
                    <p><strong>Project:</strong> {booking.project_description}</p>
                    <p><strong>Address:</strong> {booking.address}</p>
                    <p><strong>Status:</strong> {booking.status}</p>
                </body>
            </html>
            """
            
            message.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            logger.info(f"Admin notification sent for {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")
            return False