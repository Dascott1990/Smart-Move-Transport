# app.py — SmartMove Transport (MOVE SMART. MOVE FAST.)
# Rebranded from Capitol City Contracting -> SmartMove Transport
# Contact: (416) 505-6927 | smartmove.ca@outlook.com
# NOTE: Only wording, seeds, and template context changed. Schema, routes, and logic preserved.

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import email service
try:
    from notifications.email_service import EmailService

    EMAIL_SERVICE_AVAILABLE = True
except ImportError as e:
    EMAIL_SERVICE_AVAILABLE = False
    logger.warning(f"Email service not available: {e}")

# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///capitol_contracting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Company-wide constants for templates and notifications
COMPANY_NAME = "SmartMove Transport"
SLOGAN = "MOVE SMART. MOVE FAST."
COMPANY_PHONE = "(416) 505-6927"
COMPANY_PHONE_RAW = "4165056927"
COMPANY_EMAIL = "smartmove.ca@outlook.com"
SERVICE_AREAS = "GTA, Ottawa & Surrounding Areas"

# Initialize database
db = SQLAlchemy(app)

# Initialize email service if available
email_service = None
if EMAIL_SERVICE_AVAILABLE:
    try:
        email_service = EmailService()
        logger.info("Email service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize email service: {e}")
        email_service = None


# Database Models (unchanged)
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_range = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    service = db.relationship('Service', backref=db.backref('bookings', lazy=True))
    project_description = db.Column(db.Text, nullable=False)  # used for move details / notes
    preferred_date = db.Column(db.String(50), nullable=False)
    preferred_time = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)  # pickup address
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    project_type = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Template context processors: provide company info and year globally
@app.context_processor
def inject_company_info():
    return {
        'COMPANY_NAME': COMPANY_NAME,
        'SLOGAN': SLOGAN,
        'COMPANY_PHONE': COMPANY_PHONE,
        'COMPANY_EMAIL': COMPANY_EMAIL,
        'SERVICE_AREAS': SERVICE_AREAS,
        'current_year': datetime.now().year
    }


# Initialize database tables and seed moving services/testimonials (non-destructive)
with app.app_context():
    db.create_all()

    # Seed initial moving service data if none exists
    if Service.query.count() == 0:
        services = [
            Service(
                name="Residential Moving",
                description="Full-service residential moves: apartments, condos, and houses. Includes careful handling of furniture, appliances, and specialty items.",
                price_range="$150 - $1,500+",
                duration="Same day - 2 days (depends on home size & distance)",
                icon="📦"
            ),
            Service(
                name="Office & Commercial Moving",
                description="Professional office relocation services: desks, IT equipment, modular offices, and efficient commercial logistics.",
                price_range="$500 - $10,000+",
                duration="1-5 days",
                icon="🏢"
            ),
            Service(
                name="Packing & Unpacking",
                description="Professional packing and unpacking services using quality materials to keep items safe during transit.",
                price_range="$100 - $1,200+",
                duration="2-8 hours (per job)",
                icon="🧰"
            ),
            Service(
                name="Truck & Driver Rental",
                description="Rent a truck with a professional driver. Ideal for DIY moves where you need a vehicle and experienced operator.",
                price_range="$80/hr - $200/hr",
                duration="Hourly / Daily",
                icon="🚚"
            ),
            Service(
                name="Long Distance Moving",
                description="Intercity and long-distance moves with trusted partners and secure transport. Door-to-door service available.",
                price_range="$1,200 - $10,000+",
                duration="1-7 days (depending on distance)",
                icon="🛣️"
            ),
            Service(
                name="Junk Removal & Disposal",
                description="Removal of unwanted items, clean-outs, and responsible disposal/recycling of materials after your move.",
                price_range="$75 - $1,000+",
                duration="Same day",
                icon="🗑️"
            )
        ]
        db.session.bulk_save_objects(services)
        logger.info("Initial moving services seeded")

    # Seed a few testimonials relevant to moving
    if Testimonial.query.count() == 0:
        testimonials = [
            Testimonial(
                customer_name="Aisha & Daniel Park",
                project_type="Residential Move",
                rating=5,
                comment="SmartMove Transport made our move effortless — punctual crew, careful with our furniture, and great communication.",
                is_featured=True
            ),
            Testimonial(
                customer_name="MapleTech Offices",
                project_type="Office Relocation",
                rating=5,
                comment="Seamless office move with minimal downtime. Professional team and excellent coordination.",
                is_featured=True
            ),
            Testimonial(
                customer_name="Paul N.",
                project_type="Long Distance Move",
                rating=5,
                comment="Handled our long-distance move with care. On time and items arrived in perfect condition.",
                is_featured=True
            )
        ]
        db.session.bulk_save_objects(testimonials)
        logger.info("Initial moving testimonials seeded")

    db.session.commit()


# Notification helpers (preserve original behavior, updated wording where applicable)
def send_booking_notifications(booking, service, event_type):
    """
    Send customer and admin notifications for booking events.
    event_type one of: 'booking_created', 'booking_confirmed', 'booking_cancelled', 'booking_completed'
    """
    # Send customer email if email service is available
    if email_service:
        try:
            email_service.send_booking_email(booking, service, event_type)
        except Exception as e:
            logger.error(f"EmailService failed to send {event_type}: {e}")
    else:
        # fallback: send basic HTML email using SMTP (if credentials available)
        if event_type == 'booking_created':
            send_fallback_email_notification(booking, service)

    # Send admin notifications for created/cancelled events
    if event_type in ['booking_created', 'booking_cancelled']:
        if email_service:
            try:
                email_service.send_admin_notification(booking, service, event_type)
            except Exception as e:
                logger.error(f"EmailService failed to send admin notification: {e}")


def send_fallback_email_notification(booking, service):
    """Fallback simple email if templated email service not available."""
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        port = int(os.getenv("SMTP_PORT", 587))
        sender_email = os.environ.get('MAIL_USERNAME') or COMPANY_EMAIL
        password = os.environ.get('MAIL_PASSWORD')

        if not sender_email or not password:
            logger.warning("Email credentials not configured. Fallback email skipped.")
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = f"{COMPANY_NAME} - Move Request Received"
        message["From"] = sender_email
        message["To"] = booking.customer_email

        html = f"""
        <html>
          <body>
            <h2>Thank you for choosing {COMPANY_NAME}!</h2>
            <p><strong>Move Details:</strong></p>
            <ul>
              <li><strong>Name:</strong> {booking.customer_name}</li>
              <li><strong>Service:</strong> {service.name}</li>
              <li><strong>Preferred Date:</strong> {booking.preferred_date}</li>
              <li><strong>Preferred Time:</strong> {booking.preferred_time}</li>
              <li><strong>Notes:</strong> {booking.project_description}</li>
              <li><strong>Pickup Address:</strong> {booking.address}</li>
            </ul>
            <p>We will contact you within 24 hours to confirm details and provide a quote.</p>
            <p>For urgent moves, call us at <strong>{COMPANY_PHONE}</strong>.</p>
            <br>
            <p>Best regards,<br>{COMPANY_NAME} Team</p>
          </body>
        </html>
        """
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)

        logger.info(f"Fallback confirmation email sent to {booking.customer_email}")
    except Exception as e:
        logger.error(f"Failed to send fallback email: {str(e)}")


def send_contact_confirmation_email(contact_message):
    """Send confirmation email to user when they submit contact form."""
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        port = int(os.getenv("SMTP_PORT", 587))
        sender_email = os.environ.get('MAIL_USERNAME') or COMPANY_EMAIL
        password = os.environ.get('MAIL_PASSWORD')

        if not sender_email or not password:
            logger.warning("Email credentials not configured. Contact confirmation email skipped.")
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = f"{COMPANY_NAME} - We Received Your Message"
        message["From"] = sender_email
        message["To"] = contact_message.email

        html = f"""
        <html>
          <body>
            <h2>Thank you for contacting {COMPANY_NAME}!</h2>
            <p>We have received your message and will get back to you within 24 hours.</p>

            <p><strong>Your Message Details:</strong></p>
            <ul>
              <li><strong>Name:</strong> {contact_message.name}</li>
              <li><strong>Subject:</strong> {contact_message.subject}</li>
              <li><strong>Message:</strong> {contact_message.message}</li>
            </ul>

            <p>For urgent matters, please call us directly at <strong>{COMPANY_PHONE}</strong>.</p>
            <br>
            <p>Best regards,<br>{COMPANY_NAME} Team</p>
          </body>
        </html>
        """
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)

        logger.info(f"Contact confirmation email sent to {contact_message.email}")
    except Exception as e:
        logger.error(f"Failed to send contact confirmation email: {str(e)}")


# Routes (same endpoints, reworded for views)
@app.route('/')
def index():
    services = Service.query.filter_by(is_active=True).limit(3).all()
    testimonials = Testimonial.query.filter_by(is_featured=True).all()
    return render_template('index.html', services=services, testimonials=testimonials)


@app.route('/services')
def services():
    services = Service.query.filter_by(is_active=True).all()
    return render_template('services.html', services=services)


@app.route('/about')
def about():
    testimonials = Testimonial.query.filter_by(is_featured=True).all()
    return render_template('about.html', testimonials=testimonials)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # extract form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # save message to DB
        contact_message = ContactMessage(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        db.session.add(contact_message)
        db.session.commit()

        # Send confirmation email to user
        send_contact_confirmation_email(contact_message)

        # Notify admin by email
        if email_service:
            try:
                email_service.send_contact_message(contact_message)
            except Exception as e:
                logger.error(f"Failed to send contact notification: {e}")
        else:
            # Fallback admin notification
            try:
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                port = int(os.getenv("SMTP_PORT", 587))
                sender_email = os.environ.get('MAIL_USERNAME') or COMPANY_EMAIL
                password = os.environ.get('MAIL_PASSWORD')

                if sender_email and password:
                    admin_message = MIMEMultipart("alternative")
                    admin_message["Subject"] = f"New Contact Message - {contact_message.subject}"
                    admin_message["From"] = sender_email
                    admin_message["To"] = COMPANY_EMAIL

                    html = f"""
                    <html>
                      <body>
                        <h2>New Contact Form Message</h2>
                        <p><strong>From:</strong> {contact_message.name}</p>
                        <p><strong>Email:</strong> {contact_message.email}</p>
                        <p><strong>Phone:</strong> {contact_message.phone or 'Not provided'}</p>
                        <p><strong>Subject:</strong> {contact_message.subject}</p>
                        <p><strong>Message:</strong> {contact_message.message}</p>
                      </body>
                    </html>
                    """
                    admin_message.attach(MIMEText(html, "html"))

                    with smtplib.SMTP(smtp_server, port) as server:
                        server.starttls()
                        server.login(sender_email, password)
                        server.send_message(admin_message)
            except Exception as e:
                logger.error(f"Failed to send fallback admin notification: {e}")

        flash('Thank you for your message! We will get back to you within 24 hours.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/booking')
def booking_page():
    services = Service.query.filter_by(is_active=True).all()
    return render_template('booking.html', services=services, today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()

        # Validate required fields (same fields kept)
        required_fields = ['name', 'email', 'phone', 'service_id', 'description', 'date', 'time', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create booking (address = pickup address)
        booking = Booking(
            customer_name=data['name'],
            customer_email=data['email'],
            customer_phone=data['phone'],
            service_id=data['service_id'],
            project_description=data['description'],
            preferred_date=data['date'],
            preferred_time=data['time'],
            address=data['address']
        )

        db.session.add(booking)
        db.session.commit()

        # Get service details for notifications
        service = db.session.get(Service, data['service_id'])

        # Send notifications (email service preferred, fallback available)
        if email_service:
            send_booking_notifications(booking, service, "booking_created")
        else:
            send_fallback_email_notification(booking, service)

        return jsonify({
            'message': 'Move request submitted successfully! We will contact you within 24 hours.',
            'booking_id': booking.id
        }), 201

    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to process move request'}), 500


@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'error': 'Please enter a valid email address'}), 400

        # Create contact message
        contact_message = ContactMessage(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            subject=data['subject'],
            message=data['message']
        )

        db.session.add(contact_message)
        db.session.commit()

        # Send confirmation email to user
        send_contact_confirmation_email(contact_message)

        # Notify admin by email
        if email_service:
            try:
                email_service.send_contact_message(contact_message)
            except Exception as e:
                logger.error(f"Failed to send contact notification: {e}")

        logger.info(f"Contact form submitted by {contact_message.name} ({contact_message.email})")

        return jsonify({
            'message': 'Thank you for your message! We will get back to you within 24 hours.'
        }), 201

    except Exception as e:
        logger.error(f"Contact form error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit message. Please try again.'}), 500


@app.route('/admin/bookings')
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin.html', bookings=bookings)


@app.route('/api/admin/bookings/<int:booking_id>/status', methods=['PUT'])
def update_booking_status(booking_id):
    try:
        data = request.get_json()
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        new_status = data.get('status', booking.status)

        # Determine event type based on status change
        event_type = None
        if new_status == 'confirmed' and booking.status != 'confirmed':
            event_type = 'booking_confirmed'
        elif new_status == 'cancelled' and booking.status != 'cancelled':
            event_type = 'booking_cancelled'
        elif new_status == 'completed' and booking.status != 'completed':
            event_type = 'booking_completed'

        booking.status = new_status
        db.session.commit()

        # Send appropriate notifications if status changed
        if event_type:
            service = db.session.get(Service, booking.service_id)
            if email_service:
                try:
                    email_service.send_booking_email(booking, service, event_type)
                except Exception as e:
                    logger.error(f"Failed sending status email: {e}")

        return jsonify({'message': 'Status updated successfully'})

    except Exception as e:
        logger.error(f"Status update error: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500


# ----------------------------
# ERROR HANDLERS (SmartMove Transport)
# ----------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


# Production configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting {COMPANY_NAME} application...")
    logger.info(f"Slogan: {SLOGAN}")
    logger.info(f"Email service available: {EMAIL_SERVICE_AVAILABLE}")
    logger.info(f"Contact: {COMPANY_PHONE} | {COMPANY_EMAIL}")
    logger.info(f"Production: {not debug}")

    app.run(debug=debug, host='0.0.0.0', port=port)