from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.recommend.engine import recommend_friends, suggest_mutual_friends, dijkstra_suggestions, INTEREST_FIELDS, get_daily_twin
from app.models import User, Friends, DailyMatch
from app.extensions import db
from datetime import date as date_type
recommend_bp = Blueprint('recommend', __name__)

@recommend_bp.route('/explore')
def explore():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    category = request.args.get('category', '').lower()
    method   = request.args.get('method', 'hybrid')

    if method == 'mutual':
        recs = suggest_mutual_friends(session['user_id'])
    elif method == 'dijkstra' and category in INTEREST_FIELDS:
        recs = dijkstra_suggestions(session['user_id'], category)
    else:
        recs = recommend_friends(session['user_id'], category or None)

    already_friends = {f.friend_id for f in Friends.query.filter_by(user_id=session['user_id']).all()}
    for r in recs:
        r['is_friend'] = r['id'] in already_friends

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(recommendations=recs)

    return render_template('recommend/explore.html',
                           user=user,
                           recommendations=recs,
                           categories=INTEREST_FIELDS,
                           selected_category=category,
                           selected_method=method)
@recommend_bp.route('/daily-twin')
def daily_twin():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user  = User.query.get(session['user_id'])
    twin  = get_daily_twin(session['user_id'])
    return render_template('recommend/daily_twin.html', user=user, twin=twin)

@recommend_bp.route('/daily-twin/wave/<int:match_db_id>', methods=['POST'])
def wave_at_twin(match_db_id):
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    match = DailyMatch.query.get_or_404(match_db_id)
    if match.user_id != session['user_id']:
        return jsonify(error='Forbidden'), 403

    match.waved = True
    match.revealed = True

    # Check if the other person also waved at this user today
    their_match = DailyMatch.query.filter_by(
        user_id=match.match_id,
        match_id=session['user_id'],
        date=date_type.today()
    ).first()

    mutual = False
    if their_match and their_match.waved:
        mutual = True
        their_match.revealed = True
        # Send friend request automatically
        from app.models import FriendRequest, Notification
        if not FriendRequest.query.filter_by(
            sender_id=session['user_id'], receiver_id=match.match_id).first():
            db.session.add(FriendRequest(
                sender_id=session['user_id'],
                receiver_id=match.match_id
            ))
            sender = User.query.get(session['user_id'])
            db.session.add(Notification(
                user_id=match.match_id,
                type='daily_twin_match',
                content=f'🎉 You and {sender.name} both waved! You matched today!'
            ))

    db.session.commit()
    match_user = User.query.get(match.match_id)
    return jsonify(
        mutual=mutual,
        revealed=True,
        name=match_user.name,
        username=match_user.username
    )

@recommend_bp.route('/daily-twin/reveal/<int:match_db_id>', methods=['POST'])
def reveal_twin(match_db_id):
    if 'user_id' not in session:
        return jsonify(error='Unauthorized'), 401
    match = DailyMatch.query.get_or_404(match_db_id)
    if match.user_id != session['user_id']:
        return jsonify(error='Forbidden'), 403
    match.revealed = True
    db.session.commit()
    match_user = User.query.get(match.match_id)
    return jsonify(name=match_user.name, username=match_user.username,
                   profile_picture=match_user.profile_picture)