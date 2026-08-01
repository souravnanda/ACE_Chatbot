# src/backend.py

import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st


# Cached OpenAI Client (Prevents recreating connection on every turn for faster response)
@st.cache_resource
def get_openai_client():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


# Fast Streaming API Completion
def get_ai_stream(client, chat_history, system_prompt, temperature=0.7):
    messages_to_send = [{"role": "system", "content": system_prompt}]
    messages_to_send.extend(chat_history)

    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_to_send,
        temperature=temperature,
        stream=True,
    )


# Fetch Lottie vector animation JSON
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None