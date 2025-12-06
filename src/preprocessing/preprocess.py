# src/preprocessing/preprocess.py
import pandas as pd
from datetime import datetime
import os


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
INTERACTIONS = os.path.join(DATA_PATH, 'sample_interactions.csv')




def temporal_split(df, test_days=7):
# For toy dataset: split by last timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])
max_ts = df['timestamp'].max()
split_point = max_ts - pd.Timedelta(days=test_days)
train = df[df['timestamp'] <= split_point]
test = df[df['timestamp'] > split_point]
return train, test




def make_sequences(df, user_col='user_id', item_col='item_id', window=5):
df = df.sort_values(['user_id','timestamp'])
seqs = []
for uid, g in df.groupby(user_col):
items = list(g[item_col])
for i in range(1, len(items)):
history = items[max(0,i-window):i]
target = items[i]
seqs.append({'user_id': uid, 'history': history, 'target': target})
return pd.DataFrame(seqs)




if __name__ == '__main__':
df = pd.read_csv(INTERACTIONS)
train, test = temporal_split(df, test_days=30)
print('TRAIN', train.shape, 'TEST', test.shape)
seqs = make_sequences(train)
print('SEQS', seqs.head())
