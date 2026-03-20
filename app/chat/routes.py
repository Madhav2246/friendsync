from flask import Blueprint, render_template, session, redirect, url_for
from flask_socketio import emit, join_room, leave_room
from app.extensions import db, socketio
from app.models import User, Message, Notification, Friends
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<int:friend_id>')
def chat(friend_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    friend = User.query.get_or_404(friend_id)
    room_id = "_".join(sorted([str(session['user_id']), str(friend_id)]))
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at).limit(100).all()
    # Mark as read
    Message.query.filter_by(room_id=room_id, is_read=False).filter(
        Message.sender_id != session['user_id']
    ).update({'is_read': True})
    db.session.commit()
    current_user = User.query.get(session['user_id'])
    return render_template('chat/chat.html',
                           friend=friend,
                           room_id=room_id,
                           messages=messages,
                           current_user=current_user)

@chat_bp.route('/list')
def chat_list():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    friends = (db.session.query(User)
               .join(Friends, Friends.friend_id == User.id)
               .filter(Friends.user_id == user_id).all())
    conversations = []
    for friend in friends:
        room_id = "_".join(sorted([str(user_id), str(friend.id)]))
        last_msg = (Message.query
                    .filter_by(room_id=room_id)
                    .order_by(Message.created_at.desc())
                    .first())
        unread = (Message.query
                  .filter_by(room_id=room_id, is_read=False)
                  .filter(Message.sender_id != user_id)
                  .count())
        conversations.append({
            'friend': friend,
            'last_message': last_msg,
            'unread': unread
        })
    conversations.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min,
        reverse=True
    )
    current_user = User.query.get(user_id)
    return render_template('chat/chat_list.html',
                           conversations=conversations,
                           current_user=current_user)

# ── Socket events ─────────────────────────────────────────────
@socketio.on('join')
def handle_join(data):
    join_room(data['room_id'])

@socketio.on('leave')
def handle_leave(data):
    leave_room(data['room_id'])

@socketio.on('send_message')
def handle_message(data):
    if 'user_id' not in session:
        return
    room_id   = data['room_id']
    content   = data.get('message', '').strip()
    ephemeral = data.get('ephemeral', False)
    if not content:
        return
    sender_id = session['user_id']

    # Only save to DB if NOT ephemeral
    msg_id = None
    if not ephemeral:
        msg = Message(room_id=room_id, sender_id=sender_id, content=content)
        db.session.add(msg)
        # Notification for receiver
        parts = room_id.split('_')
        receiver_id = int(parts[0]) if int(parts[1]) == sender_id else int(parts[1])
        notif = Notification(
            user_id=receiver_id,
            type='message',
            content=f'New message from {User.query.get(sender_id).name}'
        )
        db.session.add(notif)
        db.session.commit()
        msg_id = msg.id

    emit('receive_message', {
        'sender_id': sender_id,
        'message':   content,
        'timestamp': datetime.utcnow().strftime('%H:%M'),
        'ephemeral': ephemeral,
        'msg_id':    msg_id,
        'sender_name': User.query.get(sender_id).name
    }, room=room_id)

@socketio.on('typing')
def handle_typing(data):
    emit('user_typing', {'user_id': session.get('user_id')},
         room=data['room_id'], include_self=False)

@socketio.on('stopped_typing')
def handle_stopped_typing(data):
    emit('user_stopped_typing', {}, room=data['room_id'], include_self=False)