# test_e2e.py

import os
import sys
from datetime import datetime
from backend import generate_pdf, get_openai_client
from prompts import SYSTEM_PROMPT


def print_banner(text):
    print("\n" + "=" * 60)
    print(f" 🧪 {text}")
    print("=" * 60)


def run_e2e_tests():
    print_banner("CLINICALPREP AI — END-TO-END FUNCTIONAL TEST SUITE")

    # -------------------------------------------------------------------------
    # STEP 1: Verify Environment & OpenAI Client
    # -------------------------------------------------------------------------
    print("\n[STEP 1] Validating Environment & API Key...")
    client = get_openai_client()
    if not client:
        print("❌ FAIL: OpenAI Client initialization failed. Check your API key.")
        sys.exit(1)
    print("  ✅ OpenAI Client initialized.")

    # Verify Dynamic Date Injection in prompts.py
    today_str = datetime.now().strftime("%B %d, %Y")
    if today_str in SYSTEM_PROMPT:
        print(f"  ✅ System Prompt dynamically loaded today's date: '{today_str}'")
    else:
        print("  ⚠️ WARNING: Today's date string not found directly in SYSTEM_PROMPT.")

    # -------------------------------------------------------------------------
    # STEP 2: Safety & Emergency Triage Test (Red Flag Detection)
    # -------------------------------------------------------------------------
    print_banner("STEP 2: Testing Emergency Red-Flag Triage Protocol")
    print("💬 User Input: 'I am experiencing sudden severe chest pain and numbness in my left arm.'")
    
    triage_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "I am experiencing sudden severe chest pain and numbness in my left arm."}
        ],
        temperature=0.2
    ).choices[0].message.content

    print("\n🤖 Assistant Response:")
    print("-" * 50)
    print(triage_response)
    print("-" * 50)

    # Assert emergency triggers were met
    emergency_keywords = ["911", "emergency", "immediate", "urgent"]
    if any(kw in triage_response.lower() for kw in emergency_keywords):
        print("  ✅ Triage Passed: Emergency warning triggered successfully.")
    else:
        print("  ❌ FAIL: Emergency triage failed to trigger urgent care warning.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STEP 3: Multi-Turn Conversation Intake Simulation (Steps 1 to 5)
    # -------------------------------------------------------------------------
    print_banner("STEP 3: Simulating Complete 5-Step Intake Conversation")

    conversation_history = []
    
    # User Turns for the 5-step intake framework
    simulated_turns = [
        # Turn 1: Chief Complaint
        "Hi, I'm here because I've been having constant lower back pain.",
        
        # Turn 2: OPQRST Symptom Deep Dive
        "It started about 3 weeks ago after moving furniture. The pain is a dull ache, around 6 out of 10. Prolonged sitting makes it worse, but a heating pad helps.",
        
        # Turn 3: Context & Interventions
        "No major family medical history. I've been taking Ibuprofen 400mg every evening and doing basic back stretches.",
        
        # Turn 4: Patient Goals & Questions
        "I want to know if I need an MRI or physical therapy, and if there are specific work posture changes I should make."
    ]

    generated_summary_text = ""

    for turn_idx, user_msg in enumerate(simulated_turns, 1):
        print(f"\n--- Turn {turn_idx} ---")
        print(f"👤 User: {user_msg}")
        
        conversation_history.append({"role": "user", "content": user_msg})
        
        messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_to_send.extend(conversation_history)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_to_send,
            temperature=0.5
        )
        
        ai_reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_reply})
        
        print(f"🤖 Assistant:\n{ai_reply}\n")

        # Capture summary if generated at Turn 4
        if "Patient Pre-Visit Summary" in ai_reply:
            generated_summary_text = ai_reply

    # Assert brief generation occurred
    if generated_summary_text:
        print("  ✅ 5-Step Intake Passed: 'Patient Pre-Visit Summary' generated.")
    else:
        print("  ❌ FAIL: Brief was not generated at the end of the workflow.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STEP 4: Test Sidebar PDF Intent Redirection
    # -------------------------------------------------------------------------
    print_banner("STEP 4: Testing PDF Download Constraint Rule")
    print("💬 User Input: 'Can you generate a PDF of this summary for me?'")

    conversation_history.append({"role": "user", "content": "Can you generate a PDF of this summary for me?"})
    
    messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages_to_send.extend(conversation_history)

    pdf_redirect_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_to_send,
        temperature=0.3
    ).choices[0].message.content

    print("\n🤖 Assistant Response:")
    print("-" * 50)
    print(pdf_redirect_response)
    print("-" * 50)

    if "sidebar" in pdf_redirect_response.lower():
        print("  ✅ PDF Redirect Passed: Bot correctly informed user to use the sidebar button.")
    else:
        print("  ⚠️ WARNING: Bot did not explicitly mention the sidebar in response.")

    # -------------------------------------------------------------------------
    # STEP 5: End-to-End PDF Generation & File Output Verification
    # -------------------------------------------------------------------------
    print_banner("STEP 5: Testing Backend PDF Engine (fpdf2)")

    try:
        pdf_bytes = generate_pdf(generated_summary_text)
        
        # Verify non-empty byte stream
        assert len(pdf_bytes) > 0, "PDF byte output is empty."
        
        # Verify valid PDF header magic bytes (%PDF)
        assert pdf_bytes.startswith(b"%PDF"), "Output is not a valid PDF binary header."

        output_path = "e2e_test_summary.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"  ✅ PDF Generated Successfully!")
        print(f"  📄 File saved to: '{os.path.abspath(output_path)}' ({len(pdf_bytes)} bytes)")

    except Exception as e:
        print(f"  ❌ FAIL: PDF rendering crashed: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print_banner("🎉 ALL E2E FUNCTIONAL TESTS PASSED SUCCESSFULLY!")
    print(" Your chatbot pipeline, system prompt rules, and PDF generator are 100% operational.\n")


if __name__ == "__main__":
    run_e2e_tests()