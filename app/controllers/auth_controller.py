from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.organization import Organization
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            organization_name = request.form.get('organization_name', '').strip()
            
            # Validate
            if not email or not password:
                flash('Email and password are required', 'danger')
                return render_template('auth/signup.html')
            
            if len(password) < 8:
                flash('Password must be at least 8 characters', 'danger')
                return render_template('auth/signup.html')
            
            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered', 'danger')
                return render_template('auth/signup.html')
            
            # Create organization
            org_name = organization_name or f"{first_name}'s Organization"
            organization = Organization(name=org_name)
            db.session.add(organization)
            db.session.flush()
            
            # Create user
            user = User(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.organization_id = organization.id
            user.is_verified = True  # Auto-verify for now
            
            db.session.add(user)
            db.session.commit()
            
            # Log them in
            login_user(user)
            
            flash(f'Welcome to SendBaba, {user.first_name or user.email}! 🎉', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            logger.error(f"Signup error: {e}")
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)
            
            if not email or not password:
                flash('Email and password are required', 'danger')
                return render_template('auth/login.html')
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Your account has been deactivated', 'danger')
                    return render_template('auth/login.html')
                
                login_user(user, remember=remember)
                user.last_login = db.func.now()
                db.session.commit()
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
                return redirect(url_for('dashboard.index'))
            else:
                flash('Invalid email or password', 'danger')
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('web.index'))
