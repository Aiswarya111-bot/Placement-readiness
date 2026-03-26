import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
genai.configure(api_key="YOUR_API_KEY_HERE")  # 🔑 Replace with your key
model = genai.GenerativeModel("gemini-2.0-flash")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text

def ask_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text

def generate_pdf_report(sections: dict) -> bytes:
    """Takes a dict of {section_title: content} and returns PDF bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("AI Placement Readiness Report", styles["Title"]))
    story.append(Spacer(1, 20))

    for title, content in sections.items():
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(Spacer(1, 8))
        for line in content.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Normal"]))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 16))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Placement Readiness", page_icon="🎯", layout="wide")
st.title("🎯 AI-Powered Placement Readiness System")
st.write("Enhancing interview performance using Generative AI")

# Session state init
for key in ["resume_text", "analysis", "questions", "jd_match", "chat_history", "interview_questions"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "chat_history" else []

# ─────────────────────────────────────────────
# SIDEBAR — Upload
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        st.session_state.resume_text = extract_text(uploaded_file)
        st.success("Resume loaded!")
        with st.expander("Preview"):
            st.write(st.session_state.resume_text[:800])

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Resume Analysis",
    "❓ Interview Questions",
    "💬 Mock Interview",
    "🔍 JD Matcher",
    "📥 Download Report"
])

resume = st.session_state.resume_text

# ── TAB 1: Resume Analysis ──────────────────
with tab1:
    st.subheader("Resume Analysis")
    if not resume:
        st.info("Please upload your resume from the sidebar.")
    else:
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing..."):
                prompt = f"""
                You are an expert recruiter. Analyze this resume and provide:
                - Key Strengths
                - Weaknesses
                - Improvement Suggestions
                - ATS Optimization Tips

                Resume:
                {resume}
                """
                st.session_state.analysis = ask_gemini(prompt)
        if st.session_state.analysis:
            st.write(st.session_state.analysis)

# ── TAB 2: Interview Questions ───────────────
with tab2:
    st.subheader("Interview Questions")
    if not resume:
        st.info("Please upload your resume from the sidebar.")
    else:
        if st.button("Generate Questions"):
            with st.spinner("Generating questions..."):
                prompt = f"""
                Based on this resume, generate:
                - 5 Technical interview questions
                - 3 HR/behavioral questions
                - 2 situational questions

                Resume:
                {resume}
                """
                st.session_state.questions = ask_gemini(prompt)

        if st.session_state.questions:
            st.write(st.session_state.questions)

            # Answer Evaluator
            st.divider()
            st.subheader("✍️ Answer Evaluator")
            selected_q = st.text_input("Paste a question to answer:")
            user_answer = st.text_area("Your Answer:")
            if st.button("Evaluate My Answer"):
                if selected_q and user_answer:
                    with st.spinner("Evaluating..."):
                        eval_prompt = f"""
                        You are an expert interviewer. Evaluate this answer:

                        Question: {selected_q}
                        Answer: {user_answer}

                        Provide:
                        - Score out of 10
                        - What was good
                        - What was missing
                        - A model answer
                        """
                        result = ask_gemini(eval_prompt)
                        st.write(result)
                else:
                    st.warning("Please enter both a question and your answer.")

# ── TAB 3: Mock Interview ────────────────────
with tab3:
    st.subheader("💬 Mock Interview Chat")
    if not resume:
        st.info("Please upload your resume from the sidebar.")
    else:
        if st.button("Start / Reset Interview"):
            with st.spinner("Preparing interviewer..."):
                intro_prompt = f"""
                You are a professional interviewer. The candidate's resume is below.
                Start the mock interview by greeting them and asking your first question.
                Keep your responses concise (2-4 sentences max per turn).

                Resume:
                {resume}
                """
                first_msg = ask_gemini(intro_prompt)
                st.session_state.chat_history = [
                    {"role": "assistant", "content": first_msg}
                ]

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # User input
        user_input = st.chat_input("Your answer...")
        if user_input and st.session_state.chat_history:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            history_text = "\n".join(
                [f"{m['role'].upper()}: {m['content']}" for m in st.session_state.chat_history]
            )
            follow_up_prompt = f"""
            You are a professional interviewer conducting a mock interview.
            Resume: {resume}

            Conversation so far:
            {history_text}

            Continue the interview naturally. Ask the next question or give brief feedback then ask next question.
            Keep it concise (2-4 sentences).
            """
            with st.spinner("Interviewer is responding..."):
                reply = ask_gemini(follow_up_prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.write(reply)

# ── TAB 4: JD Matcher ────────────────────────
with tab4:
    st.subheader("🔍 Job Description Matcher")
    if not resume:
        st.info("Please upload your resume from the sidebar.")
    else:
        jd_text = st.text_area("Paste the Job Description here:", height=200)
        if st.button("Match Resume to JD"):
            if jd_text.strip():
                with st.spinner("Matching..."):
                    match_prompt = f"""
                    Compare this resume against the job description and provide:
                    - Match Score (out of 100)
                    - Matching Skills & Keywords
                    - Missing Skills / Gaps
                    - Recommendations to tailor the resume

                    Resume:
                    {resume}

                    Job Description:
                    {jd_text}
                    """
                    st.session_state.jd_match = ask_gemini(match_prompt)
            else:
                st.warning("Please paste a job description.")

        if st.session_state.jd_match:
            st.write(st.session_state.jd_match)

# ── TAB 5: Download Report ───────────────────
with tab5:
    st.subheader("📥 Download Full Report as PDF")

    has_content = any([
        st.session_state.analysis,
        st.session_state.questions,
        st.session_state.jd_match
    ])

    if not has_content:
        st.info("Run Resume Analysis, Generate Questions, and/or JD Match first to include them in the report.")
    else:
        if st.button("Generate PDF Report"):
            sections = {}
            if st.session_state.analysis:
                sections["Resume Analysis"] = st.session_state.analysis
            if st.session_state.questions:
                sections["Interview Questions"] = st.session_state.questions
            if st.session_state.jd_match:
                sections["Job Description Match"] = st.session_state.jd_match

            pdf_bytes = generate_pdf_report(sections)
            st.download_button(
                label="⬇️ Download Report",
                data=pdf_bytes,
                file_name="placement_readiness_report.pdf",
                mime="application/pdf"
            )
