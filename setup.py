#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("Setting up Capitol City Contracting website...")
    
    # Install Flask and dependencies
    packages = [
        "Flask==2.3.3",
        "Flask-SQLAlchemy==3.0.5", 
        "twilio==8.10.0",
        "python-dotenv==1.0.0",
        "gunicorn==21.2.0"
    ]
    
    print("Installing dependencies...")
    for package in packages:
        if not run_command(f"pip install {package}"):
            print(f"Failed to install {package}")
            sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("""SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///capitol_contracting.db

# Optional: Configure these for email/SMS notifications
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password
# TWILIO_ACCOUNT_SID=your-twilio-account-sid
# TWILIO_AUTH_TOKEN=your-twilio-auth-token
# TWILIO_PHONE_NUMBER=your-twilio-phone-number
# ADMIN_PHONE=+16135550123
# ADMIN_EMAIL=admin@capitolcitycontracting.ca
""")
        print("✓ Created .env file")
    
    print("\n✅ Setup completed successfully!")
    print("\nTo run the application:")
    print("python app.py")
    print("\nThe website will be available at: http://localhost:5000")

if __name__ == "__main__":
    main()