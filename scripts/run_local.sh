#!/usr/bin/env bash
# Run backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000


# In another terminal run:
# streamlit run src/ui/streamlit_app.py
