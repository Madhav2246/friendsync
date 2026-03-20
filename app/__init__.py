from flask import Flask, redirect
from app.config import Config
from app.extensions import db, migrate, sess, mail, bcrypt, socketio, cache, limiter
import os
from flask import session as flask_session
from app.models import User


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    # ── Ensure required folders exist (local + Render) ──────────────────────
    os.makedirs(os.path.join(app.root_path, '..', 'instance'),       exist_ok=True)
    os.makedirs(os.path.join(app.root_path, '..', 'flask_sessions'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads'),    exist_ok=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    sess.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app, manage_session=False, cors_allowed_origins="*")
    cache.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from app.auth.routes      import auth_bp
    from app.profile.routes   import profile_bp
    from app.friends.routes   import friends_bp
    from app.recommend.routes import recommend_bp
    from app.chat.routes      import chat_bp
    from app.swipe.routes     import swipe_bp
    from app.vibe.routes      import vibe_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(profile_bp,   url_prefix='/profile')
    app.register_blueprint(friends_bp,   url_prefix='/friends')
    app.register_blueprint(recommend_bp, url_prefix='/recommend')
    app.register_blueprint(chat_bp,      url_prefix='/chat')
    app.register_blueprint(swipe_bp,     url_prefix='/swipe')
    app.register_blueprint(vibe_bp,      url_prefix='/vibe')

    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return redirect('/auth/login')

    @app.context_processor
    def inject_current_user():
        user = None
        if 'user_id' in flask_session:
            user = User.query.get(flask_session['user_id'])
        return dict(current_user=user)

    return app