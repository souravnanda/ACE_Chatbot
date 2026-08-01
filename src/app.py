# src/app.py
import os
import sys
import streamlit as st

# Ensure project root is in Python module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend import get_ai_stream, get_openai_client
from src.prompts import SYSTEM_PROMPT
from src.utils.pdf_generator import generate_pdf

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION (Expanded on Desktop/Laptop, Collapsed on Mobile)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ClinicalPrep AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="auto",  # Expands on Desktop (>=768px), Collapses on Mobile (<768px)
)

# -----------------------------------------------------------------------------
# CACHED CSS LOADER
# -----------------------------------------------------------------------------
@st.cache_data
def load_css(css_file_path):
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            return f"<style>\n{f.read()}\n</style>"
    return ""

css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
bg_path = os.path.join(os.path.dirname(__file__), "assets", "bg_image.png")
st.markdown(load_css(css_path), unsafe_allow_html=True)

# Initialize Cached OpenAI Client
client = get_openai_client()
if not client:
    st.error("⚠️ API Key missing! Set OPENAI_API_KEY in your local `.env` file or Streamlit Cloud Secrets.")
    st.stop()


def initialize_chat():
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm **ClinicalPrep AI**, your patient-intake assistant. "
                "Before we begin, please note that I don't provide medical advice—I'm here to help you prepare for your visit.\n\n"
                "To get started, may I please have your **Name**?"
            ),
        }
    ]
    st.session_state.current_step = 1


if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    initialize_chat()

if "quick_reply" not in st.session_state:
    st.session_state.quick_reply = None

if "current_step" not in st.session_state:
    st.session_state.current_step = 1

# Detect generated summary brief
brief_content = None
for msg in reversed(st.session_state.messages):
    if msg["role"] == "assistant" and "Patient Pre-Visit Summary" in msg["content"]:
        brief_content = msg["content"]
        break

# Get last assistant message
last_assistant_msg = ""
for msg in reversed(st.session_state.messages):
    if msg["role"] == "assistant":
        last_assistant_msg = msg["content"].lower()
        break

# Calculate user turns
user_turn_count = len([m for m in st.session_state.messages if m["role"] == "user"])

# Anticipate pending turn increment if quick reply or input is active
if st.session_state.get("quick_reply") or st.session_state.get("pending_user_input"):
    effective_user_turns = user_turn_count + 1
else:
    effective_user_turns = user_turn_count

# -----------------------------------------------------------------------------
# STEP & DYNAMIC QUESTION COUNTER CALCULATOR (ZERO-FLICKER)
# -----------------------------------------------------------------------------
if brief_content:
    st.session_state.current_step = 5
    step_label_text = "Final Review & Summary Brief (Completed 🎉)"
elif any(k in last_assistant_msg for k in ["anything else on your mind", "specific points or questions", "bring up with your doctor", "questions or outcomes", "goals for this appointment"]):
    st.session_state.current_step = max(st.session_state.current_step, 4)
    step_label_text = "Questions for Doctor (Question 1 of 1)"
elif st.session_state.current_step >= 3 or (st.session_state.current_step >= 2 and any(k in last_assistant_msg for k in ["medication", "supplement", "home remed", "currently taking", "taking for this"])):
    st.session_state.current_step = max(st.session_state.current_step, 3)
    s3_q = 2 if any(k in last_assistant_msg for k in ["remed", "home", "attempted"]) else 1
    step_label_text = f"Interventions & Meds (Question {s3_q} of 2)"
elif st.session_state.current_step >= 2 or any(k in last_assistant_msg for k in ["when did", "how long", "feeling this way", "experiencing concerns", "scale", "severe", "constant", "intermittent", "come and go", "better or worse", "trigger", "reliev", "associated"]):
    st.session_state.current_step = max(st.session_state.current_step, 2)
    if any(k in last_assistant_msg for k in ["scale", "severe", "1 to 10"]):
        s2_q = 2
    elif any(k in last_assistant_msg for k in ["constant", "intermittent", "come and go", "pattern", "frequency"]):
        s2_q = 3
    elif any(k in last_assistant_msg for k in ["better or worse", "trigger", "reliev", "make it"]):
        s2_q = 4
    elif any(k in last_assistant_msg for k in ["associated", "secondary", "other symptom", "fever", "nausea"]):
        s2_q = 5
    else:
        s2_q = 1
    step_label_text = f"Symptom Details (Question {s2_q} of 5)"
else:
    st.session_state.current_step = 1
    s1_q = min(effective_user_turns + 1, 7)
    step_label_text = f"Demographics & Reason for Visit (Question {s1_q} of 7)"

current_step = st.session_state.current_step

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists(bg_path):
        st.image(bg_path, width="stretch")
    else:
        st.markdown("### 🩺 ClinicalPrep AI")

    st.markdown("### ⚙️ Model Settings")
    temperature = st.slider(
        "Model Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more creative; lower values make it more focused and deterministic.",
    )

    st.divider()

    if brief_content:
        st.success("✅ Doctor Brief Ready!")
        pdf_bytes = generate_pdf(brief_content)
        st.download_button(
            label="📥 Download PDF Summary",
            data=pdf_bytes,
            file_name="Patient_PreVisit_Summary.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.divider()

    if st.button("🔄 Restart Intake", width="stretch"):
        initialize_chat()
        st.session_state.quick_reply = None
        st.session_state.pending_user_input = None
        st.rerun()

    # CUSTOM SIGNATURE FOOTER
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.85rem; opacity: 0.8; color: #38240D; padding-top: 5px;">
            Made with ❤️ by <b>Sourav Nanda</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# 📌 FROZEN TOP HEADER CONTAINER (LOCKED AT TOP)
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="frozen-header-container">
        <div class="title-text">🩺 ClinicalPrep AI</div>
        <div class="sub-text">Prepare your medical concerns into a concise 30-second summary for your physician.</div>
        <div class="progress-label">
            📋 Progress — Step {current_step} of 5: <span class="step-highlight">{step_label_text}</span>
        </div>
        <div class="custom-progress-bg">
            <div class="custom-progress-fill" style="width: {current_step * 20}%;"></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# RENDER CHAT HISTORY
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🩺"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "user":
            st.markdown(f"<div class='user-bubble-marker'></div>\n\n{msg['content']}", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-bubble-marker'></div>\n\n{msg['content']}", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INTENT-AWARE QUICK-REPLY CHIPS
# -----------------------------------------------------------------------------
current_chips = []

if not brief_content:
    # 0. Gender Selection Chips (Strictly Male, Female, Non-Binary)
    if any(k in last_assistant_msg for k in ["gender", "male, female", "non-binary"]):
        current_chips = [
            "Male",
            "Female",
            "Non-Binary",
        ]
    # 1. Chief Complaint Chips
    elif any(k in last_assistant_msg for k in ["main reason for your upcoming visit", "chief complaint", "reason for your visit"]) and not any(k in last_assistant_msg for k in ["what seems to be the issue", "more details", "tell me more"]):
        current_chips = [
            "Headache / Migraine",
            "Lower Back Pain",
            "Cough & Fever",
            "General Health Checkup",
            "Other",
        ]
    # 2a. Onset / Duration Chips
    elif any(k in last_assistant_msg for k in ["when did", "how long", "feeling this way", "experiencing concerns", "start experiencing"]) and not any(k in last_assistant_msg for k in ["to get started", "name", "scale", "severe", "constant", "intermittent", "more details"]):
        current_chips = [
            "Yesterday",
            "3–7 days ago",
            "More than a week",
            "More than a month",
            "Other",
        ]
    # 2b. Severity Chips
    elif any(k in last_assistant_msg for k in ["scale of 1 to 10", "1 to 10", "how severe", "rate your pain", "rate your symptom"]) and "more details" not in last_assistant_msg:
        current_chips = [
            "Mild (1-3)",
            "Moderate (4-6)",
            "Severe (7-9)",
            "Very Severe (10)",
        ]
    # 2c. Pattern / Frequency Chips
    elif any(k in last_assistant_msg for k in ["constant or intermittent", "constant", "intermittent", "come and go"]) and "more details" not in last_assistant_msg:
        current_chips = [
            "Constant",
            "Intermittent",
            "Comes and goes in waves",
            "Worse at night/morning",
            "Other",
        ]
    # 3. Interventions / Medication Chips
    elif any(k in last_assistant_msg for k in ["medication", "supplement", "remedy", "currently taking"]) and "more details" not in last_assistant_msg:
        current_chips = [
            "Taking Over-the-Counter Painkillers",
            "No current medications",
            "Using heating pad / rest",
            "Other",
        ]
    # 4. Patient Goals Chips
    elif any(k in last_assistant_msg for k in ["anything else on your mind", "specific points or questions", "bring up with your doctor", "questions or outcomes", "goals for this appointment"]) and "more details" not in last_assistant_msg:
        current_chips = [
            "Do I need an X-ray / MRI?",
            "Should I see a specialist?",
            "What should I monitor at home?",
            "Nothing else for now",
            "Other",
        ]

if current_chips:
    st.caption("⚡ **Quick Suggestions (Click to send):**")
    cols = st.columns(len(current_chips))
    for i, option in enumerate(current_chips):
        if cols[i].button(option, key=f"chip_{i}", width="stretch"):
            st.session_state.quick_reply = option

# Capture user input
user_input = st.chat_input("Type your response here...")

if st.session_state.quick_reply:
    user_input = st.session_state.quick_reply
    st.session_state.quick_reply = None

if user_input:
    st.session_state.pending_user_input = user_input
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(f"<div class='user-bubble-marker'></div>\n\n{user_input}", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar="🩺"):
        stream = get_ai_stream(client, st.session_state.messages, SYSTEM_PROMPT, temperature=temperature)
        response_text = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.session_state.pending_user_input = None
    st.rerun()