"""Optional Streamlit client for a separately running Liwin AI backend."""

from __future__ import annotations

import os
import uuid

import requests
import streamlit as st


API_URL = os.getenv("LIWIN_AI_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="Liwin AI", page_icon="L", layout="centered")
st.title("Liwin AI")
st.caption("Personal portfolio assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if question := st.chat_input("Ask about projects, skills, experience, or education"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"question": question, "session_id": st.session_state.session_id},
                    timeout=40,
                )
                response.raise_for_status()
                answer = response.json().get("answer")
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError("The backend returned an empty response.")
            except (requests.RequestException, ValueError):
                answer = "Liwin AI is temporarily unavailable. Please try again shortly."
            st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
