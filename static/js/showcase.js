// Showcase Gallery Auto-Swiping Functionality
class ShowcaseGallery {
    constructor() {
        this.track = document.getElementById('showcaseTrack');
        this.slides = document.querySelectorAll('.showcase-slide');
        this.dots = document.querySelectorAll('.dot');
        this.prevBtn = document.querySelector('.showcase-prev');
        this.nextBtn = document.querySelector('.showcase-next');
        this.currentIndex = 0;
        this.interval = null;
        this.intervalTime = 3000; // 3 seconds
        
        this.init();
    }
    
    init() {
        // Start auto-slide
        this.startAutoSlide();
        
        // Event listeners for navigation
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => {
                this.pauseAutoSlide();
                this.prevSlide();
                this.restartAutoSlide();
            });
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => {
                this.pauseAutoSlide();
                this.nextSlide();
                this.restartAutoSlide();
            });
        }
        
        // Dot navigation
        this.dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                this.pauseAutoSlide();
                this.goToSlide(index);
                this.restartAutoSlide();
            });
        });
        
        // Pause on hover
        if (this.track) {
            this.track.addEventListener('mouseenter', () => this.pauseAutoSlide());
            this.track.addEventListener('mouseleave', () => this.restartAutoSlide());
        }
        
        // Touch/swipe support for mobile
        this.setupTouchEvents();
    }
    
    startAutoSlide() {
        this.interval = setInterval(() => {
            this.nextSlide();
        }, this.intervalTime);
    }
    
    pauseAutoSlide() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
    
    restartAutoSlide() {
        this.pauseAutoSlide();
        this.startAutoSlide();
    }
    
    nextSlide() {
        const nextIndex = (this.currentIndex + 1) % this.slides.length;
        this.goToSlide(nextIndex);
    }
    
    prevSlide() {
        const prevIndex = (this.currentIndex - 1 + this.slides.length) % this.slides.length;
        this.goToSlide(prevIndex);
    }
    
    goToSlide(index) {
        // Remove active classes
        this.slides.forEach(slide => {
            slide.classList.remove('active', 'prev', 'next');
        });
        this.dots.forEach(dot => dot.classList.remove('active'));
        
        // Update current index
        this.currentIndex = index;
        
        // Add active class to current slide
        this.slides[index].classList.add('active');
        this.dots[index].classList.add('active');
        
        // Add prev/next classes for animation context
        const prevIndex = (index - 1 + this.slides.length) % this.slides.length;
        const nextIndex = (index + 1) % this.slides.length;
        
        this.slides[prevIndex].classList.add('prev');
        this.slides[nextIndex].classList.add('next');
        
        // Trigger custom event
        this.onSlideChange();
    }
    
    onSlideChange() {
        // Add any additional logic when slide changes
        console.log(`Slide changed to: ${this.currentIndex + 1}`);
    }
    
    setupTouchEvents() {
        let startX = 0;
        let endX = 0;
        
        if (this.track) {
            this.track.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
                this.pauseAutoSlide();
            });
            
            this.track.addEventListener('touchend', (e) => {
                endX = e.changedTouches[0].clientX;
                this.handleSwipe(startX, endX);
                this.restartAutoSlide();
            });
        }
    }
    
    handleSwipe(startX, endX) {
        const swipeThreshold = 50;
        const diff = startX - endX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                this.nextSlide(); // Swipe left
            } else {
                this.prevSlide(); // Swipe right
            }
        }
    }
}

// Initialize showcase gallery when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new ShowcaseGallery();
    
    // Add loading state handling for images
    const images = document.querySelectorAll('.showcase-image');
    images.forEach(img => {
        img.addEventListener('load', function() {
            this.style.background = 'none'; // Remove loading background
        });
        
        img.addEventListener('error', function() {
            console.error('Failed to load image:', this.src);
            // You could set a placeholder image here
        });
    });
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ShowcaseGallery;
}