# frontend/app.py
import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Intelligent Document Q&A",
    page_icon="🤖",
    layout="wide"
)

# --- Custom CSS for Enhanced Glassmorphism Effect ---
# This CSS has been updated to improve text readability. The glass box
# is slightly darker, and the text is now white with a shadow to create
# strong contrast against the blurred background.
glass_box_css = """
<style>
body {
    background-color: #e0e5ec; /* A neutral, light background */
}
.glass-box {
    background: rgba(40, 55, 71, 0.6); /* Darker, semi-transparent background for contrast */
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px); /* For Safari */
    border-radius: 15px; /* Rounded corners */
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 25px;
    margin-bottom: 20px; /* Space between boxes */
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15); /* Subtle shadow for depth */
}
.question-title {
    font-weight: bold;
    font-size: 1.15em;
    color: #ffffff; /* Bright white for high contrast */
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3); /* Shadow for readability */
    margin-bottom: 12px;
}
.answer-text {
    color: #f0f3f4; /* A slightly softer white for the answer */
    font-size: 1.05em; /* Increase font size slightly */
    font-weight: 500; /* Make the answer text a bit bolder */
    line-height: 1.6;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5); /* Stronger shadow for pop */
}
</style>
"""
st.markdown(glass_box_css, unsafe_allow_html=True)


# --- Backend API Configuration ---
API_BASE_URL = "https://huggingface.co/spaces/soumya721644/backend_llm"  # Hugging Face backend Space URL


# --- UI Components ---
st.title("📄 Intelligent Document Query System")
st.markdown("An LLM-powered system to answer questions about your documents (insurance, legal, HR, etc.).")
st.divider()

# --- Sidebar for Inputs ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Pre-fill with sample data from the problem statement
    doc_url = st.text_input(
        "Enter Document URL (PDF)", 
        "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    )
    
    bearer_token = st.text_input(
        "Enter Bearer Token", 
        "b8171a8cdbd8010a1ac308defcbcc5210fbba7412f60ef99cd428ffb3a412be7", 
        type="password"
    )
    
    st.subheader("❓ Ask Questions")
    st.markdown("Enter one question per line.")
    
    sample_questions = (
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?\n"
        "What is the waiting period for pre-existing diseases (PED) to be covered?\n"
        "Does this policy cover maternity expenses, and what are the conditions?\n"
        "What is the waiting period for cataract surgery?\n"
        "Are the medical expenses for an organ donor covered under this policy?"
    )
    
    questions_text = st.text_area(
        "Questions", 
        sample_questions, 
        height=250
    )

submit_button = st.sidebar.button("🧠 Get Answers", use_container_width=True, type="primary")

# --- Main Content Area for Results ---
if submit_button:
    # Validate inputs
    if not doc_url or not questions_text or not bearer_token:
        st.error("Please provide the document URL, at least one question, and the bearer token.")
    else:
        # Prepare the request
        questions_list = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        payload = {
            "documents": doc_url,
            "questions": questions_list
        }
        
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Make the API call
        with st.spinner("Processing document and finding answers... Please wait. ⏳"):
            try:
                response = requests.post(API_ENDPOINT, json=payload, headers=headers)
                
                if response.status_code == 200:
                    st.success("✅ Answers received successfully!")
                    results = response.json()
                    answers = results.get("answers", [])
                    
                    if len(answers) == len(questions_list):
                        # Loop through questions and answers and display them in the glass boxes
                        for i, (question, answer) in enumerate(zip(questions_list, answers)):
                            # Basic HTML sanitization to prevent rendering issues
                            question_html = question.replace("<", "&lt;").replace(">", "&gt;")
                            answer_html = answer.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

                            st.markdown(f"""
                            <div class="glass-box">
                                <p class="question-title">Question {i+1}: {question_html}</p>
                                <p class="answer-text">{answer_html}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error("Mismatch between questions asked and answers received.")

                else:
                    st.error(f"❌ API Error (Status {response.status_code})")
                    try:
                        error_details = response.json()
                        st.json(error_details)
                    except json.JSONDecodeError:
                        st.text(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: Could not connect to the backend at {API_ENDPOINT}.")
                st.error(f"Details: {e}")
                st.info("Please ensure the FastAPI backend server is running.")

else:
    st.info("Enter a document URL and your questions in the sidebar, then click 'Get Answers'.")



