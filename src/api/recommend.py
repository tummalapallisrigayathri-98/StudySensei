# src/backend/recommend.py
"""
recommend_items(user_id, query, k)

Simple, interpretable recommendation function for StudySensi.
It returns a list of dicts:
  {'item_id', 'title', 'url', 'score', 'explanation'}

How it works (pipeline):
- Loads interactions from data/sample_interactions.csv (lightweight persistence)
- Loads resource catalog from data/resources.csv (URLs + tags + popularity)
- Computes:
    * tag match score between query and resource tags/title
    * popularity score (from interactions -> item completions)
    * user preference score based on user's past interactions (boost resources similar to items they completed)
    * recency bonus for items user interacted recently
- Combines scores (weighted sum) and returns top-k with explanation.

This is intentionally simple and fully local (no web calls).
"""

import os
import logging
import pandas as pd
import math
import time
from collections import defaultdict, Counter

# Configure module-level logger (main.py also logs)
logger = logging.getLogger("recommend")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Paths (relative to repo root)
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
INTERACTIONS_PATH = os.path.join(BASE_DIR, 'data', 'sample_interactions.csv')
RESOURCES_PATH = os.path.join(BASE_DIR, 'data', 'resources.csv')

# Small text helpers
def tokenize(s: str):
    if not isinstance(s, str):
        return []
    return [t.strip().lower() for t in s.split() if t.strip()]

def jaccard(a_tokens, b_tokens):
    if not a_tokens or not b_tokens:
        return 0.0
    a = set(a_tokens)
    b = set(b_tokens)
    return float(len(a & b)) / float(len(a | b))

# Loading helpers (cached)
_cached_interactions = None
_cached_resources = None

def load_interactions():
    global _cached_interactions
    if _cached_interactions is None:
        if os.path.exists(INTERACTIONS_PATH):
            try:
                df = pd.read_csv(INTERACTIONS_PATH, parse_dates=['timestamp'])
            except Exception:
                df = pd.read_csv(INTERACTIONS_PATH)
        else:
            # create empty dataframe if missing
            df = pd.DataFrame(columns=['user_id', 'item_id', 'event_type', 'timestamp'])
        _cached_interactions = df
    return _cached_interactions

def load_resources():
    """
    resources.csv columns:
      item_id,title,url,tags
    tags is pipe-separated: tag1|tag2|...
    """
    global _cached_resources
    if _cached_resources is None:
        if os.path.exists(RESOURCES_PATH):
            df = pd.read_csv(RESOURCES_PATH)
            # normalize tags into list
            df['tags_list'] = df['tags'].fillna('').apply(lambda s: [t.strip().lower() for t in str(s).split('|') if t.strip()])
        else:
            # fallback small catalog
            sample = [
                {'item_id':'r1','title':'Intro to Python - Official Tutorial','url':'https://docs.python.org/3/tutorial/','tags_list':['python','basics']},
                {'item_id':'r2','title':'Scikit-learn Tutorial','url':'https://scikit-learn.org/stable/tutorial/','tags_list':['ml','machine-learning']},
                {'item_id':'r3','title':'Coursera - Machine Learning (Andrew Ng)','url':'https://www.coursera.org/learn/machine-learning','tags_list':['ml','course']},
            ]
            df = pd.DataFrame(sample)
            df['tags_list'] = df['tags_list']
        _cached_resources = df
    return _cached_resources

# Utility: popularity counts per resource (from interactions mapped to resource item_id)
def compute_popularity():
    df = load_interactions()
    # treat 'complete' as heaviest, start/view lighter
    w = {'complete':3, 'start':2, 'view':1}
    if 'event_type' not in df.columns:
        return {}
    df['weight'] = df['event_type'].map(lambda x: w.get(x, 1))
    counts = df.groupby('item_id')['weight'].sum().to_dict()
    return counts

# Map resource tags to item_ids (simple)
def build_tag_index(resources_df):
    tag_index = defaultdict(set)
    for _, row in resources_df.iterrows():
        item = row['item_id']
        tags = row.get('tags_list', []) or []
        # include title tokens as pseudo-tags
        title_tokens = tokenize(row.get('title',''))
        for t in tags + title_tokens:
            tag_index[t].add(item)
    return tag_index

# Find similarity between a user history item and resource (here we treat item/item_id strings -> tags via resource catalog)
def resource_similarity(resource_row, item_id, resources_df):
    """
    If item_id exists in resources_df -> compute jaccard between tag sets.
    Otherwise return 0.
    """
    try:
        other = resources_df[resources_df['item_id'] == item_id]
        if other.empty:
            return 0.0
        a = set(resource_row.get('tags_list', []))
        b = set(other.iloc[0].get('tags_list', []))
        if not a and not b:
            return 0.0
        return float(len(a & b)) / float(len(a | b)) if (a or b) else 0.0
    except Exception:
        return 0.0

def recommend_items(user_id: str, query: str, k: int = 5):
    """
    Returns a list of recommendation dicts:
      {'item_id','title','url','score','explanation'}
    """
    start_time = time.time()
    try:
        resources = load_resources()
        interactions = load_interactions()
        popularity = compute_popularity()
        resources_index = {r['item_id']: r for _, r in resources.iterrows()} if not resources.empty else {}
        # user history
        user_hist = []
        if not interactions.empty and user_id in interactions['user_id'].values:
            user_df = interactions[interactions['user_id'] == user_id].sort_values('timestamp', ascending=False)
            user_hist = list(user_df['item_id'].values)[:50]  # recent 50
        # derive simple user-topic weights from history
        user_topic_counts = Counter()
        if user_hist:
            for item in user_hist:
                # map to resource tags if available
                if item in resources_index:
                    tags = resources_index[item].get('tags_list', [])
                    user_topic_counts.update(tags)
        # parsed query tokens
        q_tokens = tokenize(query or '')
        q_tags = q_tokens  # simple approach
        # scoring
        scores = {}
        explanations = {}
        now = pd.Timestamp.now()
        for _, row in resources.iterrows():
            item_id = row['item_id']
            title = row['title']
            url = row['url'] if 'url' in row else row.get('link', '')
            # tag match: jaccard between query tokens and tags/title tokens
            tag_tokens = row.get('tags_list', []) or []
            title_tokens = tokenize(title)
            tag_match = jaccard(q_tokens, tag_tokens + title_tokens)
            # popularity (normalized)
            pop = popularity.get(item_id, 0)
            pop_score = math.log(1 + pop) if pop > 0 else 0.0
            # user preference: average similarity between resource tags and user's top topics
            user_pref = 0.0
            if user_topic_counts:
                # score proportional to sum of user topic counts that match resource tags
                s = 0.0
                for t,cnt in user_topic_counts.items():
                    if t in tag_tokens:
                        s += cnt
                # normalize
                user_pref = math.log(1 + s)
            # recency bonus: if user recently interacted with same item, give small boost
            recency_bonus = 0.0
            if item_id in user_hist:
                # more recent interactions earlier in user_hist are boosted
                idx = user_hist.index(item_id)
                recency_bonus = max(0.0, 1.0 - (idx / 50.0))
            # Combine into final score with weights (tuneable)
            # We place higher weight on tag_match and user_pref, moderate on popularity
            score = (3.0 * tag_match) + (2.0 * user_pref) + (1.0 * pop_score) + (1.0 * recency_bonus)
            scores[item_id] = float(score)
            expl = []
            if tag_match > 0:
                expl.append(f"query-match:{round(tag_match,3)}")
            if user_pref > 0:
                expl.append(f"user-pref:{round(user_pref,3)}")
            if pop_score > 0:
                expl.append(f"pop:{round(pop_score,3)}")
            if recency_bonus > 0:
                expl.append(f"recent")
            if not expl:
                expl.append("baseline")
            explanations[item_id] = "; ".join(expl)
        # sort items by score
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        results = []
        for item_id, sc in ranked[:k]:
            row = resources[resources['item_id'] == item_id].iloc[0]
            results.append({
                "item_id": item_id,
                "title": row.get('title', item_id),
                "url": row.get('url', ''),
                "score": round(float(sc), 4),
                "explanation": explanations.get(item_id, "")
            })
        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"recommend_items user={user_id} query='{query}' k={k} -> {len(results)} results ({elapsed} ms)")
        return results
    except Exception as e:
        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.exception(f"recommend_items failed user={user_id} query='{query}' k={k} ({elapsed} ms)")
        # return empty with error explanation in minimal form (main.py logs)
        return []
