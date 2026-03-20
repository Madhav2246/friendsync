# FriendSync 🤝✨

> **AI-powered friend discovery platform built for Gen Z.**
> Stop scrolling, start connecting — with people who actually *get* you.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=flat-square&logo=flask)
![SocketIO](https://img.shields.io/badge/SocketIO-Realtime-purple?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📱 Device Support

| Device | Support |
|---|---|
| 💻 Laptop / Desktop | ✅ Fully supported |
| 📱 Tablet (landscape) | ✅ Fully supported |
| 📱 Tablet (portrait) | ⚠️ Works, recommended landscape |
| 📱 Mobile | 🔄 Please rotate to landscape for best experience |

> **FriendSync is optimized for laptop and tablet screens.**
> If you're on mobile, rotate your device to landscape mode for the full experience.
> A mobile-first version is coming soon. 🚀

---

## 🧠 What is FriendSync?

FriendSync is a **social discovery app** that uses machine learning to match you with people based on your actual interests — not your follower count. No cringe cold DMs, no awkward "hey" messages. Just genuine connections built through fun, low-pressure experiences.

Built specifically for **Gen Z** — the generation that wants real connection but hates the pressure of traditional social apps.

---

## ✨ Features

### 🤖 AI-Powered Matching
- **Cosine Similarity** engine compares your interest profile with everyone else
- **KMeans Clustering** groups users by interest patterns at scale
- **Dijkstra's Algorithm** finds shortest interest-path connections
- Recommendations get smarter every time you interact

### 🌟 Daily Twin
Every day at midnight, AI picks your **single closest match** from users you haven't connected with yet.
- Their identity is hidden — mystery first, connection second
- Send an anonymous 👋 wave
- If they wave back → profiles reveal automatically + friend request sent
- New twin every 24 hours

### 🃏 This or That (Swipe Cards)
Tinder-style swipe cards — but for **interests, not people**.
- 20 cards across all interest categories
- Each swipe silently updates your interest profile
- Every 5 swipes → milestone popup shows 3 new matches who think like you
- Drag or tap — full touch support
- Streak counter to keep you hooked

### 👻 Vibe Check
Anonymous 3-question exchange before you reveal who you are.
- System sends both users the same 3 random questions independently
- Match 2 out of 3 answers → profiles reveal + auto friend request
- Full anonymity until mutual match
- Status flow: pending → waiting → matched / unmatched

### 💬 Real-time Chat
- Powered by Flask-SocketIO
- Live typing indicators
- Read receipts
- **👻 Ephemeral mode** — messages vanish after 60 seconds (not saved)

### 👤 Interest Profiles
- 12 interest categories: Sports, Movies, Dance, Music, Education, Travel, Books, Cooking, Art, Gaming, Fitness, Technology
- Slider-based interest levels (0–5)
- Interest profile auto-updates from swipe behavior

### 🔔 Smart Notifications
- Friend requests, vibe check alerts, daily twin waves, match results
- Direct deep-links to relevant pages

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.0, Python 3.11 |
| Database | SQLite + SQLAlchemy ORM |
| Realtime | Flask-SocketIO + Eventlet |
| ML Engine | scikit-learn (KMeans, Cosine Similarity), NumPy |
| Auth | Flask-Bcrypt, Flask-Session |
| Email | Flask-Mail (Gmail SMTP) |
| Rate Limiting | Flask-Limiter |
| Caching | Flask-Caching (SimpleCache) |
| Frontend | Jinja2, Custom CSS (dark UI, CSS variables) |
| Fonts | Syne + DM Sans (Google Fonts) |
| Deployment | Render.com + Gunicorn |

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
- Python 3.11+
- Git

### 1. Clone the repo
```bash
git clone https://github.com/Madhav2246/friendsync.git
cd friendsync
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```
Edit `.env` and fill in:
```env
SECRET_KEY=your-secret-key-here
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

> For Gmail, use an **App Password** (not your regular password).
> Generate one at: myaccount.google.com → Security → App Passwords

### 5. Run the app
```bash
python run.py
```

Visit `http://127.0.0.1:3000`

### 6. (Optional) Seed fake users for testing
```bash
python -c "
from app import create_app
from app.extensions import db, bcrypt
from app.models import User, Interests
import random

app = create_app()
users = [
    ('Arjun Sharma','arjun_sharma','arjun@test.com'),
    ('Priya Patel','priya_patel','priya@test.com'),
    ('Rahul Verma','rahul_verma','rahul@test.com'),
    ('Sneha Reddy','sneha_reddy','sneha@test.com'),
    ('Karthik Nair','karthik_nair','karthik@test.com'),
]
pw = bcrypt.generate_password_hash('Test@1234').decode('utf-8')
fields = ['sports','movies','dance','songs','education','travel','books','cooking','art','gaming','fitness','technology']
with app.app_context():
    for name, username, email in users:
        if not User.query.filter_by(username=username).first():
            u = User(name=name, username=username, email=email, password_hash=pw)
            db.session.add(u)
            db.session.flush()
            db.session.add(Interests(user_id=u.id, **{f: random.randint(0,5) for f in fields}))
    db.session.commit()
    print('Done!')
"
```
All test accounts use password: `Test@1234`

---

## 📁 Project Structure

```
friendsync/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask extensions
│   ├── models.py            # Database models
│   ├── auth/                # Login, register, forgot password
│   ├── profile/             # Profile, interests, notifications
│   ├── friends/             # Friend requests, accept, decline
│   ├── recommend/           # AI engine, explore, daily twin
│   │   └── engine.py        # ML recommendation logic
│   ├── chat/                # Real-time chat with SocketIO
│   ├── swipe/               # This or That swipe cards
│   ├── vibe/                # Vibe Check anonymous exchange
│   ├── static/
│   │   └── uploads/         # Profile picture uploads
│   └── templates/           # Jinja2 HTML templates
├── flask_sessions/          # Server-side session storage
├── instance/
│   └── friends.db           # SQLite database
├── run.py                   # App entry point
├── requirements.txt
├── render.yaml              # Render deployment config
├── .env.example
└── .gitignore
```

---

## 🗄️ Database Models

| Model | Description |
|---|---|
| `User` | Core user profile, auth, online status |
| `Interests` | 12-category interest scores per user |
| `Friends` | Bidirectional friendship records |
| `FriendRequest` | Pending friend requests with status |
| `Message` | Chat messages with room, read status |
| `Notification` | Activity notifications with deep-link |
| `DailyMatch` | Today's AI twin match per user |
| `SwipeCard` | Swipe history for interest updates |
| `VibeCheck` | Anonymous vibe check sessions |
| `VibeAnswer` | Per-user answers for a vibe check |

---

## 🧬 ML Engine

Located in `app/recommend/engine.py`:

```
recommend_friends()     → Cosine similarity (< 30 users) or KMeans (≥ 30 users)
suggest_mutual_friends()→ Collaborative filtering on friend graph
dijkstra_suggestions()  → Shortest interest-path between users
get_daily_twin()        → Single closest match per day, cached in DB
```

Recommendations are cached for 300s and invalidated on every swipe or interest update.

---

## 🌐 Deployment

Deployed on **Render.com** using Gunicorn + Eventlet for WebSocket support.

Start command:
```bash
gunicorn -k eventlet -w 1 --bind 0.0.0.0:$PORT "app:create_app()"
```

Environment variables needed on Render:
```
SECRET_KEY
MAIL_USERNAME
MAIL_PASSWORD
```

> ⚠️ Render free tier has an ephemeral filesystem.
> Profile picture uploads will reset on redeploy.
> Upgrade to Cloudinary for persistent image storage.

---

## 🔒 Privacy by Design

Every Gen Z feature was built with privacy as a hard constraint:

- Identities hidden until **mutual consent** (Daily Twin wave, Vibe Check match)
- Vibe Check is **fully anonymous** until 2/3 question match
- Ephemeral chat mode — messages **never saved**, auto-delete in 60s
- No location data used anywhere
- No third-party ad tracking
- All Gen Z features are **opt-in only**
- Rate limiting on auth routes to prevent brute force

---

## 🗺️ Roadmap

- [ ] Interest-based group chat rooms (24h auto-purge)
- [ ] Icebreaker mini-games on shared interests
- [ ] Interest leaderboards (weekly reset)
- [ ] Cloudinary integration for persistent image uploads
- [ ] Mobile-first responsive redesign
- [ ] Push notifications (PWA)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, open an issue first.

1. Fork the repo
2. Create your branch: `git checkout -b feature/cool-thing`
3. Commit: `git commit -m 'Add cool thing'`
4. Push: `git push origin feature/cool-thing`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Built By

**Madhav** — built with Flask, a lot of caffeine, and genuine frustration with how hard it is to make real friends online. ☕

---

*FriendSync — Because your next best friend is out there, they just haven't found you yet.*
