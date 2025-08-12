import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Intelligent Document Q&A",
    page_icon="🤖",
    layout="wide"
)

# --- Custom CSS ---
glass_box_css = """
<style>
body {
    background-color: #e0e5ec;
}
.glass-box {
    background: rgba(40, 55, 71, 0.6);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
}
.question-title {
    font-weight: bold;
    font-size: 1.15em;
    color: #ffffff;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    margin-bottom: 12px;
}
.answer-text {
    color: #f0f3f4;
    font-size: 1.05em;
    font-weight: 500;
    line-height: 1.6;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
}
</style>
"""
st.markdown(glass_box_css, unsafe_allow_html=True)

# --- Backend API Configuration ---
API_BASE_URL = "https://soumya721644-backend-llm.hf.space/api/v1"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/hackrx/upload"   # New upload route in backend
RUN_ENDPOINT = f"{API_BASE_URL}/hackrx/run"

# --- UI ---
st.title("📄 Intelligent Document Query System")
st.markdown("An LLM-powered system to answer questions about your uploaded documents.")
st.divider()

with st.sidebar:
    st.header("⚙️ Configuration")

    uploaded_file = st.file_uploader("📂 Upload PDF Document", type=["pdf"])
    bearer_token = st.text_input(
        "Enter Bearer Token",
        "b8171a8cdbd8010a1ac308defcbcc5210fbba7412f60ef99cd428ffb3a412be7",
        type="password"
    )

    st.subheader("❓ Ask Questions")
    sample_questions = (
        "What is the grace period for premium payment under the policy?\n"
        "What is the waiting period for pre-existing diseases?\n"
        "Does this policy cover maternity expenses?\n"
        "What is the waiting period for cataract surgery?\n"
        "Are organ donor expenses covered?"
    )
    questions_text = st.text_area("Questions", sample_questions, height=250)

submit_button = st.sidebar.button("🧠 Get Answers", use_container_width=True)

# --- Main Processing ---
if submit_button:
    if not uploaded_file or not questions_text or not bearer_token:
        st.error("Please upload a PDF, enter your questions, and provide the bearer token.")
    else:
        questions_list = [q.strip() for q in questions_text.split("\n") if q.strip()]

        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            # Step 1: Upload the file
            with st.spinner("📤 Uploading document..."):
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                upload_res = requests.post(UPLOAD_ENDPOINT, headers=headers, files=files)

                if upload_res.status_code != 200:
                    st.error(f"File upload failed: {upload_res.text}")
                    st.stop()

                # The backend should return a document reference or URL
                doc_ref = upload_res.json().get("document_id", uploaded_file.name)

            # Step 2: Run question answering
            payload = {"documents": doc_ref, "questions": questions_list}
            with st.spinner("🤖 Processing document and finding answers..."):
                run_res = requests.post(RUN_ENDPOINT, json=payload, headers={**headers, "Content-Type": "application/json"})

            if run_res.status_code == 200:
                st.success("✅ Answers received successfully!")
                answers = run_res.json().get("answers", [])

                if len(answers) == len(questions_list):
                    for i, (q, a) in enumerate(zip(questions_list, answers)):
                        st.markdown(f"""
                        <div class="glass-box">
                            <p class="question-title">Question {i+1}: {q}</p>
                            <p class="answer-text">{a}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Mismatch between questions asked and answers received.")

            else:
                st.error(f"❌ API Error (Status {run_res.status_code})")
                st.text(run_res.text)

        except requests.exceptions.RequestException as e:
            st.error(f"Connection Error: Could not connect to the backend.")
            st.error(f"Details: {e}")

else:
    st.info("Upload a PDF, enter your questions, and click 'Get Answers'.")
