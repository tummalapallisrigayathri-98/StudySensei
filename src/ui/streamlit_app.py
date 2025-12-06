# src/ui/streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime


API_BASE = st.secrets.get('API_BASE', 'http://localhost:8000')


st.set_page_config(page_title='StudySensi — Chat', page_icon=':mortar_board:')
st.title('StudySensi — Your learning guide')
st.write('Ask for recommended next courses or exercises. Example: "What should I learn next about reinforcement learning?"')


if 'messages' not in st.session_state:
st.session_state['messages'] = []


with st.form('input_form', clear_on_submit=True):
user_input = st.text_input('You', '')
submitted = st.form_submit_button('Send')


if submitted and user_input:
st.session_state.messages.append({'role': 'user', 'text': user_input})
# build request
payload = {'user_id': 'anonymous', 'query': user_input, 'k': 5}
try:
r = requests.post(f"{API_BASE}/api/recommend", json=payload, timeout=5)
data = r.json()
recs = data.get('recommendations', [])
# format reply
reply = ''
for i, rec in enumerate(recs, start=1):
reply += f"{i}. {rec['title']} — {rec['explanation']}\n"
if not reply:
reply = 'No recommendations found.'
except Exception as e:
reply = f'Error contacting backend: {e}'
st.session_state.messages.append({'role': 'assistant', 'text': reply})
st.markdown(f"**StudySensi:** {msg['text']}')
