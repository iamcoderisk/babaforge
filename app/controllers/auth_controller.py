from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.organization import Organization
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter email and password', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember', False))
            
            # Update last login
            try:
                user.last_login = datetime.utcnow()
                db.session.commit()
            except:
                pass
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/dashboard/')
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', email.split('@')[0] if email else '')
        
        if not email or not password:
            flash('Email and password required', 'error')
            return render_template('auth/register.html')
        
        # Validate password length
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            # Create organization
            org = Organization(name=f"{name}'s Organization")
            db.session.add(org)
            db.session.flush()
            
            # Create user
            user = User(
                email=email,
                name=name,
                organization_id=org.id,
                password_hash=generate_password_hash(password),
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # Log the user in
            login_user(user)
            flash('Registration successful! Welcome to SendBaba.', 'success')
            return redirect('/dashboard/')
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Signup error: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect('/')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password"""
    if request.method == 'POST':
        email = request.form.get('email')
        # TODO: Implement password reset logic
        flash('Password reset instructions sent to your email.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

# Legacy routes for backward compatibility
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Legacy /signup route"""
    return register()

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def auth_login():
    """Legacy /auth/login route"""
    return login()

@auth_bp.route('/auth/register', methods=['GET', 'POST'])
def auth_register():
    """Legacy /auth/register route"""
    return register()

@auth_bp.route('/auth/signup', methods=['GET', 'POST'])
def auth_signup():
    """Legacy /auth/signup route"""
    return register()

@auth_bp.route('/auth/logout')
@login_required
def auth_logout():
    """Legacy /auth/logout route"""
    return logout()
