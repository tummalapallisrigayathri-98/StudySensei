# src/recommender/persistence.py
import pandas as pd
import os


class Persistence:
def __init__(self, interactions_path: str):
self.interactions_path = interactions_path
# create file if not exists
if not os.path.exists(self.interactions_path):
os.makedirs(os.path.dirname(self.interactions_path), exist_ok=True)
with open(self.interactions_path, 'w') as f:
f.write('user_id,item_id,event_type,timestamp\n')


def load(self):
return pd.read_csv(self.interactions_path)


def append_event(self, user_id, item_id, event_type, timestamp):
line = f"{user_id},{item_id},{event_type},{timestamp}\n"
with open(self.interactions_path, 'a') as f:
f.write(line)
