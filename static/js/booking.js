// Booking Form Handling
document.addEventListener('DOMContentLoaded', function() {
    const bookingForm = document.getElementById('bookingForm');
    const submitBtn = document.getElementById('submitBtn');
    const formMessage = document.getElementById('formMessage');
    
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Validate form
            if (!validateBookingForm()) {
                return;
            }
            
            // Show loading state - ONLY DISABLE BUTTON
            submitBtn.disabled = true;
            formMessage.innerHTML = '';
            
            try {
                const formData = new FormData(bookingForm);
                const bookingData = {
                    name: formData.get('name'),
                    email: formData.get('email'),
                    phone: formData.get('phone'),
                    service_id: parseInt(formData.get('service_id')),
                    description: formData.get('description'),
                    date: formData.get('date'),
                    time: formData.get('time'),
                    address: formData.get('address')
                };
                
                const response = await fetch('/api/bookings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(bookingData)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showFormMessage('Booking request submitted successfully! We will contact you within 24 hours.', 'success');
                    bookingForm.reset();
                } else {
                    throw new Error(data.error || 'Failed to submit booking');
                }
            } catch (error) {
                console.error('Booking error:', error);
                showFormMessage(error.message || 'Failed to submit booking request. Please try again or call us directly.', 'error');
            } finally {
                // ALWAYS RE-ENABLE BUTTON
                submitBtn.disabled = false;
            }
        });
    }
    
    function validateBookingForm() {
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const service = document.getElementById('service').value;
        const description = document.getElementById('description').value.trim();
        const date = document.getElementById('date').value;
        const time = document.getElementById('time').value;
        const address = document.getElementById('address').value.trim();
        
        // Basic validation
        if (!name) {
            showFormMessage('Please enter your full name.', 'error');
            return false;
        }
        
        if (!validateEmail(email)) {
            showFormMessage('Please enter a valid email address.', 'error');
            return false;
        }
        
        if (!phone) {
            showFormMessage('Please enter your phone number.', 'error');
            return false;
        }
        
        if (!service) {
            showFormMessage('Please select a service.', 'error');
            return false;
        }
        
        if (!description) {
            showFormMessage('Please describe your project.', 'error');
            return false;
        }
        
        if (!date) {
            showFormMessage('Please select a preferred date.', 'error');
            return false;
        }
        
        if (!time) {
            showFormMessage('Please select a preferred time.', 'error');
            return false;
        }
        
        if (!address) {
            showFormMessage('Please enter the project address.', 'error');
            return false;
        }
        
        return true;
    }
    
    function showFormMessage(message, type) {
        formMessage.innerHTML = `
            <div class="alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        formMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
});

// Contact Form Handling
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    const contactSubmitBtn = contactForm?.querySelector('button[type="submit"]');
    
    if (contactForm && contactSubmitBtn) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // DISABLE BUTTON
            contactSubmitBtn.disabled = true;
            
            try {
                // Get form data
                const formData = new FormData(contactForm);
                const contactData = {
                    name: formData.get('name'),
                    email: formData.get('email'),
                    phone: formData.get('phone'),
                    subject: formData.get('subject'),
                    message: formData.get('message')
                };
                
                console.log('Sending contact data:', contactData);
                
                // Send to backend
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(contactData)
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // SUCCESS - Show alert and reset form
                    alert('Thank you for your message! We will get back to you within 24 hours.');
                    contactForm.reset();
                    console.log('Contact form submitted successfully');
                } else {
                    throw new Error(data.error || 'Failed to send message');
                }
                
            } catch (error) {
                // ERROR - Show alert
                console.error('Contact form error:', error);
                alert(error.message || 'Failed to send message. Please try again.');
            } finally {
                // ⭐⭐⭐ ALWAYS RE-ENABLE BUTTON ⭐⭐⭐
                contactSubmitBtn.disabled = false;
                console.log('Contact button re-enabled');
            }
        });
    }
});