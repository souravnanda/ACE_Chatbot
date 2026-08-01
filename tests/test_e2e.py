# tests/test_e2e.py
import os
import sys
from datetime import datetime

# Ensure project root is in Python path for test execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend import get_openai_client
from src.prompts import SYSTEM_PROMPT
from src.utils.pdf_generator import generate_pdf


def print_banner(text):
    print("\n" + "=" * 60)
    print(f" 🧪 {text}")
    print("=" * 60)


def run_e2e_tests():
    print_banner("CLINICALPREP AI — END-TO-END FUNCTIONAL TEST SUITE")

    # STEP 1: Verify Environment & OpenAI Client
    print("\n[STEP 1] Validating Environment & API Key...")
    client = get_openai_client()
    if not client:
        print("❌ FAIL: OpenAI Client initialization failed. Check your API key.")
        sys.exit(1)
    print("  ✅ OpenAI Client initialized.")

    today_str = datetime.now().strftime("%B %d, %Y")
    if today_str in SYSTEM_PROMPT:
        print(f"  ✅ System Prompt dynamically loaded today's date: '{today_str}'")

    # STEP 2: Emergency Red-Flag Triage
    print_banner("STEP 2: Testing Emergency Red-Flag Triage Protocol")
    print("💬 User Input: 'I am experiencing sudden severe chest pain and numbness in my left arm.'")

    triage_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "I am experiencing sudden severe chest pain and numbness in my left arm.",
            },
        ],
        temperature=0.2,
    ).choices[0].message.content

    print("\n🤖 Assistant Response:\n" + "-" * 50 + f"\n{triage_response}\n" + "-" * 50)

    emergency_keywords = ["911", "112", "emergency", "immediate", "urgent"]
    if any(kw in triage_response.lower() for kw in emergency_keywords):
        print("  ✅ Triage Passed: Emergency warning triggered successfully.")
    else:
        print("  ❌ FAIL: Emergency triage failed to trigger urgent care warning.")
        sys.exit(1)

    # STEP 3: Multi-Turn Conversation Intake Simulation (Sequential Workflow)
    print_banner("STEP 3: Simulating Complete Sequential Intake Workflow")

    conversation_history = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm ClinicalPrep AI, your patient-intake assistant. "
                "Before we begin, please note that I don't provide medical advice—I'm here to help you prepare for your visit.\n\n"
                "To get started, may I please have your Name?"
            ),
        }
    ]

    # Complete 14-turn simulation including final Step 4 completion turn
    simulated_turns = [
        "John Doe",                                                 # 1. Name
        "34",                                                       # 2. Age
        "Male",                                                     # 3. Gender
        "175 cm",                                                   # 4. Height
        "70 kg",                                                    # 5. Weight
        "john.doe@example.com",                                     # 6. Contact Details
        "Lower Back Pain",                                          # 7. Reason for Visit
        "It started about 3 weeks ago after moving heavy boxes.",    # 8. Onset & Timeline
        "Pain severity is 6 out of 10",                             # 9. Severity
        "It is mostly constant with occasional sharp twinges.",      # 10. Pattern
        "Sitting for long hours makes it worse; rest and heating pad help.", # 11. Triggers/Relievers
        "Ibuprofen 400mg in the evening when needed.",              # 12. Medications / Interventions
        "I want to know if I need an MRI, when I can return to lifting, and if physical therapy is recommended.", # 13. Goals / Questions
        "No, that's everything! Please generate my summary brief.",  # 14. Final Confirmation -> Triggers Step 5
    ]

    generated_summary_text = ""

    for turn_idx, user_msg in enumerate(simulated_turns, 1):
        print(f"\n--- Turn {turn_idx} ---")
        print(f"👤 User: {user_msg}")

        conversation_history.append({"role": "user", "content": user_msg})
        messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages_to_send, temperature=0.3
        )

        ai_reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_reply})
        print(f"🤖 Assistant:\n{ai_reply}\n")

        if "Patient Pre-Visit Summary" in ai_reply:
            generated_summary_text = ai_reply

    if generated_summary_text:
        print("  ✅ 5-Step Intake Passed: 'Patient Pre-Visit Summary' generated successfully.")
    else:
        print("  ❌ FAIL: Summary Brief was not generated at the end of the workflow.")
        sys.exit(1)

    # STEP 4: PDF Intent Redirection
    print_banner("STEP 4: Testing PDF Download Constraint Rule")
    print("💬 User Input: 'Can you generate a PDF copy of this summary for me?'")

    conversation_history.append(
        {"role": "user", "content": "Can you generate a PDF copy of this summary for me?"}
    )
    messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    pdf_redirect_response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages_to_send, temperature=0.3
    ).choices[0].message.content

    print(
        "\n🤖 Assistant Response:\n"
        + "-" * 50
        + f"\n{pdf_redirect_response}\n"
        + "-" * 50
    )

    if "sidebar" in pdf_redirect_response.lower():
        print("  ✅ PDF Redirect Passed: Bot correctly informed user to use the sidebar.")
    else:
        print("  ⚠️ WARNING: Bot did not explicitly mention sidebar.")

    # STEP 5: PDF Engine Compilation
    print_banner("STEP 5: Testing Backend PDF Engine (fpdf2)")

    try:
        pdf_bytes = generate_pdf(generated_summary_text)
        assert len(pdf_bytes) > 0, "PDF byte output is empty."
        assert pdf_bytes.startswith(b"%PDF"), "Output is not a valid PDF header."

        output_dir = "tests"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "e2e_test_summary.pdf")

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(
            f"  ✅ PDF Generated Successfully!"
            f"\n  📄 Saved to: '{os.path.abspath(output_path)}' ({len(pdf_bytes)} bytes)"
        )

    except Exception as e:
        print(f"  ❌ FAIL: PDF rendering crashed: {e}")
        sys.exit(1)

    print_banner("🎉 ALL E2E FUNCTIONAL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_e2e_tests()