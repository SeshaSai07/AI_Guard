from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import joblib
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from markupsafe import Markup

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load the trained model and vectorizer
try:
    logger.info('Attempting to load ML models...')
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    classifier_path = os.path.join(model_dir, 'job_classifier.pkl')
    vectorizer_path = os.path.join(model_dir, 'tfidf_vectorizer.pkl')
    
    if not os.path.exists(classifier_path) or not os.path.exists(vectorizer_path):
        logger.error('Model files not found. Please ensure models are trained.')
        raise FileNotFoundError('Required model files are missing')
        
    classifier = joblib.load(classifier_path)
    vectorizer = joblib.load(vectorizer_path)
    logger.info('Successfully loaded ML models')
except Exception as e:
    logger.error(f'Error loading ML models: {str(e)}')
    classifier = None
    vectorizer = None

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Please fill in all fields', 'danger')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        if username in [user.username for user in users.values()]:
            flash('Username already exists', 'danger')
            return render_template('signup.html')
        
        user_id = str(len(users) + 1)
        password_hash = generate_password_hash(password)
        users[user_id] = User(user_id, username, password_hash)
        
        flash('Registration successful! Please login with your credentials.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = next((user for user in users.values() if user.username == username), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash(f'Welcome back, {username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Goodbye {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/check_job', methods=['GET', 'POST'])
@login_required
def check_job():
    if request.method == 'POST':
        # Get all form fields
        job_title = request.form.get('job_title', '')
        company_name = request.form.get('company_name', '')
        job_location = request.form.get('job_location', '')
        job_description = request.form.get('job_description', '')
        requirements = request.form.get('requirements', '')
        salary_range = request.form.get('salary_range', '')
        benefits = request.form.get('benefits', '')
        employment_type = request.form.get('employment_type', '')
        contact_info = request.form.get('contact_info', '')
        application_method = request.form.get('application_method', '')

        # Combine all fields into a single text for analysis
        combined_text = f"""
        Job Title: {job_title}
        Company: {company_name}
        Location: {job_location}
        
        Description:
        {job_description}
        
        Requirements:
        {requirements}
        
        Compensation:
        Salary Range: {salary_range}
        Benefits: {benefits}
        Employment Type: {employment_type}
        
        Contact & Application:
        {contact_info}
        {application_method}
        """

        if not combined_text.strip():
            flash('Please enter job posting details', 'error')
            return render_template('check_job.html')

        if classifier is None or vectorizer is None:
            flash('Job classification service is currently unavailable', 'error')
            return render_template('check_job.html')

        try:
            # Transform the text using the vectorizer
            features = vectorizer.transform([combined_text])
            prediction = classifier.predict(features)[0]
            probability = classifier.predict_proba(features)[0][1]

            # Initialize analysis lists
            red_flags = []
            positive_indicators = []
            
            # Define red flag keywords
            red_flag_keywords = {
                'payment_info': ['bank account', 'wire transfer', 'payment details', 'financial information'],
                'personal_info': ['ssn', 'social security', 'passport', 'driver license', 'personal documents'],
                'too_good': ['unlimited earning', 'instant money', 'quick money', 'work from home', 'be your own boss'],
                'unprofessional': ['urgent hiring', 'immediate start', 'no experience needed', 'earn from home'],
                'suspicious_payment': ['upfront payment', 'training fee', 'registration fee', 'certification fee'],
            }

            legitimate_indicators = {
                'company_details': ['company history', 'about us', 'established', 'founded'],
                'professional_terms': ['benefits package', 'health insurance', '401k', 'professional development'],
                'clear_requirements': ['years of experience', 'degree required', 'qualifications', 'skills required'],
                'detailed_process': ['interview process', 'selection process', 'background check', 'references'],
            }

            combined_text_lower = combined_text.lower()
            
            # Check for red flags
            for category, keywords in red_flag_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text_lower:
                        red_flags.append(f"Contains suspicious term: '{keyword}'")

            # Check for legitimate indicators
            for category, keywords in legitimate_indicators.items():
                for keyword in keywords:
                    if keyword in combined_text_lower:
                        positive_indicators.append(f"Contains professional term: '{keyword}'")

            # Additional checks
            if not job_location.strip():
                red_flags.append("No specific job location provided")
            if not company_name.strip():
                red_flags.append("No company name provided")
            if len(job_description.strip()) < 100:
                red_flags.append("Job description is unusually short")
            if not requirements.strip():
                red_flags.append("No specific job requirements listed")
            
            # Check for professional email domain
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            emails = re.findall(email_pattern, contact_info.lower())
            if emails:
                if any(email.endswith(('.com', '.org', '.net', '.edu')) for email in emails):
                    positive_indicators.append("Contains professional email contact")
                else:
                    red_flags.append("Contains suspicious email domain")

            # Determine risk level and generate detailed explanation
            if probability > 0.8 or len(red_flags) >= 3:
                risk_level = 'high'
                risk_explanation = "This job posting shows multiple high-risk indicators typical of fraudulent listings."
            elif probability > 0.5 or len(red_flags) >= 1:
                risk_level = 'medium'
                risk_explanation = "This job posting shows some concerning patterns but requires further verification."
            else:
                risk_level = 'low'
                risk_explanation = "This job posting appears to follow professional standards and contains legitimate indicators."

            # Add positive aspects if the job seems legitimate
            if prediction == 0:
                risk_explanation += "\n\nPositive aspects of this posting:"
                for indicator in positive_indicators:
                    risk_explanation += f"\n- {indicator}"

            # Add detailed warning if the job seems suspicious
            if prediction == 1:
                risk_explanation += "\n\nWarning signs detected:"
                for flag in red_flags:
                    risk_explanation += f"\n- {flag}"

            # Convert newlines to HTML breaks
            risk_explanation = Markup(risk_explanation.replace('\n', '<br>'))

            return render_template('result.html',
                                job_title=job_title,
                                company_name=company_name,
                                job_location=job_location,
                                job_description=job_description,
                                requirements=requirements,
                                salary_range=salary_range,
                                benefits=benefits,
                                employment_type=employment_type,
                                contact_info=contact_info,
                                application_method=application_method,
                                prediction=prediction,
                                probability=probability,
                                risk_level=risk_level,
                                red_flags=red_flags,
                                positive_indicators=positive_indicators,
                                risk_explanation=risk_explanation)

        except Exception as e:
            flash(f'Error analyzing job posting: {str(e)}', 'error')
            return render_template('check_job.html')

    return render_template('check_job.html')

@app.route('/check_url')
@login_required
def check_url():
    return render_template('check_url.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)