# src/backend.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st


@st.cache_resource
def get_openai_client():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    return OpenAI(api_key=api_key) if api_key else None


def get_ai_stream(client, chat_history, system_prompt, temperature=0.7):
    messages_to_send = [{"role": "system", "content": system_prompt}] + chat_history
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_to_send,
        temperature=temperature,
        stream=True,
    )