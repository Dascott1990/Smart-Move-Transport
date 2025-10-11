# 🏗️ Capitol City Contracting – Booking & Service Management App

A modern **Flask-based web application** for managing home renovation services, bookings, testimonials, and contact forms.  
It includes an admin panel, email notifications (with fallback support), and an auto-seeding database for demo purposes.

---

## 🌟 Features

✅ **Dynamic Service Management** – Manage multiple service categories (kitchen, bathroom, basement, etc.)  
✅ **Online Booking System** – Clients can schedule renovation projects directly from the website  
✅ **Automated Email Notifications** – Customer and admin emails for booking confirmations (via SMTP or custom EmailService)  
✅ **Contact Form Handling** – Submit and store client inquiries securely  
✅ **Admin Dashboard** – Review and update bookings (status, confirmations, completions)  
✅ **Database Auto-Seeding** – Preloads services and testimonials for demo/testing  
✅ **Environment Configurable** – Uses `.env` for secrets, email credentials, and database URLs  

---

## 🧠 Tech Stack

| Component | Technology |
|------------|-------------|
| Backend | Flask (Python) |
| Database | SQLite / PostgreSQL (via SQLAlchemy) |
| Email | SMTP or Custom EmailService |
| Frontend | Jinja2 Templates |
| Environment | Python-dotenv |
| Logging | Python `logging` module |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
2. Create & Activate a Virtual Environment
bash
Copy code
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
3. Install Dependencies
bash
Copy code
pip install -r requirements.txt
(If you don’t have one yet, create it using: pip freeze > requirements.txt)

4. Create a .env File
ini
Copy code
# .env
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///capitol_contracting.db

# Email Configuration
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# App Configuration
DEBUG=True
PORT=5002
5. Run the Application
bash
Copy code
python app.py
Access the app at 👉 http://localhost:5002

🗃️ Database Models Overview
Model	Description
Service	Stores information about renovation services
Booking	Tracks customer bookings and status
Testimonial	Customer reviews and ratings
ContactMessage	Stores messages from the contact form

💡 The app auto-seeds demo data (services & testimonials) on first run.

✉️ Email Notification Flow
Customer Booking Created → Sends confirmation email

Admin Notification → Sent on new or cancelled bookings

Fallback SMTP Mode → Used if EmailService isn’t available

Emails are HTML-formatted and branded for a professional look.

🧑‍💻 API Endpoints
Endpoint	Method	Description
/api/bookings	POST	Create a new booking
/api/contact	POST	Submit contact form
/api/admin/bookings/<id>/status	PUT	Update booking status

🧰 Logging
All events are logged using Python’s built-in logging module:

python
Copy code
logging.basicConfig(level=logging.INFO)
Includes logs for:

App startup

Email service initialization

Database seeding

Booking & contact form submissions

📂 Project Structure
bash
Copy code
capitol_contracting/
│
├── templates/
│   ├── index.html
│   ├── about.html
│   ├── services.html
│   ├── contact.html
│   └── booking.html
│
├── notifications/
│   └── email_service.py   # Optional custom service
│
├── app.py                 # Main Flask application
├── requirements.txt
├── .env
└── README.md
🚀 Deployment
Recommended Platforms:

Render

Railway

Heroku

Steps
Push to GitHub

Connect your repo on the platform

Set environment variables (SECRET_KEY, DATABASE_URL, etc.)

Deploy and enjoy 🎉

🧩 Future Enhancements
Add authentication for admin dashboard

Integrate payment gateway

Add analytics dashboard

RESTful API documentation (Swagger / Postman)

💼 Author
Capitol City Contracting Web App
Built with ❤️ by Dascott
🌐 Website: https://windowportfolio-five.vercel.app