from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.organization import Organization

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter email and password', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember', False))
            return redirect('/dashboard/')
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', email.split('@')[0])
        
        if not email or not password:
            flash('Email and password required', 'error')
            return render_template('auth/signup.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/signup.html')
        
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
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            return redirect('/dashboard/')
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Signup error: {e}")
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# Alias for backward compatibility
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    return signup()
