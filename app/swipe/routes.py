from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.extensions import db, cache
from app.models import User, Interests, SwipeCard
from app.recommend.engine import INTEREST_FIELDS, recommend_friends
import random

swipe_bp = Blueprint('swipe', __name__)

CARDS = [
    {"id": "s1",  "field": "sports",     "a": "⚽ Football",     "b": "🏏 Cricket",       "label": "Your Sport"},
    {"id": "s2",  "field": "fitness",    "a": "🏋️ Gym",           "b": "🧘 Yoga",           "label": "Workout Style"},
    {"id": "m1",  "field": "movies",     "a": "🎬 Action",        "b": "💕 Romance",        "label": "Movie Mood"},
    {"id": "m2",  "field": "movies",     "a": "😂 Comedy",        "b": "😱 Thriller",       "label": "Tonight's Pick"},
    {"id": "mu1", "field": "songs",      "a": "🎧 Lo-fi",         "b": "🎸 Rock",           "label": "Music Vibe"},
    {"id": "mu2", "field": "songs",      "a": "🎤 Bollywood",     "b": "🌍 Western Pop",    "label": "Playlist"},
    {"id": "b1",  "field": "books",      "a": "📖 Fiction",       "b": "🔬 Non-fiction",    "label": "Reading Pick"},
    {"id": "b2",  "field": "education",  "a": "🎓 Online Course", "b": "📚 Self-reading",   "label": "How You Learn"},
    {"id": "t1",  "field": "travel",     "a": "🏔️ Mountains",     "b": "🏖️ Beach",          "label": "Getaway"},
    {"id": "t2",  "field": "travel",     "a": "🌆 City Trip",     "b": "🌿 Nature Escape",  "label": "Travel Style"},
    {"id": "c1",  "field": "cooking",    "a": "🍕 Order In",      "b": "🍳 Cook at Home",   "label": "Dinner Plan"},
    {"id": "c2",  "field": "cooking",    "a": "🌶️ Spicy",         "b": "🍰 Sweet",          "label": "Food Preference"},
    {"id": "a1",  "field": "art",        "a": "🎨 Drawing",       "b": "📸 Photography",    "label": "Creative Side"},
    {"id": "g1",  "field": "gaming",     "a": "🎮 Console",       "b": "📱 Mobile Games",   "label": "Gaming Setup"},
    {"id": "g2",  "field": "gaming",     "a": "🧩 Puzzle",        "b": "⚔️ RPG",            "label": "Game Genre"},
    {"id": "te1", "field": "technology", "a": "🤖 AI and ML",     "b": "🔐 Cybersecurity",  "label": "Tech Interest"},
    {"id": "d1",  "field": "dance",      "a": "💃 Classical",     "b": "🕺 Hip-hop",        "label": "Dance Style"},
    {"id": "l1",  "field": "sports",     "a": "🌅 Morning Person","b": "🌙 Night Owl",      "label": "Daily Rhythm"},
    {"id": "l2",  "field": "travel",     "a": "🗺️ Plan Everything","b": "🎲 Spontaneous",   "label": "Travel Approach"},
    {"id": "l3",  "field": "education",  "a": "🤫 Introvert",     "b": "🎉 Extrovert",      "label": "Social Energy"},
]

@swipe_bp.route('/')
def swipe():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])

    # Get already swiped card IDs this session
    swiped = session.get('swiped_cards', [])

    # Pass ALL remaining cards to frontend — JS handles the queue
    remaining = [c for c in CARDS if c['id'] not in swiped]
    random.shuffle(remaining)

    return render_template('swipe/swipe.html',
                           user=user,
                           cards=remaining,
                           swipe_count=len(swiped),
                           total=len(CARDS))

@swipe_bp.route('/submit', methods=['POST'])
def submit_swipe():
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401

    data    = request.get_json()
    card_id = data.get('card_id')
    choice  = data.get('choice')

    card = next((c for c in CARDS if c['id'] == card_id), None)
    if not card or choice not in ('a', 'b'):
        return jsonify(error='Invalid card or choice'), 400

    user_id = session['user_id']
    field   = card['field']

    # Save swipe record
    db.session.add(SwipeCard(user_id=user_id, field=field, choice=choice))

    # Silently boost interest level (cap at 5)
    interests = Interests.query.filter_by(user_id=user_id).first()
    if interests and hasattr(interests, field):
        current = getattr(interests, field, 0) or 0
        setattr(interests, field, min(current + 1, 5))

    db.session.commit()

    # Track in session
    swiped = session.get('swiped_cards', [])
    if card_id not in swiped:
        swiped.append(card_id)
    session['swiped_cards'] = swiped
    session.modified = True

    # Invalidate recommendation cache
    cache.delete_memoized(recommend_friends, user_id)

    # Every 5 swipes return fresh recommendations
    recs = []
    if len(swiped) % 5 == 0:
        try:
            recs = recommend_friends(user_id)[:3]
        except Exception:
            recs = []

    return jsonify(
        success=True,
        swipe_count=len(swiped),
        total=len(CARDS),
        milestone=(len(swiped) % 5 == 0),
        recommendations=recs
    )

@swipe_bp.route('/reset', methods=['POST'])
def reset_swipes():
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    session['swiped_cards'] = []
    session.modified = True
    return jsonify(success=True)