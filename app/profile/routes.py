from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.extensions import db, cache
from app.models import User, Interests, Friends, FriendRequest, Notification
from app.recommend.engine import recommend_friends, suggest_mutual_friends, INTEREST_FIELDS
from werkzeug.utils import secure_filename
import os

profile_bp = Blueprint('profile', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@profile_bp.route('/interests', methods=['GET', 'POST'])
def interests():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        data = request.form
        user_id = session['user_id']
        existing = Interests.query.filter_by(user_id=user_id).first()
        fields = {f: int(data.get(f, 0)) for f in INTEREST_FIELDS}
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
        else:
            db.session.add(Interests(user_id=user_id, **fields))
        db.session.commit()
        cache.delete_memoized(recommend_friends, user_id)
        user = User.query.get(user_id)
        return redirect(url_for('profile.view_profile', username=user.username))
    user = User.query.get(session['user_id'])
    existing = Interests.query.filter_by(user_id=user.id).first()
    return render_template('profile/interests.html', user=user,
                           interests=existing, fields=INTEREST_FIELDS)

@profile_bp.route('/<username>')
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_user_id = session.get('user_id')
    is_own_profile = current_user_id == user.id

    followers = (db.session.query(User)
                 .join(Friends, Friends.user_id == User.id)
                 .filter(Friends.friend_id == user.id).all())
    following = (db.session.query(User)
                 .join(Friends, Friends.friend_id == User.id)
                 .filter(Friends.user_id == user.id).all())

    is_friend = False
    pending_request = None
    if current_user_id and not is_own_profile:
        is_friend = Friends.query.filter_by(
            user_id=current_user_id, friend_id=user.id).first() is not None
        pending_request = FriendRequest.query.filter_by(
            sender_id=current_user_id, receiver_id=user.id).first()

    notifications = []
    incoming_requests = []
    if is_own_profile and current_user_id:
        notifications = (Notification.query
                         .filter_by(user_id=current_user_id, is_read=False)
                         .order_by(Notification.created_at.desc()).limit(10).all())
        incoming_requests = (db.session.query(FriendRequest, User)
                             .join(User, User.id == FriendRequest.sender_id)
                             .filter(FriendRequest.receiver_id == current_user_id,
                                     FriendRequest.status == 'pending').all())

    recs = recommend_friends(user.id) if is_own_profile else []
    mutuals = suggest_mutual_friends(user.id) if is_own_profile else []
    interests = Interests.query.filter_by(user_id=user.id).first()

    return render_template('profile/profile.html',
                           user=user,
                           interests=interests,
                           interest_fields=INTEREST_FIELDS,
                           followers=followers,
                           following=following,
                           is_own_profile=is_own_profile,
                           is_friend=is_friend,
                           pending_request=pending_request,
                           recommendations=recs[:6],
                           mutual_suggestions=mutuals[:6],
                           notifications=notifications,
                           incoming_requests=incoming_requests)

@profile_bp.route('/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    user.name     = request.form.get('name', user.name).strip()
    user.bio      = request.form.get('bio', '').strip()
    user.location = request.form.get('location', '').strip()
    file = request.files.get('profile_picture')
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        user.profile_picture = url_for('static', filename=f'uploads/{filename}')
    db.session.commit()
    flash('Profile updated!', 'success')
    return redirect(url_for('profile.view_profile', username=user.username))

@profile_bp.route('/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify(message='Marked as read')