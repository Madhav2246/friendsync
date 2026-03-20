from flask import Blueprint, request, redirect, url_for, session, jsonify
from app.extensions import db
from app.models import User, Friends, FriendRequest, Notification

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/send-request/<int:receiver_id>', methods=['POST'])
def send_request(receiver_id):
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    sender_id = session['user_id']
    if FriendRequest.query.filter_by(sender_id=sender_id, receiver_id=receiver_id).first():
        return jsonify(message='Request already sent'), 200
    if Friends.query.filter_by(user_id=sender_id, friend_id=receiver_id).first():
        return jsonify(message='Already friends'), 200
    req = FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
    db.session.add(req)
    sender = User.query.get(sender_id)
    notif = Notification(
        user_id=receiver_id,
        type='friend_request',
        content=f'{sender.name} sent you a friend request',
        link=url_for('profile.view_profile', username=sender.username)
    )
    db.session.add(notif)
    db.session.commit()
    return jsonify(message='Request sent')

@friends_bp.route('/accept/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    freq = FriendRequest.query.get_or_404(request_id)
    if freq.receiver_id != session['user_id']:
        return jsonify(error='Forbidden'), 403

    sender_id   = freq.sender_id
    receiver_id = freq.receiver_id

    # Check both directions before inserting
    if not Friends.query.filter_by(user_id=sender_id, friend_id=receiver_id).first():
        db.session.add(Friends(user_id=sender_id, friend_id=receiver_id))

    if not Friends.query.filter_by(user_id=receiver_id, friend_id=sender_id).first():
        db.session.add(Friends(user_id=receiver_id, friend_id=sender_id))

    db.session.delete(freq)

    receiver_name = User.query.get(receiver_id).name
    notif = Notification(
        user_id=sender_id,
        type='friend_accepted',
        content=f'{receiver_name} accepted your friend request'
    )
    db.session.add(notif)
    db.session.commit()

    user = User.query.get(session['user_id'])
    return redirect(url_for('profile.view_profile', username=user.username))

@friends_bp.route('/decline/<int:request_id>', methods=['POST'])
def decline_request(request_id):
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    freq = FriendRequest.query.get_or_404(request_id)
    if freq.receiver_id != session['user_id']:
        return jsonify(error='Forbidden'), 403
    db.session.delete(freq)
    db.session.commit()
    return jsonify(message='Request declined')

@friends_bp.route('/remove/<int:friend_id>', methods=['POST'])
def remove_friend(friend_id):
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    user_id = session['user_id']
    Friends.query.filter_by(user_id=user_id, friend_id=friend_id).delete()
    Friends.query.filter_by(user_id=friend_id, friend_id=user_id).delete()
    db.session.commit()
    return jsonify(message='Friend removed')