import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, redirect, url_for
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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///capitol_contracting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# Database Models
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
    project_description = db.Column(db.Text, nullable=False)
    preferred_date = db.Column(db.String(50), nullable=False)
    preferred_time = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)
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

# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Seed initial data if tables are empty
    if Service.query.count() == 0:
        services = [
            Service(
                name="Home Renovations",
                description="Complete home transformation including kitchen and bathroom remodels, basement finishing, and whole-house updates.",
                price_range="$15,000 - $75,000+",
                duration="2-8 weeks",
                icon="🏠"
            ),
            Service(
                name="Kitchen Remodeling",
                description="Custom kitchen designs with quality cabinetry, countertops, and professional installation.",
                price_range="$12,000 - $45,000",
                duration="3-6 weeks",
                icon="🔪"
            ),
            Service(
                name="Bathroom Renovations",
                description="Luxury bathroom upgrades with modern fixtures, tiling, and efficient space planning.",
                price_range="$8,000 - $25,000",
                duration="2-4 weeks",
                icon="🚿"
            ),
            Service(
                name="Basement Finishing",
                description="Transform your basement into functional living space with proper insulation and lighting.",
                price_range="$20,000 - $50,000",
                duration="4-8 weeks",
                icon="🏗️"
            ),
            Service(
                name="Emergency Repairs",
                description="24/7 emergency service for urgent home repairs and damage control.",
                price_range="$150 - $500/hr",
                duration="2-24 hours",
                icon="🚨"
            ),
            Service(
                name="Commercial Build-outs",
                description="Office and retail space construction with commercial-grade materials and compliance.",
                price_range="$50,000 - $200,000+",
                duration="8-16 weeks",
                icon="🏢"
            )
        ]
        db.session.bulk_save_objects(services)
        logger.info("Initial services seeded")
    
    if Testimonial.query.count() == 0:
        testimonials = [
            Testimonial(
                customer_name="Sarah & Mark Thompson",
                project_type="Kitchen Renovation",
                rating=5,
                comment="Capitol City transformed our outdated kitchen into a modern dream space. Professional, on-time, and exceptional quality!",
                is_featured=True
            ),
            Testimonial(
                customer_name="James Wilson",
                project_type="Basement Finishing",
                rating=5,
                comment="They finished our basement ahead of schedule and under budget. The team was clean, respectful, and highly skilled.",
                is_featured=True
            ),
            Testimonial(
                customer_name="Ottawa Dental Clinic",
                project_type="Commercial Build-out",
                rating=5,
                comment="Professional commercial contracting that understood our business needs. Highly recommend for commercial projects!",
                is_featured=True
            )
        ]
        db.session.bulk_save_objects(testimonials)
        logger.info("Initial testimonials seeded")
    
    db.session.commit()

def send_booking_notifications(booking, service, event_type):
    """Send all notifications for booking events"""
    # Send customer email if email service is available
    if email_service:
        email_service.send_booking_email(booking, service, event_type)
    
    # Send admin notifications for important events
    if event_type in ['booking_created', 'booking_cancelled']:
        if email_service:
            email_service.send_admin_notification(booking, service, event_type)

def send_fallback_email_notification(booking, service):
    """Fallback email notification if email service is not available"""
    try:
        # Basic email configuration
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        port = int(os.getenv("SMTP_PORT", 587))
        sender_email = os.environ.get('MAIL_USERNAME')
        password = os.environ.get('MAIL_PASSWORD')
        
        if not sender_email or not password:
            logger.warning("Email credentials not configured. Email skipped.")
            return
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Capitol City Contracting - Booking Confirmation"
        message["From"] = sender_email
        message["To"] = booking.customer_email
        
        # Create HTML content
        html = f"""
        <html>
          <body>
            <h2>Thank you for choosing Capitol City Contracting!</h2>
            <p><strong>Booking Details:</strong></p>
            <ul>
              <li><strong>Name:</strong> {booking.customer_name}</li>
              <li><strong>Service:</strong> {service.name}</li>
              <li><strong>Preferred Date:</strong> {booking.preferred_date}</li>
              <li><strong>Preferred Time:</strong> {booking.preferred_time}</li>
              <li><strong>Project:</strong> {booking.project_description}</li>
            </ul>
            <p>We will review your request and contact you within 24 hours to confirm details and schedule.</p>
            <p>For urgent inquiries, call us at <strong>(613) 555-0123</strong>.</p>
            <br>
            <p>Best regards,<br>Capitol City Contracting Team</p>
          </body>
        </html>
        """
        
        # Add HTML content
        message.attach(MIMEText(html, "html"))
        
        # Send email
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
            
        logger.info(f"Fallback confirmation email sent to {booking.customer_email}")
        
    except Exception as e:
        logger.error(f"Failed to send fallback email: {str(e)}")

# Routes
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

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/booking')
def booking_page():
    services = Service.query.filter_by(is_active=True).all()
    return render_template('booking.html', services=services, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'service_id', 'description', 'date', 'time', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create booking
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
        
        # Send notifications
        if email_service:
            send_booking_notifications(booking, service, "booking_created")
        else:
            # Use fallback email notification
            send_fallback_email_notification(booking, service)
        
        return jsonify({
            'message': 'Booking request submitted successfully! We will contact you within 24 hours.',
            'booking_id': booking.id
        }), 201
        
    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to process booking request'}), 500

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
            
            # Send email notification
            if email_service:
                email_service.send_booking_email(booking, service, event_type)
        
        return jsonify({'message': 'Status updated successfully'})
        
    except Exception as e:
        logger.error(f"Status update error: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500

# Production configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Capitol City Contracting application...")
    logger.info(f"Email service available: {EMAIL_SERVICE_AVAILABLE}")
    logger.info(f"Production: {not debug}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)