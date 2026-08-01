# app.py
import streamlit as st
from backend import generate_pdf, get_ai_stream, get_openai_client, load_lottie_url
from prompts import SYSTEM_PROMPT
from streamlit_lottie import st_lottie

# -----------------------------------------------------------------------------
# PAGE CONFIG & CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ClinicalPrep Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
    }
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #ffffff;
        border-left: 5px solid #3b82f6;
    }
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f0fdf4;
        border-left: 5px solid #10b981;
    }
    .main-header { color: #0f172a; font-weight: 700; margin-bottom: 0px; }
    .sub-header { color: #64748b; font-size: 0.95rem; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .stButton>button {
        width: 100%; border-radius: 12px;
        background: linear-gradient(90deg, #10b981, #059669);
        color: white; border: none; font-weight: 600; transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize OpenAI Client
client = get_openai_client()
if not client:
    st.error(
        "⚠️ API Key missing! Set OPENAI_API_KEY in your local `.env` file or Streamlit Cloud Secrets."
    )
    st.stop()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & ACTIONS
# -----------------------------------------------------------------------------
with st.sidebar:
    lottie_json = load_lottie_url(
        "https://assets5.lottiefiles.com/packages/lf20_5njp3vgg.json"
    )
    if lottie_json:
        st_lottie(lottie_json, height=140, key="medical_anim")

    st.markdown("### 📋 Preparation Tracker")

    user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
    current_step = min(len(user_msgs) + 1, 5)

    st.progress(current_step / 5.0)
    st.caption(f"**Step {current_step} of 5** in progress")

    st.markdown(
        """
    * **1.** Chief Complaint
    * **2.** Symptom Details
    * **3.** History & Meds
    * **4.** Appointment Goals
    * **5.** Final Doctor Brief
    """
    )

    st.divider()

    # Search for compiled brief in chat history to display PDF Download Button
    brief_content = None
    for msg in reversed(st.session_state.messages):
        if (
            msg["role"] == "assistant"
            and "Patient Pre-Visit Summary" in msg["content"]
        ):
            brief_content = msg["content"]
            break

    if brief_content:
        st.success("✅ Summary Brief Ready!")
        pdf_bytes = generate_pdf(brief_content)
        st.download_button(
            label="📥 Download Summary PDF",
            data=pdf_bytes,
            file_name="Patient_PreVisit_Summary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.divider()

    if st.button("🔄 Restart Intake Session"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------------------------------------------
# CHAT INTERFACE
# -----------------------------------------------------------------------------
st.markdown(
    "<h1 class='main-header'>🩺 ClinicalPrep Assistant</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='sub-header'>I'm your AI assistant, here to help you prepare for your upcoming doctor's visit.</p>",
    unsafe_allow_html=True,
)

# Render Chat History
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🩺"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# User Chat Input
if user_input := st.chat_input("Describe your symptoms or reason for visit..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🩺"):
        stream = get_ai_stream(client, st.session_state.messages, SYSTEM_PROMPT)
        response_text = st.write_stream(stream)

    st.session_state.messages.append(
        {"role": "assistant", "content": response_text}
    )