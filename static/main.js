// Animations on page load
document.addEventListener('DOMContentLoaded', () => {
    animateElements();
    initializeFormValidation();
    initializeLoadingSpinners();
});

// Animate elements with fade-in effect
function animateElements() {
    const elements = document.querySelectorAll('.card, .form-control, .btn');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        setTimeout(() => {
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Form validation functions
function validateSignupForm() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    clearErrors();

    let isValid = true;
    
    if (username.length < 3) {
        showError('username', 'Username must be at least 3 characters long');
        isValid = false;
    }

    if (password.length < 6) {
        showError('password', 'Password must be at least 6 characters long');
        isValid = false;
    }

    if (password !== confirmPassword) {
        showError('confirm_password', 'Passwords do not match');
        isValid = false;
    }

    return isValid;
}

function validateLoginForm() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    clearErrors();

    let isValid = true;

    if (!username.trim()) {
        showError('username', 'Username is required');
        isValid = false;
    }

    if (!password.trim()) {
        showError('password', 'Password is required');
        isValid = false;
    }

    return isValid;
}

function validateJobPostingForm() {
    clearErrors();
    
    const fields = {
        'job_title': 'Job title is required',
        'company_name': 'Company name is required',
        'job_description': 'Job description must be at least 50 characters',
        'requirements': 'Job requirements are required'
    };

    let isValid = true;

    for (const [fieldId, message] of Object.entries(fields)) {
        const field = document.getElementById(fieldId);
        if (!field.value.trim() || (fieldId === 'job_description' && field.value.length < 50)) {
            showError(fieldId, message);
            isValid = false;
        }
    }

    return isValid;
}

// Show error with animation
function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(`${fieldId}_error`) || createErrorDiv(fieldId);
    
    field.classList.add('is-invalid');
    errorDiv.textContent = message;
    errorDiv.style.animation = 'slideIn 0.3s ease';
}

// Create error div if it doesn't exist
function createErrorDiv(fieldId) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.createElement('div');
    errorDiv.id = `${fieldId}_error`;
    errorDiv.className = 'invalid-feedback';
    field.parentNode.appendChild(errorDiv);
    return errorDiv;
}

// Clear all errors with fade-out effect
function clearErrors() {
    const errorElements = document.querySelectorAll('.is-invalid, .invalid-feedback');
    errorElements.forEach(element => {
        if (element.classList.contains('is-invalid')) {
            element.classList.remove('is-invalid');
        } else {
            element.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => element.remove(), 300);
        }
    });
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const formId = form.id;
            let isValid = true;

            switch(formId) {
                case 'signup-form':
                    isValid = validateSignupForm();
                    break;
                case 'login-form':
                    isValid = validateLoginForm();
                    break;
                case 'job-posting-form':
                    isValid = validateJobPostingForm();
                    break;
            }

            if (!isValid) {
                e.preventDefault();
                highlightErrors();
            }
        });
    });
}

// Add loading spinners to forms
function initializeLoadingSpinners() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (this.checkValidity()) {
                const submitBtn = this.querySelector('[type="submit"]');
                const spinner = createSpinner();
                submitBtn.disabled = true;
                submitBtn.prepend(spinner);
            }
        });
    });
}

// Create spinner element
function createSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    spinner.setAttribute('role', 'status');
    spinner.innerHTML = '<span class="visually-hidden">Loading...</span>';
    return spinner;
}

// Highlight form errors with animation
function highlightErrors() {
    const invalidFields = document.querySelectorAll('.is-invalid');
    invalidFields.forEach((field, index) => {
        setTimeout(() => {
            field.style.animation = 'shake 0.5s ease';
        }, index * 100);
    });
}

// Add shake animation for invalid fields
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    @keyframes fadeOut {
        to { opacity: 0; transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);