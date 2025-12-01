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

        # UPDATED BRAND NAME
        self.sender_name = os.getenv("MAIL_SENDER_NAME", "SmartMove Transport")
        self.admin_email = os.getenv("ADMIN_EMAIL", "can2naija@gmail.com")

        # Template environment
        template_dir = os.path.join(os.path.dirname(__file__), '../templates/emails')
        self.env = Environment(loader=FileSystemLoader(template_dir))

        self._setup_variations()

    def _setup_variations(self):
        """SmartMove Transport email variations"""
        self.variations = {
            'greetings': [
                "Hi {name},",
                "Hello {name},",
                "Dear {name},",
                "Good day {name},"
            ],

            # BOOKING RECEIVED
            'booking_created_intro': [
                "Thanks for choosing SmartMove Transport!",
                "Your moving request has been received!",
                "We're excited to help you with your upcoming move.",
                "Thanks for trusting SmartMove Transport with your move!"
            ],

            # CONFIRMED
            'booking_confirmed_intro': [
                "Great news — your move is officially confirmed.",
                "Your moving date and time are now booked.",
                "Your SmartMove Transport booking is confirmed.",
                "Everything is set for your upcoming move!"
            ],

            # CANCELLED
            'booking_cancelled_intro': [
                "Your moving request has been cancelled.",
                "We've processed your cancellation as requested.",
                "Your SmartMove Transport booking has been cancelled.",
                "Your cancellation has been confirmed."
            ],

            # COMPLETED
            'booking_completed_intro': [
                "Your move has been successfully completed!",
                "We're happy to let you know your move is now finished!",
                "Your SmartMove Transport moving service is complete.",
                "Thank you for moving with SmartMove Transport!"
            ],

            'closings': [
                "Best regards,",
                "Thank you,",
                "Warm regards,",
                "Sincerely,",
                "With appreciation,"
            ]
        }

    def _get_subject_variation(self, event_type, service_name):
        """SmartMove Transport subject lines"""
        subjects = {
            'booking_created': [
                f"SmartMove Transport – {service_name} Request Received",
                f"Your Moving Request: {service_name}",
                f"Move Request Confirmed – {service_name}",
                f"Thanks for Choosing SmartMove Transport!"
            ],
            'booking_confirmed': [
                f"Your Move is Confirmed – {service_name}",
                f"Moving Date Scheduled – {service_name}",
                f"SmartMove Transport Confirmation – {service_name}",
                f"Everything is Set for Your Move!"
            ],
            'booking_cancelled': [
                f"Move Cancelled – {service_name}",
                f"Cancellation Confirmation – {service_name}",
                f"SmartMove Transport: Booking Cancelled",
                f"Your Move Has Been Cancelled"
            ],
            'booking_completed': [
                f"Your Move is Complete – {service_name}",
                f"Moving Service Completed – {service_name}",
                f"SmartMove Transport – Move Completed",
                f"Your SmartMove Service Is Finished!"
            ]
        }
        return random.choice(subjects.get(event_type, [f"SmartMove Transport – Update"]))

    def _get_random_variation(self, variation_type, **kwargs):
        """Pick random text variation"""
        variations = self.variations.get(variation_type, [])
        if variations:
            chosen = random.choice(variations)
            return chosen.format(**kwargs) if kwargs else chosen
        return ""

    def send_booking_email(self, booking, service, event_type):
        """
        Sends customer-facing email notifications.
        Structure unchanged — only the content was updated.
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured. Email skipped.")
            return False

        try:
            template_name = f"{event_type}.html"
            template = self.env.get_template(template_name)

            context = {
                'booking': booking,
                'service': service,
                'greeting': self._get_random_variation('greetings', name=booking.customer_name.split()[0]),
                'intro_message': self._get_random_variation(f'{event_type}_intro'),
                'closing': self._get_random_variation('closings'),
                'sender_name': self.sender_name,
                'sender_email': self.sender_email,
                'current_year': datetime.now().year,
                'customer_first_name': booking.customer_name.split()[
                    0] if booking.customer_name else booking.customer_name,
            }

            html_body = template.render(**context)

            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_subject_variation(event_type, service.name)
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = booking.customer_email

            message.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"SmartMove {event_type} email sent to {booking.customer_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SmartMove email: {str(e)}")
            return False

    def send_admin_notification(self, booking, service, event_type):
        """Admin-facing notification (kept same, reworded to moving context)"""
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            return False

        try:
            subject = f"ADMIN: Move {event_type.replace('_', ' ').title()} – {service.name}"

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = admin_email

            html_content = f"""
            <html>
                <body>
                    <h3>Move {event_type.replace('_', ' ').title()}</h3>

                    <p><strong>Customer:</strong> {booking.customer_name}</p>
                    <p><strong>Email:</strong> {booking.customer_email}</p>
                    <p><strong>Phone:</strong> {booking.customer_phone}</p>

                    <p><strong>Service:</strong> {service.name}</p>
                    <p><strong>Preferred Move Time:</strong> {booking.preferred_date} at {booking.preferred_time}</p>
                    <p><strong>Move Details:</strong> {booking.project_description}</p>
                    <p><strong>Pickup Address:</strong> {booking.address}</p>

                    <p><strong>Status:</strong> {booking.status}</p>
                </body>
            </html>
            """

            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Admin SmartMove notification sent for {event_type}")
            return True

        except Exception as e:
            logger.error(f"Failed admin notification: {str(e)}")
            return False

    def send_contact_message(self, contact_message):
        """Send contact form notification to admin"""
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured. Contact email skipped.")
            return False

        try:
            # Try to use template first
            try:
                template = self.env.get_template("contact_notification.html")
                html_body = template.render(
                    message=contact_message,
                    current_year=datetime.now().year,
                    COMPANY_NAME=self.sender_name
                )
            except Exception as template_error:
                logger.warning(f"Contact template not found, using fallback: {template_error}")
                # Fallback HTML
                html_body = f"""
                <html>
                    <body>
                        <h2>New Contact Form Message - {contact_message.subject}</h2>
                        <p><strong>From:</strong> {contact_message.name}</p>
                        <p><strong>Email:</strong> {contact_message.email}</p>
                        <p><strong>Phone:</strong> {contact_message.phone or 'Not provided'}</p>
                        <p><strong>Subject:</strong> {contact_message.subject}</p>
                        <p><strong>Message:</strong> {contact_message.message}</p>
                    </body>
                </html>
                """

            message = MIMEMultipart("alternative")
            message["Subject"] = f"New Contact Message - {contact_message.subject}"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = self.admin_email

            message.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Contact notification sent to admin from {contact_message.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send contact email: {str(e)}")
            return False

    def test_connection(self):
        """Test SMTP connection and credentials"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                logger.info("SMTP connection test successful")
                return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False