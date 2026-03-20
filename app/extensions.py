from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

db = SQLAlchemy()
migrate = Migrate()
sess = Session()
mail = Mail()
bcrypt = Bcrypt()
socketio = SocketIO()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)