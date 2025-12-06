# src/recommender/baselines.py
import pandas as pd
from collections import Counter
import os


class MostPopular:
def __init__(self, persistence):
self.persistence = persistence
self._cache = None
self._build()


def _build(self):
df = self.persistence.load()
# define weights: complete=3, start=2, view=1
w = {'complete':3, 'start':2, 'view':1}
df['weight'] = df['event_type'].map(lambda x: w.get(x,1))
counts = df.groupby('item_id')['weight'].sum().to_dict()
# sort by weight desc
self._cache = sorted(counts.keys(), key=lambda k: -counts[k])


def get_top_k(self, k=10):
return self._cache[:k]
