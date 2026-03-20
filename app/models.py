from app.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    username      = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email         = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(300), nullable=True)
    bio           = db.Column(db.String(300), nullable=True)
    location      = db.Column(db.String(100), nullable=True)
    is_verified   = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen     = db.Column(db.DateTime, default=datetime.utcnow)
    is_online     = db.Column(db.Boolean, default=False)

class Interests(db.Model):
    __tablename__ = 'interests'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    sports     = db.Column(db.Integer, default=0)
    movies     = db.Column(db.Integer, default=0)
    dance      = db.Column(db.Integer, default=0)
    songs      = db.Column(db.Integer, default=0)
    education  = db.Column(db.Integer, default=0)
    travel     = db.Column(db.Integer, default=0)
    books      = db.Column(db.Integer, default=0)
    cooking    = db.Column(db.Integer, default=0)
    art        = db.Column(db.Integer, default=0)
    gaming     = db.Column(db.Integer, default=0)
    fitness    = db.Column(db.Integer, default=0)
    technology = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Friends(db.Model):
    __tablename__ = 'friends'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id'),)

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status      = db.Column(db.String(10), default='pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id         = db.Column(db.Integer, primary_key=True)
    room_id    = db.Column(db.String(50), nullable=False, index=True)
    sender_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type       = db.Column(db.String(50), nullable=False)  # 'friend_request', 'message', 'recommendation'
    content    = db.Column(db.String(300), nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link       = db.Column(db.String(200), nullable=True)
class DailyMatch(db.Model):
    __tablename__ = 'daily_matches'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    match_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score      = db.Column(db.Float, nullable=False)
    date       = db.Column(db.Date, default=datetime.utcnow().date)
    revealed   = db.Column(db.Boolean, default=False)
    waved      = db.Column(db.Boolean, default=False)
class SwipeCard(db.Model):
    __tablename__ = 'swipe_cards'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    field      = db.Column(db.String(50), nullable=False)
    choice     = db.Column(db.String(10), nullable=False)  # 'a' or 'b'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class VibeCheck(db.Model):
    __tablename__ = 'vibe_checks'
    id           = db.Column(db.Integer, primary_key=True)
    sender_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status       = db.Column(db.String(20), default='pending')
    # pending → answered → matched / unmatched
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class VibeAnswer(db.Model):
    __tablename__ = 'vibe_answers'
    id             = db.Column(db.Integer, primary_key=True)
    vibe_check_id  = db.Column(db.Integer, db.ForeignKey('vibe_checks.id'), nullable=False, index=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    q1             = db.Column(db.String(10), nullable=False)
    q2             = db.Column(db.String(10), nullable=False)
    q3             = db.Column(db.String(10), nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)