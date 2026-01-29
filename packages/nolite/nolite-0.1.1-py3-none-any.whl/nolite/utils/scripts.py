NOLITE_RUNTIME_JS = """
document.addEventListener('DOMContentLoaded', function() {
    // --- Nolite's simple event delegation runtime for clicks ---
    document.body.addEventListener('click', function(event) {
        let target = event.target;
        while (target && target !== document.body) {
            const action = target.getAttribute('data-nolite-action');
            if (action) {
                handleNoliteAction(target, action);
                event.stopPropagation();
                return;
            }
            target = target.parentElement;
        }
    });

    // --- Initialize all Slider components ---
    document.querySelectorAll('[data-nolite-component="slider"]').forEach(sliderEl => {
        new NoliteSlider(sliderEl);
    });
});

function handleNoliteAction(element, action) {
    switch (action) {
        case 'toggle-class':
            const targetSelector = element.getAttribute('data-nolite-target');
            const className = element.getAttribute('data-nolite-class');
            if (targetSelector && className) {
                const targetElement = document.querySelector(targetSelector);
                if (targetElement) {
                    targetElement.classList.toggle(className);
                } else {
                    console.error(`Nolite action error: Target element '${targetSelector}' not found.`);
                }
            } else {
                console.error('Nolite action error: "toggle-class" requires "data-nolite-target" and "data-nolite-class" attributes.');
            }
            break;
        default:
            console.warn(`Nolite: Unknown action '${action}'`);
    }
}

class NoliteSlider {
    constructor(element) {
        this.slider = element;
        this.track = this.slider.querySelector('.nolite-slider-track');
        this.slides = Array.from(this.track.children);
        this.nextButton = this.slider.querySelector('.nolite-slider-nav.next');
        this.prevButton = this.slider.querySelector('.nolite-slider-nav.prev');
        this.dotsNav = this.slider.querySelector('.nolite-slider-dots');
        this.currentIndex = 0;

        if (this.slides.length === 0) return;

        this.slideWidth = this.slides[0].getBoundingClientRect().width;
        this.setup();
    }

    setup() {
        if (this.dotsNav) {
            this.createDots();
            this.updateDots();
        }

        if (this.nextButton && this.prevButton) {
            this.nextButton.addEventListener('click', () => this.goToSlide(this.currentIndex + 1));
            this.prevButton.addEventListener('click', () => this.goToSlide(this.currentIndex - 1));
        }

        window.addEventListener('resize', () => {
            this.slideWidth = this.slides[0].getBoundingClientRect().width;
            this.goToSlide(this.currentIndex, false);
        });

        this.goToSlide(0, false);
    }

    goToSlide(index, animate = true) {
        if (index < 0) {
            index = this.slides.length - 1;
        } else if (index >= this.slides.length) {
            index = 0;
        }

        if (animate) {
            this.track.style.transition = 'transform 0.5s ease-in-out';
        } else {
            this.track.style.transition = 'none';
        }

        this.track.style.transform = 'translateX(-' + (this.slideWidth * index) + 'px)';
        this.currentIndex = index;

        if (this.dotsNav) {
            this.updateDots();
        }
    }

    createDots() {
        this.dotsNav.innerHTML = '';
        this.slides.forEach((_, index) => {
            const button = document.createElement('button');
            button.classList.add('nolite-slider-dot');
            button.addEventListener('click', () => this.goToSlide(index));
            this.dotsNav.appendChild(button);
        });
        this.dots = Array.from(this.dotsNav.children);
    }

    updateDots() {
        this.dots.forEach((dot, index) => {
            if (index === this.currentIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
}
"""

# We can also add default CSS for components like Modals here.
# This ensures components work out-of-the-box without user styling.
DEFAULT_STYLES_CSS = """
/* Nolite Default Component Styles */

/* Modal Styles */
.nolite-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: none; /* Hidden by default */
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.nolite-modal-backdrop.is-visible {
    display: flex; /* Shown when is-visible class is added */
}

.nolite-modal-content {
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 90%;
    position: relative;
}

.nolite-modal-close {
    position: absolute;
    top: 15px;
    right: 15px;
    border: none;
    background: transparent;
    font-size: 1.5rem;
    cursor: pointer;
    line-height: 1;
}

/* Alert Styles */
.nolite-alert {
    padding: 15px;
    margin-bottom: 20px;
    border: 1px solid transparent;
    border-radius: 4px;
}
.nolite-alert-success {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
}
.nolite-alert-warning {
    color: #856404;
    background-color: #fff3cd;
    border-color: #ffeeba;
}
.nolite-alert-error {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
}

/* Card Styles */
.nolite-card {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    padding: 24px;
    margin-bottom: 20px;
}

/* Navbar Styles */
.nolite-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: #fff;
    border-bottom: 1px solid #e2e8f0;
}
.nolite-navbar-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #2d3748;
}
.nolite-navbar-links {
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
}
.nolite-navbar-links li {
    margin-left: 20px;
}
.nolite-navbar-links a {
    text-decoration: none;
    color: #4a5568;
}
.nolite-navbar-links a:hover {
    color: #2d3748;
}

/* File Upload Styles */
.nolite-file-upload-wrapper {
    border: 2px dashed #ccc;
    border-radius: 6px;
    padding: 25px;
    text-align: center;
    cursor: pointer;
}
.nolite-file-upload-wrapper:hover {
    border-color: #007bff;
}
.nolite-file-upload-input {
    display: none;
}
.nolite-file-upload-label {
    color: #007bff;
    font-weight: bold;
}

/* Slider Styles */
.nolite-slider {
    position: relative;
    overflow: hidden;
    width: 100%;
}
.nolite-slider-track {
    display: flex;
}
.nolite-slider-slide {
    min-width: 100%;
    box-sizing: border-box;
    flex-shrink: 0;
}
.nolite-slider-nav {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background-color: rgba(255, 255, 255, 0.7);
    border: 1px solid #ccc;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    cursor: pointer;
    z-index: 10;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 1.5rem;
}
.nolite-slider-nav:hover {
    background-color: white;
}
.nolite-slider-nav.prev {
    left: 10px;
}
.nolite-slider-nav.next {
    right: 10px;
}
.nolite-slider-dots {
    position: absolute;
    bottom: 15px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 8px;
    z-index: 10;
}
.nolite-slider-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #fff;
    background-color: #ccc;
    cursor: pointer;
    padding: 0;
}
.nolite-slider-dot.active {
    background-color: white;
}
"""
