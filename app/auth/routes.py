from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.extensions import db, bcrypt, mail, limiter
from app.models import User, Interests, Notification
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
import os

auth_bp = Blueprint('auth', __name__)

def get_serializer():
    return URLSafeTimedSerializer(os.getenv('SECRET_KEY'))

# ---------- REGISTER ----------
@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not all([name, username, email, password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html')

        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle profile picture upload
        profile_pic_url = None
        file = request.files.get('profile_picture')
        if file and file.filename:
            from werkzeug.utils import secure_filename
            upload_folder = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder, filename))
            profile_pic_url = f'/static/uploads/{filename}'

        user = User(name=name, username=username, email=email,
                    password_hash=pw_hash, profile_picture=profile_pic_url)
        db.session.add(user)
        db.session.commit()

        flash('Registered! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

# ---------- LOGIN ----------
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id']  = user.id
            session['username'] = user.username
            user.is_online = True
            db.session.commit()
            next_page = request.args.get('next')
            if not Interests.query.filter_by(user_id=user.id).first():
                return redirect(url_for('profile.interests'))
            return redirect(next_page or url_for('profile.view_profile', username=user.username))
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html')

# ---------- LOGOUT ----------
@auth_bp.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.is_online = False
            db.session.commit()
    session.clear()
    return redirect(url_for('auth.login'))

# ---------- FORGOT PASSWORD ----------
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()
        # Always show same message to prevent user enumeration
        flash('If that email exists, a reset link has been sent.', 'info')
        if user:
            token = get_serializer().dumps(email, salt='password-reset')
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            msg = Message("Reset your FriendSync password",
                          sender=os.getenv('MAIL_USERNAME'),
                          recipients=[email])
            msg.body = f"Hi {user.name},\n\nReset your password using the link below:\n\n{reset_link}\n\nThis link expires in 1 hour.\n\nIf you didn't request this, ignore this email."
            try:
                mail.send(msg)
            except Exception:
                pass
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')

# ---------- RESET PASSWORD ----------
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = get_serializer().loads(token, salt='password-reset', max_age=3600)
    except Exception:
        flash('Reset link is invalid or expired.', 'error')
        return redirect(url_for('auth.forgot_password'))
    user = User.query.filter_by(email=email).first()
    if not user:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
        flash('Password updated! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)

# ---------- VERIFY EMAIL ----------
@auth_bp.route('/verify/<token>')
def verify_email(token):
    try:
        email = get_serializer().loads(token, salt='email-verify', max_age=86400)
    except Exception:
        flash('Verification link expired.', 'error')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()
        flash('Email verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))