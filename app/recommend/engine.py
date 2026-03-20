import numpy as np
import heapq
import logging
from collections import defaultdict
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from app.models import User, Interests, Friends
from app.extensions import cache

logger = logging.getLogger(__name__)

INTEREST_FIELDS = [
    'sports', 'movies', 'dance', 'songs', 'education',
    'travel', 'books', 'cooking', 'art', 'gaming', 'fitness', 'technology'
]

def _build_interest_matrix():
    """Build numpy matrix of all user interests."""
    all_interests = Interests.query.all()
    if not all_interests:
        return np.array([]), [], []
    data = np.array([[getattr(i, f) for f in INTEREST_FIELDS] for i in all_interests])
    user_ids = [i.user_id for i in all_interests]
    return data, user_ids, all_interests

@cache.memoize(timeout=300)
def recommend_friends(user_id, category=None):
    """
    Hybrid recommendation: cosine similarity (<30 users) or KMeans (>=30).
    Returns list of dicts: {id, name, score, reason}
    """
    data, user_ids, _ = _build_interest_matrix()
    if len(data) == 0 or user_id not in user_ids:
        return []

    user_index = user_ids.index(user_id)
    existing_friends = {f.friend_id for f in Friends.query.filter_by(user_id=user_id).all()}
    existing_friends.add(user_id)

    if category and category in INTEREST_FIELDS:
        cat_idx = INTEREST_FIELDS.index(category)
        mask = np.where(data[:, cat_idx] > 0)[0]
        if len(mask) == 0:
            return []
        nn = NearestNeighbors(n_neighbors=min(len(mask), 10), metric='cosine')
        nn.fit(data[mask])
        distances, indices = nn.kneighbors([data[user_index]])
        recommended = []
        for dist, i in zip(distances[0], indices[0]):
            uid = user_ids[mask[i]]
            if uid not in existing_friends:
                user = User.query.get(uid)
                if user:
                    recommended.append({
                        'id': uid, 'name': user.name,
                        'username': user.username,
                        'profile_picture': user.profile_picture,
                        'score': round((1 - dist) * 100, 1),
                        'reason': f'Shares interest in {category}'
                    })
        return recommended

    if len(data) <= 30:
        similarity_scores = cosine_similarity([data[user_index]], data)[0]
        ranked = np.argsort(similarity_scores)[::-1]
        recommended = []
        for i in ranked[1:21]:
            uid = user_ids[i]
            if uid not in existing_friends:
                user = User.query.get(uid)
                if user:
                    recommended.append({
                        'id': uid, 'name': user.name,
                        'username': user.username,
                        'profile_picture': user.profile_picture,
                        'score': round(similarity_scores[i] * 100, 1),
                        'reason': 'Similar interests across all categories'
                    })
        return recommended
    else:
        n_clusters = min(len(data), 5)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(data)
        user_cluster = clusters[user_index]
        recommended = []
        for i, cluster in enumerate(clusters):
            if cluster == user_cluster and user_ids[i] not in existing_friends:
                user = User.query.get(user_ids[i])
                sim = cosine_similarity([data[user_index]], [data[i]])[0][0]
                if user:
                    recommended.append({
                        'id': user_ids[i], 'name': user.name,
                        'username': user.username,
                        'profile_picture': user.profile_picture,
                        'score': round(sim * 100, 1),
                        'reason': 'In the same interest cluster'
                    })
        return sorted(recommended, key=lambda x: -x['score'])


def suggest_mutual_friends(user_id):
    """Greedy mutual friend suggestions with collaborative filtering score."""
    user_friends = {f.friend_id for f in Friends.query.filter_by(user_id=user_id).all()}
    user_interests = Interests.query.filter_by(user_id=user_id).first()
    mutual_counts = defaultdict(int)
    for friend_id in user_friends:
        for f in Friends.query.filter_by(user_id=friend_id).all():
            if f.friend_id != user_id and f.friend_id not in user_friends:
                mutual_counts[f.friend_id] += 1
    results = []
    for uid, count in sorted(mutual_counts.items(), key=lambda x: -x[1])[:20]:
        user = User.query.get(uid)
        if not user:
            continue
        score = count
        if user_interests:
            their_interests = Interests.query.filter_by(user_id=uid).first()
            if their_interests:
                similarity = sum(
                    abs(getattr(user_interests, f) - getattr(their_interests, f))
                    for f in INTEREST_FIELDS
                )
                score += 1 / (1 + similarity)
        results.append({
            'id': uid, 'name': user.name,
            'username': user.username,
            'profile_picture': user.profile_picture,
            'score': round(score, 2),
            'mutual_count': count,
            'reason': f'{count} mutual friend{"s" if count > 1 else ""}'
        })
    return results


def dijkstra_suggestions(user_id, category):
    """Dijkstra-based category similarity recommendations."""
    if category not in INTEREST_FIELDS:
        return []
    user_interests = Interests.query.filter_by(user_id=user_id).first()
    if not user_interests:
        return []
    existing_friends = {f.friend_id for f in Friends.query.filter_by(user_id=user_id).all()}
    existing_friends.add(user_id)
    all_interests = Interests.query.all()
    graph = defaultdict(list)
    for u in all_interests:
        if u.user_id != user_id:
            weight = abs(getattr(user_interests, category) - getattr(u, category))
            graph[user_id].append((u.user_id, weight))
    pq = [(0, user_id)]
    distances = {user_id: 0}
    while pq:
        dist, curr = heapq.heappop(pq)
        for neighbor, weight in graph[curr]:
            d = dist + weight
            if neighbor not in distances or d < distances[neighbor]:
                distances[neighbor] = d
                heapq.heappush(pq, (d, neighbor))
    results = []
    for uid, dist in sorted(distances.items(), key=lambda x: x[1]):
        if uid == user_id or uid in existing_friends:
            continue
        user = User.query.get(uid)
        if user:
            results.append({
                'id': uid, 'name': user.name,
                'username': user.username,
                'profile_picture': user.profile_picture,
                'score': round(max(0, 100 - dist * 10), 1),
                'reason': f'Close match in {category}'
            })
    return results[:20]

from datetime import date as date_type

def get_daily_twin(user_id):
    """Find the single closest interest match for today."""
    from app.models import DailyMatch
    today = date_type.today()

    # Return cached match if already computed today
    existing = DailyMatch.query.filter_by(user_id=user_id, date=today).first()
    if existing:
        match_user = User.query.get(existing.match_id)
        return {
            'match_id':   existing.match_id,
            'name':       match_user.name if existing.revealed else None,
            'username':   match_user.username if existing.revealed else None,
            'profile_picture': match_user.profile_picture if existing.revealed else None,
            'score':      existing.score,
            'revealed':   existing.revealed,
            'waved':      existing.waved,
            'match_db_id': existing.id
        }

    # Build interest matrix
    data, user_ids, all_interests = _build_interest_matrix()
    if len(data) == 0 or user_id not in user_ids:
        return None

    user_index = user_ids.index(user_id)
    existing_friends = {f.friend_id for f in Friends.query.filter_by(user_id=user_id).all()}
    existing_friends.add(user_id)

    # Already matched today
    already_matched = {
        m.match_id for m in DailyMatch.query.filter_by(user_id=user_id).all()
    }
    existing_friends.update(already_matched)

    # Cosine similarity
    similarity_scores = cosine_similarity([data[user_index]], data)[0]
    ranked = np.argsort(similarity_scores)[::-1]

    best_id    = None
    best_score = 0.0
    for i in ranked[1:]:
        uid = user_ids[i]
        if uid not in existing_friends:
            best_id    = uid
            best_score = round(similarity_scores[i] * 100, 1)
            break

    if not best_id:
        return None

    # Save to DB
    from app.extensions import db
    match = DailyMatch(user_id=user_id, match_id=best_id, score=best_score, date=today)
    db.session.add(match)
    db.session.commit()

    return {
        'match_id':    best_id,
        'name':        None,
        'username':    None,
        'profile_picture': None,
        'score':       best_score,
        'revealed':    False,
        'waved':       False,
        'match_db_id': match.id
    }