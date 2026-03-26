import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
import io
import json
import re
import plotly.graph_objects as go
import plotly.express as px
 
# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
client = genai.Client(api_key="AIzaSyCxp60tMVYGqqvWz7NKDkvM6mHeo-bGnk4")
MODEL_ID = "models/gemini-2.5-flash"
 
# ─────────────────────────────────────────────
# CUSTOM CSS — Dark Neon Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
 
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}
 
/* Background */
.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0f1a 100%);
    min-height: 100vh;
}
 
/* Header */
.main-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
}
.main-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2d78);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    margin-bottom: 0.3rem;
}
.main-header p {
    color: #666;
    font-size: 1rem;
    letter-spacing: 2px;
    text-transform: uppercase;
}
 
/* Score Cards */
.score-card {
    background: linear-gradient(135deg, #111827, #1a2332);
    border: 1px solid rgba(0, 212, 255, 0.15);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.score-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #00d4ff, #7b2ff7);
}
.score-card:hover {
    border-color: rgba(0, 212, 255, 0.4);
    transform: translateY(-2px);
}
.score-number {
    font-size: 3rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: #00d4ff;
}
.score-label {
    font-size: 0.75rem;
    color: #888;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.3rem;
}
 
/* Bullet Point Cards */
.insight-card {
    background: rgba(17, 24, 39, 0.8);
    border-left: 3px solid #00d4ff;
    border-radius: 0 12px 12px 0;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: #e2e8f0;
    font-size: 0.92rem;
    line-height: 1.5;
    transition: all 0.2s ease;
}
.insight-card:hover {
    background: rgba(0, 212, 255, 0.07);
    border-left-color: #7b2ff7;
    transform: translateX(4px);
}
.insight-card.strength { border-left-color: #10b981; }
.insight-card.weakness { border-left-color: #ef4444; }
.insight-card.suggestion { border-left-color: #f59e0b; }
.insight-card.ats { border-left-color: #8b5cf6; }
 
/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 1.5rem 0 0.8rem 0;
}
.section-header .icon {
    font-size: 1.2rem;
}
.section-header h3 {
    font-size: 0.75rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #00d4ff;
    margin: 0;
    font-weight: 600;
}
 
/* Skill Tags */
.skill-tag {
    display: inline-block;
    background: rgba(123, 47, 247, 0.15);
    border: 1px solid rgba(123, 47, 247, 0.4);
    color: #a78bfa;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.8rem;
    margin: 0.2rem;
    font-family: 'JetBrains Mono', monospace;
}
.skill-tag.match {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.4);
    color: #6ee7b7;
}
.skill-tag.missing {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.4);
    color: #fca5a5;
}
 
/* Interview Question Cards */
.question-card {
    background: linear-gradient(135deg, #111827, #151e2e);
    border: 1px solid rgba(123, 47, 247, 0.2);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    color: #e2e8f0;
}
.question-card .q-type {
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #7b2ff7;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.question-card .q-text {
    font-size: 0.95rem;
    line-height: 1.5;
}
 
/* Score Badge */
.score-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.1rem;
}
.score-badge.high { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; }
.score-badge.mid  { background: rgba(245,158,11,0.2);  color: #f59e0b; border: 1px solid #f59e0b; }
.score-badge.low  { background: rgba(239,68,68,0.2);   color: #ef4444; border: 1px solid #ef4444; }
 
/* Readiness Meter */
.readiness-bar-wrap {
    background: rgba(255,255,255,0.05);
    border-radius: 999px;
    height: 12px;
    width: 100%;
    overflow: hidden;
    margin: 0.5rem 0;
}
.readiness-bar {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #7b2ff7, #00d4ff);
    transition: width 1s ease;
}
 
/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(17, 24, 39, 0.8);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.05);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #888;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.5rem 1rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(123,47,247,0.15)) !important;
    color: #fff !important;
}
 
/* Sidebar */
.css-1d391kg, [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117, #111827);
    border-right: 1px solid rgba(255,255,255,0.05);
}
 
/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7b2ff7, #00d4ff) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.5px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    opacity: 0.85 !important;
    transform: translateY(-1px) !important;
}
 
/* Input fields */
.stTextArea textarea, .stTextInput input {
    background: rgba(17, 24, 39, 0.9) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
 
/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }
 
/* Chat messages */
[data-testid="stChatMessage"] {
    background: rgba(17, 24, 39, 0.6) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
}
 
/* Info/warning */
.stInfo, .stSuccess, .stWarning {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)
 
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
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    return response.text
 
def ask_gemini_json(prompt):
    """Ask Gemini and parse JSON response."""
    full_prompt = prompt + "\n\nRESPOND ONLY WITH VALID JSON. No markdown fences, no explanation."
    raw = ask_gemini(full_prompt)
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)
 
def render_bullet_cards(items, card_type=""):
    html = ""
    for item in items:
        html += f'<div class="insight-card {card_type}">{item}</div>'
    st.markdown(html, unsafe_allow_html=True)
 
def render_section_header(icon, label):
    st.markdown(f"""
    <div class="section-header">
        <span class="icon">{icon}</span>
        <h3>{label}</h3>
    </div>""", unsafe_allow_html=True)
 
def render_question_card(q_type, q_text, number):
    st.markdown(f"""
    <div class="question-card">
        <div class="q-type">{q_type} · Q{number}</div>
        <div class="q-text">{q_text}</div>
    </div>""", unsafe_allow_html=True)
 
def generate_pdf_report(sections: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=50, rightMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []
    title_style = ParagraphStyle('Title2', parent=styles['Title'],
                                  fontSize=22, spaceAfter=10, textColor=rl_colors.HexColor("#1a1a2e"))
    story.append(Paragraph("AI Placement Readiness Report", title_style))
    story.append(Spacer(1, 20))
    for title, content in sections.items():
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(Spacer(1, 8))
        if isinstance(content, list):
            for item in content:
                story.append(Paragraph(f"• {item}", styles["Normal"]))
                story.append(Spacer(1, 4))
        else:
            for line in str(content).split("\n"):
                if line.strip():
                    story.append(Paragraph(line.strip(), styles["Normal"]))
                    story.append(Spacer(1, 4))
        story.append(Spacer(1, 16))
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
 
def score_color_class(score):
    if score >= 75: return "high"
    if score >= 50: return "mid"
    return "low"
 
# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Placement Readiness", page_icon="🎯", layout="wide")
 
st.markdown("""
<div class="main-header">
    <h1>🎯 Placement Readiness System</h1>
    <p>AI-Powered · Interview Intelligence · Career Acceleration</p>
</div>
""", unsafe_allow_html=True)
 
# Session state init
defaults = {
    "resume_text": "",
    "analysis_json": None,
    "questions_json": None,
    "jd_match_json": None,
    "chat_history": [],
    "readiness_score": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
 
# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📄 Resume Upload")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if uploaded_file:
        st.session_state.resume_text = extract_text(uploaded_file)
        st.success("✅ Resume loaded!")
        with st.expander("Preview text"):
            st.write(st.session_state.resume_text[:800])
 
    st.divider()
 
    # Readiness Score in sidebar
    if st.session_state.readiness_score is not None:
        score = st.session_state.readiness_score
        cls = score_color_class(score)
        st.markdown(f"""
        <div style="text-align:center; padding: 1rem 0;">
            <div style="font-size:0.7rem; color:#888; letter-spacing:2px; text-transform:uppercase; margin-bottom:0.5rem;">Overall Readiness</div>
            <div class="score-badge {cls}" style="font-size:2rem; padding: 0.5rem 1.5rem;">{score}%</div>
            <div class="readiness-bar-wrap" style="margin-top:1rem;">
                <div class="readiness-bar" style="width:{score}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
resume = st.session_state.resume_text
 
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
 
# ══════════════════════════════════════════════
# TAB 1 — Resume Analysis
# ══════════════════════════════════════════════
with tab1:
    if not resume:
        st.info("⬅️ Upload your resume from the sidebar to get started.")
    else:
        col_btn, col_space = st.columns([1, 3])
        with col_btn:
            analyze_btn = st.button("🔍 Analyze Resume", key="analyze")
 
        if analyze_btn:
            with st.spinner("Analyzing your resume with AI..."):
                prompt = f"""
You are an expert recruiter and career coach. Analyze this resume and return a JSON object with EXACTLY these keys:
{{
  "overall_score": <integer 0-100>,
  "strengths": ["short bullet 1", "short bullet 2", ...],  // 4-6 items, max 15 words each
  "weaknesses": ["short bullet 1", ...],                   // 3-5 items
  "suggestions": ["actionable tip 1", ...],                // 4-6 items
  "ats_tips": ["ats tip 1", ...],                          // 3-5 items
  "skill_scores": {{                                        // rate each skill area 0-10
    "Technical Skills": <int>,
    "Communication": <int>,
    "Experience": <int>,
    "Projects": <int>,
    "Education": <int>,
    "Certifications": <int>
  }}
}}
Resume:
{resume}
"""
                try:
                    data = ask_gemini_json(prompt)
                    st.session_state.analysis_json = data
                    st.session_state.readiness_score = data.get("overall_score", 0)
                except Exception as e:
                    st.error(f"Parsing error: {e}")
 
        data = st.session_state.analysis_json
        if data:
            # Score cards row
            score = data.get("overall_score", 0)
            strengths_count = len(data.get("strengths", []))
            suggestions_count = len(data.get("suggestions", []))
            ats_count = len(data.get("ats_tips", []))
 
            c1, c2, c3, c4 = st.columns(4)
            for col, number, label in [
                (c1, f"{score}", "Overall Score"),
                (c2, f"{strengths_count}", "Strengths Found"),
                (c3, f"{suggestions_count}", "Improvements"),
                (c4, f"{ats_count}", "ATS Tips"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="score-card">
                        <div class="score-number">{number}</div>
                        <div class="score-label">{label}</div>
                    </div>""", unsafe_allow_html=True)
 
            st.markdown("<br>", unsafe_allow_html=True)
 
            # Radar chart
            skill_scores = data.get("skill_scores", {})
            if skill_scores:
                categories = list(skill_scores.keys())
                values = list(skill_scores.values())
                values_closed = values + [values[0]]
                categories_closed = categories + [categories[0]]
 
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values_closed,
                    theta=categories_closed,
                    fill='toself',
                    fillcolor='rgba(123, 47, 247, 0.15)',
                    line=dict(color='#7b2ff7', width=2),
                    name='Your Profile'
                ))
                fig.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0, 10],
                                        gridcolor='rgba(255,255,255,0.08)',
                                        tickcolor='rgba(255,255,255,0.3)',
                                        tickfont=dict(color='#888', size=10)),
                        angularaxis=dict(gridcolor='rgba(255,255,255,0.08)',
                                         tickfont=dict(color='#ccc', size=11))
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    margin=dict(t=30, b=30, l=30, r=30),
                    height=340
                )
                st.plotly_chart(fig, use_container_width=True)
 
            # Bullet sections in 2 columns
            col_l, col_r = st.columns(2)
            with col_l:
                render_section_header("💪", "Strengths")
                render_bullet_cards(data.get("strengths", []), "strength")
 
                render_section_header("⚠️", "Weaknesses")
                render_bullet_cards(data.get("weaknesses", []), "weakness")
 
            with col_r:
                render_section_header("💡", "Suggestions")
                render_bullet_cards(data.get("suggestions", []), "suggestion")
 
                render_section_header("🤖", "ATS Optimization")
                render_bullet_cards(data.get("ats_tips", []), "ats")
 
# ══════════════════════════════════════════════
# TAB 2 — Interview Questions
# ══════════════════════════════════════════════
with tab2:
    if not resume:
        st.info("⬅️ Upload your resume from the sidebar.")
    else:
        col_btn2, _ = st.columns([1, 3])
        with col_btn2:
            gen_btn = st.button("⚡ Generate Questions", key="genq")
 
        if gen_btn:
            with st.spinner("Generating tailored questions..."):
                prompt = f"""
Based on this resume, generate interview questions as JSON:
{{
  "technical": ["q1", "q2", "q3", "q4", "q5"],
  "behavioral": ["q1", "q2", "q3"],
  "situational": ["q1", "q2"]
}}
Each question max 25 words. Be specific to the resume content.
Resume:
{resume}
"""
                try:
                    data = ask_gemini_json(prompt)
                    st.session_state.questions_json = data
                except Exception as e:
                    st.error(f"Parsing error: {e}")
 
        qdata = st.session_state.questions_json
        if qdata:
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                render_section_header("⚙️", "Technical Questions")
                for i, q in enumerate(qdata.get("technical", []), 1):
                    render_question_card("TECHNICAL", q, i)
 
                render_section_header("🎭", "Situational Questions")
                for i, q in enumerate(qdata.get("situational", []), 1):
                    render_question_card("SITUATIONAL", q, i)
 
            with col_q2:
                render_section_header("🧠", "Behavioral Questions")
                for i, q in enumerate(qdata.get("behavioral", []), 1):
                    render_question_card("BEHAVIORAL", q, i)
 
            # Answer Evaluator
            st.divider()
            st.markdown("### ✍️ Answer Evaluator")
            selected_q = st.text_input("Paste a question to answer:", placeholder="Copy any question from above...")
            user_answer = st.text_area("Your Answer:", height=120, placeholder="Type your answer here...")
 
            if st.button("🎯 Evaluate My Answer"):
                if selected_q and user_answer:
                    with st.spinner("Evaluating your answer..."):
                        eval_prompt = f"""
Evaluate this interview answer and return JSON:
{{
  "score": <integer 0-10>,
  "good_points": ["point 1", "point 2", ...],     // 2-4 items
  "missing_points": ["point 1", "point 2", ...],  // 2-4 items
  "model_answer": ["sentence 1", "sentence 2", "sentence 3", "sentence 4"]  // 3-5 bullet sentences
}}
Question: {selected_q}
Answer: {user_answer}
"""
                        try:
                            edata = ask_gemini_json(eval_prompt)
                            score = edata.get("score", 0)
                            cls = score_color_class(score * 10)
                            st.markdown(f"""
                            <div style="display:flex; align-items:center; gap:1rem; margin:1rem 0;">
                                <span style="color:#888; font-size:0.8rem; letter-spacing:2px; text-transform:uppercase;">Answer Score</span>
                                <span class="score-badge {cls}">{score}/10</span>
                            </div>
                            """, unsafe_allow_html=True)
 
                            c1e, c2e, c3e = st.columns(3)
                            with c1e:
                                render_section_header("✅", "What Was Good")
                                render_bullet_cards(edata.get("good_points", []), "strength")
                            with c2e:
                                render_section_header("❌", "What Was Missing")
                                render_bullet_cards(edata.get("missing_points", []), "weakness")
                            with c3e:
                                render_section_header("⭐", "Model Answer")
                                render_bullet_cards(edata.get("model_answer", []), "suggestion")
                        except Exception as e:
                            st.error(f"Parsing error: {e}")
                else:
                    st.warning("Please enter both a question and your answer.")
 
# ══════════════════════════════════════════════
# TAB 3 — Mock Interview
# ══════════════════════════════════════════════
with tab3:
    if not resume:
        st.info("⬅️ Upload your resume from the sidebar.")
    else:
        col_start, _ = st.columns([1, 3])
        with col_start:
            if st.button("🎬 Start / Reset Interview"):
                with st.spinner("Preparing your interviewer..."):
                    intro_prompt = f"""
You are a sharp, professional interviewer. The candidate's resume is below.
Greet them briefly and ask your first specific question based on their background.
Keep it to 2-3 sentences.
Resume: {resume}
"""
                    first_msg = ask_gemini(intro_prompt)
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": first_msg}
                    ]
 
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
 
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
Continue the interview. Give 1 line of feedback on their last answer, then ask the next question.
Keep it concise (2-3 sentences total).
"""
            with st.spinner("Interviewer is responding..."):
                reply = ask_gemini(follow_up_prompt)
 
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.write(reply)
 
# ══════════════════════════════════════════════
# TAB 4 — JD Matcher
# ══════════════════════════════════════════════
with tab4:
    if not resume:
        st.info("⬅️ Upload your resume from the sidebar.")
    else:
        jd_text = st.text_area("Paste the Job Description here:", height=200,
                               placeholder="Paste the job description you're targeting...")
 
        if st.button("🔍 Match Resume to JD"):
            if jd_text.strip():
                with st.spinner("Matching your profile..."):
                    match_prompt = f"""
Compare this resume against the job description. Return JSON:
{{
  "match_score": <integer 0-100>,
  "matching_skills": ["skill1", "skill2", ...],   // 5-10 items
  "missing_skills": ["skill1", "skill2", ...],     // 3-8 items
  "recommendations": ["tip1", "tip2", ...],        // 4-6 actionable items
  "verdict": "one sentence overall verdict"
}}
Resume: {resume}
Job Description: {jd_text}
"""
                    try:
                        data = ask_gemini_json(match_prompt)
                        st.session_state.jd_match_json = data
                    except Exception as e:
                        st.error(f"Parsing error: {e}")
            else:
                st.warning("Please paste a job description.")
 
        jdata = st.session_state.jd_match_json
        if jdata:
            score = jdata.get("match_score", 0)
            cls = score_color_class(score)
 
            # Match score hero
            st.markdown(f"""
            <div style="text-align:center; padding: 1.5rem 0;">
                <div style="font-size:0.75rem; color:#888; letter-spacing:3px; text-transform:uppercase; margin-bottom:0.8rem;">Resume Match Score</div>
                <div class="score-badge {cls}" style="font-size:2.5rem; padding: 0.6rem 2rem;">{score}%</div>
                <div class="readiness-bar-wrap" style="max-width:400px; margin:1rem auto;">
                    <div class="readiness-bar" style="width:{score}%;"></div>
                </div>
                <div style="color:#aaa; font-size:0.9rem; margin-top:0.5rem; font-style:italic;">"{jdata.get('verdict', '')}"</div>
            </div>
            """, unsafe_allow_html=True)
 
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                render_section_header("✅", "Matching Skills")
                tags = "".join([f'<span class="skill-tag match">{s}</span>' for s in jdata.get("matching_skills", [])])
                st.markdown(f"<div style='margin-top:0.5rem;'>{tags}</div>", unsafe_allow_html=True)
 
            with col_m2:
                render_section_header("❌", "Missing Skills")
                tags = "".join([f'<span class="skill-tag missing">{s}</span>' for s in jdata.get("missing_skills", [])])
                st.markdown(f"<div style='margin-top:0.5rem;'>{tags}</div>", unsafe_allow_html=True)
 
            with col_m3:
                render_section_header("🎯", "How to Improve")
                render_bullet_cards(jdata.get("recommendations", []), "suggestion")
 
# ══════════════════════════════════════════════
# TAB 5 — Download Report
# ══════════════════════════════════════════════
with tab5:
    has_content = any([
        st.session_state.analysis_json,
        st.session_state.questions_json,
        st.session_state.jd_match_json
    ])
 
    if not has_content:
        st.info("Run Resume Analysis, Generate Questions, and/or JD Match first to include them in the report.")
    else:
        st.markdown("### 📄 Your Report Preview")
 
        if st.session_state.analysis_json:
            d = st.session_state.analysis_json
            render_section_header("📊", "Resume Analysis Summary")
            c1p, c2p = st.columns(2)
            with c1p:
                render_bullet_cards(d.get("strengths", []), "strength")
            with c2p:
                render_bullet_cards(d.get("suggestions", []), "suggestion")
 
        if st.session_state.questions_json:
            q = st.session_state.questions_json
            render_section_header("❓", "Interview Questions")
            all_q = (
                [f"[Technical] {x}" for x in q.get("technical", [])] +
                [f"[Behavioral] {x}" for x in q.get("behavioral", [])] +
                [f"[Situational] {x}" for x in q.get("situational", [])]
            )
            render_bullet_cards(all_q)
 
        if st.session_state.jd_match_json:
            jd = st.session_state.jd_match_json
            render_section_header("🔍", "JD Match Summary")
            render_bullet_cards(jd.get("recommendations", []), "suggestion")
 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬇️ Generate & Download PDF Report"):
            sections = {}
            if st.session_state.analysis_json:
                d = st.session_state.analysis_json
                sections["Resume Analysis"] = (
                    d.get("strengths", []) + d.get("weaknesses", []) + d.get("suggestions", [])
                )
            if st.session_state.questions_json:
                q = st.session_state.questions_json
                sections["Interview Questions"] = (
                    [f"[Technical] {x}" for x in q.get("technical", [])] +
                    [f"[Behavioral] {x}" for x in q.get("behavioral", [])] +
                    [f"[Situational] {x}" for x in q.get("situational", [])]
                )
            if st.session_state.jd_match_json:
                jd = st.session_state.jd_match_json
                sections["JD Match"] = (
                    [f"Match Score: {jd.get('match_score', 0)}%"] +
                    jd.get("recommendations", [])
                )
            pdf_bytes = generate_pdf_report(sections)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name="placement_readiness_report.pdf",
                mime="application/pdf"
            )
 
