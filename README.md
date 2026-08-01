# 🩺 ClinicalPrep AI

**ClinicalPrep AI** is an intelligent, empathetic patient-intake chatbot designed to bridge the gap between patients and physicians. It guides patients through a structured conversational interview using the standard **OPQRST framework**, compiling their symptoms, history, and goals into a concise 30-second **"Doctor Brief"** summary for their visit.

---

## 🚀 Key Features

* **Guided Intake Workflow:** 5-step conversational intake powered by OpenAI (`gpt-4o-mini`).
* **Adaptive Light/Dark Theme:** Styled using native CSS variables for seamless visual integration across device themes.
* **Contextual Interaction Chips:** Quick-reply buttons for standard choices to minimize typing friction on mobile devices.
* **Instant PDF Summary Export:** Automatically converts generated summaries into downloadable PDF briefs using `fpdf2`.
* **Built-in Triage Guardrails:** Emergency detection logic for red-flag symptoms with zero clinical diagnostic speculation.

---

## 📁 Modular Package Layout

```text
ACE_Chatbot/
├── src/
│   ├── app.py                # Main Streamlit UI & interaction interface
│   ├── backend.py            # OpenAI client & chat streaming logic
│   ├── prompts.py            # CC-SC-R system prompt & template definitions
│   ├── utils/
│   │   └── pdf_generator.py  # Standalone FPDF export engine
│   └── assets/
│       └── style.css         # Theme stylesheet
└── tests/
    └── test_e2e.py           # Automated end-to-end testing script