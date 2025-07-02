// Main JavaScript file for AgriInsight

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    const mobileMenu = document.getElementById('mobile-menu');
    const navLinks = document.getElementById('nav-links');

    if (mobileMenu && navLinks) {
        mobileMenu.addEventListener('click', () => {
            mobileMenu.classList.toggle('active');
            navLinks.classList.toggle('active');

            // Animate hamburger icon
            const spans = mobileMenu.querySelectorAll('span');
            if (mobileMenu.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                spans[0].style.transform = 'rotate(0) translate(0)';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'rotate(0) translate(0)';
            }
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !mobileMenu.contains(e.target)) {
                navLinks.classList.remove('active');
                mobileMenu.classList.remove('active');
                const spans = mobileMenu.querySelectorAll('span');
                spans[0].style.transform = 'rotate(0) translate(0)';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'rotate(0) translate(0)';
            }
        });
    }

    // Form validation helper
    window.validateForm = function(formElement) {
        let isValid = true;
        const requiredFields = formElement.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.parentElement.classList.add('invalid');
                isValid = false;
            } else {
                field.parentElement.classList.remove('invalid');
            }
        });

        return isValid;
    };

    // Helper function to get CSRF token
    window.getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    // Real-time form validation
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.parentElement.classList.contains('invalid')) {
                this.parentElement.classList.remove('invalid');
            }
        });
    });

    // Loading state helper
    window.showLoading = function(button, text = 'Loading...') {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = text;
    };

    window.hideLoading = function(button) {
        button.disabled = false;
        button.textContent = button.dataset.originalText;
    };

    // Toast notification helper
    window.showToast = function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Add toast styles if not already present
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 20px;
                    border-radius: 5px;
                    color: white;
                    font-weight: 500;
                    z-index: 1000;
                    animation: slideIn 0.3s ease;
                }
                .toast-success { background-color: var(--success); }
                .toast-error { background-color: var(--error); }
                .toast-info { background-color: var(--primary); }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    };

    // Profile popup functionality
    const profileIcon = document.getElementById('profileIcon');
    const profilePopup = document.getElementById('profilePopup');
    const closePopup = document.getElementById('closePopup');
    
    if (profileIcon && profilePopup) {
        // Open popup when profile icon is clicked
        profileIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            profilePopup.classList.add('active');
        });
        
        // Close popup when close button is clicked
        if (closePopup) {
            closePopup.addEventListener('click', function(e) {
                e.stopPropagation();
                profilePopup.classList.remove('active');
            });
        }
        
        // Close popup when clicking outside
        document.addEventListener('click', function(e) {
            if (!profilePopup.contains(e.target) && !profileIcon.contains(e.target)) {
                profilePopup.classList.remove('active');
            }
        });
        
        // Close popup on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && profilePopup.classList.contains('active')) {
                profilePopup.classList.remove('active');
            }
        });
    }

    // Signup form validation
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        const nameInput = document.getElementById('name');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirmPassword');
        
        // Real-time validation
        function validateField(field, validationFn, errorMessage) {
            const formGroup = field.closest('.form-group');
            const errorSpan = formGroup.querySelector('.error-message');
            
            if (validationFn(field.value)) {
                formGroup.classList.remove('invalid');
                errorSpan.style.display = 'none';
                return true;
            } else {
                formGroup.classList.add('invalid');
                errorSpan.style.display = 'block';
                errorSpan.textContent = errorMessage;
                return false;
            }
        }
        
        // Name validation
        if (nameInput) {
            nameInput.addEventListener('blur', function() {
                validateField(this, 
                    value => value.trim().length >= 2, 
                    'Name must be at least 2 characters long'
                );
            });
        }
        
        // Email validation
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                validateField(this, 
                    value => emailRegex.test(value), 
                    'Please enter a valid email address'
                );
            });
        }
        
        // Password validation
        if (passwordInput) {
            passwordInput.addEventListener('blur', function() {
                validateField(this, 
                    value => value.length >= 6, 
                    'Password must be at least 6 characters long'
                );
            });
        }
        
        // Confirm password validation
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('blur', function() {
                validateField(this, 
                    value => value === passwordInput.value, 
                    'Passwords do not match'
                );
            });
        }
        
        // Form submission validation
        signupForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Validate all fields
            if (nameInput && !validateField(nameInput, 
                value => value.trim().length >= 2, 
                'Name must be at least 2 characters long')) {
                isValid = false;
            }
            
            if (emailInput && !validateField(emailInput, 
                value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value), 
                'Please enter a valid email address')) {
                isValid = false;
            }
            
            if (passwordInput && !validateField(passwordInput, 
                value => value.length >= 6, 
                'Password must be at least 6 characters long')) {
                isValid = false;
            }
            
            if (confirmPasswordInput && !validateField(confirmPasswordInput, 
                value => value === passwordInput.value, 
                'Passwords do not match')) {
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
                // Scroll to first error
                const firstError = document.querySelector('.form-group.invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }
}); 