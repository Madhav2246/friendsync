from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.extensions import db
from app.models import User, VibeCheck, VibeAnswer, FriendRequest, Notification, Friends
import random

vibe_bp = Blueprint('vibe', __name__)

QUESTIONS = [
    {"id": "q1",  "text": "Morning person or night owl?",   "a": "🌅 Morning",    "b": "🌙 Night Owl"},
    {"id": "q2",  "text": "Mountains or beach?",            "a": "🏔️ Mountains",  "b": "🏖️ Beach"},
    {"id": "q3",  "text": "Introvert or extrovert?",        "a": "🤫 Introvert",  "b": "🎉 Extrovert"},
    {"id": "q4",  "text": "Coffee or tea?",                 "a": "☕ Coffee",      "b": "🍵 Tea"},
    {"id": "q5",  "text": "Movies or series?",              "a": "🎬 Movies",      "b": "📺 Series"},
    {"id": "q6",  "text": "Plan ahead or spontaneous?",     "a": "📋 Planner",     "b": "🎲 Spontaneous"},
    {"id": "q7",  "text": "Stay in or go out?",             "a": "🏠 Stay In",     "b": "🌆 Go Out"},
    {"id": "q8",  "text": "Cats or dogs?",                  "a": "🐱 Cats",        "b": "🐶 Dogs"},
    {"id": "q9",  "text": "Read or listen to music?",       "a": "📖 Read",        "b": "🎵 Music"},
    {"id": "q10", "text": "Fast food or home cooked?",      "a": "🍔 Fast Food",   "b": "🍳 Home Cooked"},
    {"id": "q11", "text": "City life or village life?",     "a": "🌆 City",        "b": "🌿 Village"},
    {"id": "q12", "text": "Spicy food or mild food?",       "a": "🌶️ Spicy",      "b": "🥛 Mild"},
    {"id": "q13", "text": "Early bird or deadline rusher?", "a": "✅ Early Bird",  "b": "⏰ Last Minute"},
    {"id": "q14", "text": "Text or call?",                  "a": "💬 Text",        "b": "📞 Call"},
    {"id": "q15", "text": "Summer or winter?",              "a": "☀️ Summer",      "b": "❄️ Winter"},
]


def get_questions_for_vibe(vibe_id):
    rng = random.Random(vibe_id * 31337)
    return rng.sample(QUESTIONS, 3)


def _notify(user_id, type_, content, link):
    try:
        n = Notification(user_id=user_id, type=type_, content=content)
        if hasattr(n, 'link'):
            n.link = link
        db.session.add(n)
    except Exception:
        pass


@vibe_bp.route('/')
def vibe_home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id    = session['user_id']
    user       = User.query.get(user_id)
    sent_by_me = VibeCheck.query.filter_by(sender_id=user_id).all()
    received   = VibeCheck.query.filter_by(receiver_id=user_id).all()

    my_pending = []
    for vc in received:
        if not VibeAnswer.query.filter_by(vibe_check_id=vc.id, user_id=user_id).first():
            my_pending.append((vc, User.query.get(vc.sender_id), 'received'))
    for vc in sent_by_me:
        if not VibeAnswer.query.filter_by(vibe_check_id=vc.id, user_id=user_id).first():
            my_pending.append((vc, User.query.get(vc.receiver_id), 'sent'))

    all_checks = []
    for vc in sent_by_me:
        other     = User.query.get(vc.receiver_id)
        my_ans    = VibeAnswer.query.filter_by(vibe_check_id=vc.id, user_id=user_id).first()
        other_ans = VibeAnswer.query.filter_by(vibe_check_id=vc.id).filter(VibeAnswer.user_id != user_id).first()
        all_checks.append((vc, other, my_ans, other_ans, 'sent'))
    for vc in received:
        other     = User.query.get(vc.sender_id)
        my_ans    = VibeAnswer.query.filter_by(vibe_check_id=vc.id, user_id=user_id).first()
        other_ans = VibeAnswer.query.filter_by(vibe_check_id=vc.id).filter(VibeAnswer.user_id != user_id).first()
        all_checks.append((vc, other, my_ans, other_ans, 'received'))
    all_checks.sort(key=lambda x: x[0].created_at, reverse=True)

    involved = (
        {vc.receiver_id for vc in sent_by_me} |
        {vc.sender_id   for vc in received}   |
        {f.friend_id for f in Friends.query.filter_by(user_id=user_id).all()} |
        {user_id}
    )
    suggestions = User.query.filter(User.id.notin_(involved)).order_by(db.func.random()).limit(6).all()

    return render_template('vibe/vibe_home.html',
                           user=user, my_pending=my_pending,
                           all_checks=all_checks, suggestions=suggestions)


@vibe_bp.route('/send/<int:receiver_id>', methods=['GET', 'POST'])
def send_vibe(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    sender_id = session['user_id']
    is_json   = request.is_json or request.method == 'POST'

    if sender_id == receiver_id:
        return (jsonify(error='Cannot send to yourself'), 400) if is_json else redirect(url_for('vibe.vibe_home'))

    existing = VibeCheck.query.filter_by(sender_id=sender_id, receiver_id=receiver_id).first()
    if existing:
        dest = (url_for('vibe.result_page', vibe_id=existing.id)
                if VibeAnswer.query.filter_by(vibe_check_id=existing.id, user_id=sender_id).first()
                else url_for('vibe.answer_page', vibe_id=existing.id))
        if is_json:
            return jsonify(success=True, answer_url=dest, already=True)
        return redirect(dest)

    try:
        vc = VibeCheck(sender_id=sender_id, receiver_id=receiver_id, status='pending')
        db.session.add(vc)
        db.session.flush()

        _notify(receiver_id, 'vibe_check',
                '👻 Someone wants to vibe check with you! Tap to answer 3 questions.',
                f'/vibe/answer/{vc.id}')

        db.session.commit()
        answer_url = url_for('vibe.answer_page', vibe_id=vc.id)

        if is_json:
            return jsonify(success=True, answer_url=answer_url)
        return redirect(answer_url)

    except Exception as e:
        db.session.rollback()
        if is_json:
            return jsonify(error=str(e)), 500
        return redirect(url_for('vibe.vibe_home'))


@vibe_bp.route('/answer/<int:vibe_id>', methods=['GET', 'POST'])
def answer_page(vibe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    vc      = VibeCheck.query.get_or_404(vibe_id)
    user_id = session['user_id']

    if user_id not in (vc.sender_id, vc.receiver_id):
        return redirect(url_for('vibe.vibe_home'))

    if VibeAnswer.query.filter_by(vibe_check_id=vibe_id, user_id=user_id).first():
        return redirect(url_for('vibe.result_page', vibe_id=vibe_id))

    questions = get_questions_for_vibe(vibe_id)
    user      = User.query.get(user_id)
    error     = None

    if request.method == 'POST':
        q1 = request.form.get('q1', '').strip()
        q2 = request.form.get('q2', '').strip()
        q3 = request.form.get('q3', '').strip()

        if not (q1 and q2 and q3):
            error = 'Please answer all 3 questions before submitting.'
        elif q1 not in ('a', 'b') or q2 not in ('a', 'b') or q3 not in ('a', 'b'):
            error = 'Invalid answer. Please select one option per question.'
        else:
            try:
                db.session.add(VibeAnswer(vibe_check_id=vibe_id, user_id=user_id, q1=q1, q2=q2, q3=q3))
                db.session.flush()

                other_id     = vc.sender_id if user_id == vc.receiver_id else vc.receiver_id
                other_answer = VibeAnswer.query.filter_by(vibe_check_id=vibe_id).filter(
                                   VibeAnswer.user_id != user_id).first()

                if other_answer:
                    matches   = sum([q1 == other_answer.q1, q2 == other_answer.q2, q3 == other_answer.q3])
                    vc.status = 'matched' if matches >= 2 else 'unmatched'
                    rlink     = f'/vibe/result/{vibe_id}'

                    if vc.status == 'matched':
                        if not Friends.query.filter_by(user_id=user_id, friend_id=other_id).first():
                            if not FriendRequest.query.filter_by(sender_id=user_id, receiver_id=other_id).first():
                                db.session.add(FriendRequest(sender_id=user_id, receiver_id=other_id))
                        _notify(other_id, 'vibe_matched', '🎉 You matched on Vibe Check!', rlink)
                        _notify(user_id,  'vibe_matched', '🎉 You matched on Vibe Check!', rlink)
                    else:
                        _notify(other_id, 'vibe_done', '👻 Vibe Check complete — see result.', rlink)
                        _notify(user_id,  'vibe_done', '👻 Vibe Check complete — see result.', rlink)
                else:
                    vc.status = 'waiting'
                    _notify(other_id, 'vibe_check',
                            '👻 Someone answered your Vibe Check — your turn!',
                            f'/vibe/answer/{vibe_id}')

                db.session.commit()
                return redirect(url_for('vibe.result_page', vibe_id=vibe_id))

            except Exception as e:
                db.session.rollback()
                error = f'Error saving answers: {str(e)}'

    return render_template('vibe/answer.html',
                           user=user, vc=vc, questions=questions, error=error)


@vibe_bp.route('/result/<int:vibe_id>')
def result_page(vibe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    vc      = VibeCheck.query.get_or_404(vibe_id)
    user_id = session['user_id']

    if user_id not in (vc.sender_id, vc.receiver_id):
        return redirect(url_for('vibe.vibe_home'))

    my_answer = VibeAnswer.query.filter_by(vibe_check_id=vibe_id, user_id=user_id).first()
    if not my_answer:
        return redirect(url_for('vibe.answer_page', vibe_id=vibe_id))

    other_answer = VibeAnswer.query.filter_by(vibe_check_id=vibe_id).filter(
                       VibeAnswer.user_id != user_id).first()

    questions   = get_questions_for_vibe(vibe_id)
    match_count = 0
    other_user  = None

    if other_answer:
        match_count = sum([
            my_answer.q1 == other_answer.q1,
            my_answer.q2 == other_answer.q2,
            my_answer.q3 == other_answer.q3,
        ])

    if vc.status == 'matched':
        other_id   = vc.sender_id if user_id == vc.receiver_id else vc.receiver_id
        other_user = User.query.get(other_id)

    user = User.query.get(user_id)
    return render_template('vibe/result.html',
                           user=user, vc=vc,
                           my_answer=my_answer,
                           other_answer=other_answer,
                           questions=questions,
                           other_user=other_user,
                           match_count=match_count)