import streamlit as st
import os
from dotenv import load_dotenv
from modules.assemblyai_stream import AssemblyAIStreamer
from modules.interview_flow import InterviewFlow
from modules.storage import save_transcript, save_report
from main import generate_intro_and_questions, generate_conclusion, evaluate_candidate
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase, RTCConfiguration
import json
import threading
import queue
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import io

# -----------------------------
# Streamlit page setup
# -----------------------------
st.set_page_config(page_title="AI Interview Bot", layout="wide")

load_dotenv()
assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not assemblyai_api_key:
    st.error("❌ ASSEMBLYAI_API_KEY not found in .env")
    st.stop()

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}
body {
    background-color: black;
    color: #f5f5f5;
}
.main .block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 2rem;
    margin: auto;
    position: relative;
    height: 100vh;
}
.stTitle {
    color: #fff;
    text-align: center;
    padding: 20px;
    background-color: rgba(40, 44, 52, 0.6);
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 30px;
}
.stButton > button {
    background-color: #6a0dad;
    color: white;
    font-size: 1rem;
    padding: 0.75rem 2rem;
    border-radius: 12px;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background-color: #4b0082;
    transform: translateY(-2px);
}
.stTextInput, .stTextArea {
    border-radius: 10px;
    border: 1px solid #928dab;
    background-color: rgba(255, 255, 255, 0.1);
    color: #f5f5f5;
}
.stTextInput > div > div > input, .stTextArea > div > textarea {
    background-color: transparent;
    color: #f5f5f5;
}
.st-emotion-cache-163j0c0 {
    background-color: #2e303c;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.webrtc-video-container {
    border: 3px solid #6a0dad;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 250px;
    aspect-ratio: 16/9;
}
.transcript-box {
    background-color: rgba(40, 44, 52, 0.8);
    color: #f5f5f5;
    padding: 15px;
    border-radius: 12px;
    max-height: 200px;
    overflow-y: auto;
    text-align: left;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# PDF Generation Function
# -----------------------------
def create_transcript_pdf(transcript_text, title):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"<b>Interview Transcript for: {title}</b>", styles['h1']))
    story.append(Spacer(1, 12))
    
    for line in transcript_text.split('\n'):
        if line.startswith('Bot:'):
            story.append(Paragraph(f"<b>{line}</b>", styles['Normal']))
        elif line.startswith('Candidate:'):
            story.append(Paragraph(line, styles['Normal']))
        else:
            story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Session state init
# -----------------------------
if 'page' not in st.session_state: st.session_state.page = "landing"
if 'role_title' not in st.session_state: st.session_state.role_title = ""
if 'role_description' not in st.session_state: st.session_state.role_description = ""
if 'evaluation' not in st.session_state: st.session_state.evaluation = None
if 'transcript_path' not in st.session_state: st.session_state.transcript_path = None
if 'report_path' not in st.session_state: st.session_state.report_path = None
if 'video_recording_path' not in st.session_state: st.session_state.video_recording_path = None
if 'interview_started' not in st.session_state: st.session_state.interview_started = False
if 'questions' not in st.session_state: st.session_state.questions = []
if 'conclusion_text' not in st.session_state: st.session_state.conclusion_text = ""
if 'current_question_index' not in st.session_state: st.session_state.current_question_index = 0
if 'full_transcript' not in st.session_state: st.session_state.full_transcript = ""
if 'streamer' not in st.session_state: st.session_state.streamer = AssemblyAIStreamer(api_key=assemblyai_api_key)
if 'webrtc_ctx' not in st.session_state: st.session_state.webrtc_ctx = None
if 'interview_flow_initialized' not in st.session_state: st.session_state.interview_flow_initialized = False
if 'show_questions' not in st.session_state: st.session_state.show_questions = False


# A simple video processor to handle video recording
class VideoRecorder(VideoProcessorBase):
    def __init__(self) -> None:
        pass
    def recv(self, frame):
        return frame

# -----------------------------
# Pages
# -----------------------------
def landing_page():
    st.markdown("<h1 class='stTitle'>Welcome to AI Interview Bot</h1>", unsafe_allow_html=True)
    if st.button("Start Interview Bot"):
        st.session_state.page = "interview"
        st.experimental_rerun()

def interview_page():
    if not st.session_state.interview_started:
        st.markdown("<h1 class='stTitle'>AI Interview Bot</h1>", unsafe_allow_html=True)
        st.markdown("### Enter Role Details to Begin")
        role_title = st.text_input("Role Title", value=st.session_state.role_title)
        role_description = st.text_area("Role Description", value=st.session_state.role_description)
        if st.button("Start Interview"):
            if not role_title.strip() or not role_description.strip():
                st.warning("Please enter both Role Title and Role Description before starting.")
                return

            st.session_state.role_title = role_title.strip()
            st.session_state.role_description = role_description.strip()
            st.session_state.interview_started = True

            with st.spinner("Generating interview questions..."):
                intro_and_questions_text = generate_intro_and_questions(role_title, role_description)
                st.session_state.questions = [line.strip() for line in intro_and_questions_text.strip().split('\n') if line.strip()]
                st.session_state.conclusion_text = generate_conclusion(role_title, role_description)
            
            st.session_state.interview_flow_initialized = True
            st.session_state.current_question_index = 0
            st.experimental_rerun()
    else:
        st.markdown("<h1 class='stTitle'>AI Interview Bot</h1>", unsafe_allow_html=True)

        # Video feed in the bottom-right corner
        st.markdown('<div class="webrtc-video-container">', unsafe_allow_html=True)
        rtc_config = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            audio_sink=False
        )
        webrtc_ctx = webrtc_streamer(
            key="interview",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": True, "audio": True},
            async_processing=False, 
            video_processor_factory=VideoRecorder,
            rtc_configuration=rtc_config
        )
        st.session_state.webrtc_ctx = webrtc_ctx
        st.markdown('</div>', unsafe_allow_html=True)

        if webrtc_ctx.state.playing and st.session_state.interview_flow_initialized:
            interview = InterviewFlow(st.session_state.questions, st.session_state.conclusion_text)
            interview.index = st.session_state.current_question_index
            
            # Start streamer only once the webrtc component is confirmed to be playing
            if not st.session_state.streamer.listening:
                st.session_state.streamer.start(webrtc_ctx)

            # Display the bot's conversation in the middle
            bot_placeholder = st.container()
            
            latest_transcript = st.session_state.streamer.get_latest_transcript()

            if latest_transcript:
                st.session_state.full_transcript += f"Candidate: {latest_transcript}\n"
                
                # Check for special phrases and update interview flow
                interview.check_for_commands(latest_transcript.lower(), st.session_state.current_question_index)
                if interview.advance_to_next_question:
                    st.session_state.current_question_index += 1
                    st.session_state.full_transcript += f"Bot: {interview.current_question()}\n"
                    interview.advance_to_next_question = False
                    st.experimental_rerun()
                elif interview.confirmation_needed:
                    bot_placeholder.markdown(f"**Bot:** Are you sure for going to next question?")
                    st.session_state.full_transcript += f"Bot: Are you sure for going to next question?\n"
                    interview.confirmation_needed = False

            # Display current bot question
            with bot_placeholder:
                if not interview.is_over():
                    current_question = interview.current_question()
                    st.markdown(f"<div style='text-align: center; font-size: 1.5rem;'><b>Bot:</b> {current_question}</div>", unsafe_allow_html=True)

            # Buttons below the centered question
            button_col1, button_col2, button_col3 = st.columns([1, 1, 1])
            with button_col2:
                if st.session_state.current_question_index == 0:
                    if st.button("Start Questions"):
                        st.session_state.current_question_index += 1
                        st.session_state.full_transcript += f"Bot: {interview.current_question()}\n"
                        st.experimental_rerun()
                elif interview.is_over():
                    st.markdown(f"<div style='text-align: center; font-size: 1.5rem;'><b>Bot:</b> {interview.conclusion_text}</div>", unsafe_allow_html=True)
                    st.session_state.streamer.stop()
                    st.session_state.page = "post_interview"
                    st.experimental_rerun()
                elif st.session_state.current_question_index >= len(st.session_state.questions) - 1:
                    if st.button("End Interview"):
                        st.session_state.interview_started = False
                        st.session_state.page = "post_interview"
                        st.experimental_rerun()
                else:
                    if st.button("Next Question"):
                        st.session_state.current_question_index += 1
                        st.experimental_rerun()

        elif not webrtc_ctx.state.playing:
            st.warning("Video stream not active. Please allow camera and microphone access.")
            if st.button("Retry"):
                st.experimental_rerun()
            
def post_interview_page():
    st.markdown("<h1 class='stTitle'>Interview Completed</h1>", unsafe_allow_html=True)
    st.success("The interview has concluded. You can find your report and transcript below.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Take another interview"):
            st.session_state.page = "landing"
            for key in st.session_state.keys():
                if key not in ['streamer', 'webrtc_ctx']:
                    del st.session_state[key]
            st.experimental_rerun()

    with col2:
        if st.button("Summary Report"):
            st.session_state.page = "summary"
            st.experimental_rerun()

    pdf_buffer = create_transcript_pdf(st.session_state.full_transcript, st.session_state.role_title)
    st.download_button(
        label="Download Full Transcript as PDF",
        data=pdf_buffer,
        file_name=f"{st.session_state.role_title}_transcript.pdf",
        mime="application/pdf"
    )

def summary_page():
    st.markdown("<h1 class='stTitle'>Candidate Evaluation Summary</h1>", unsafe_allow_html=True)
    if st.session_state.evaluation:
        st.text(st.session_state.evaluation)
    else:
        st.write("No evaluation summary available.")

    st.markdown("---")
    st.markdown("### Full Conversation Transcript")
    # Corrected display of the full conversation
    transcript_lines = st.session_state.full_transcript.split('\n')
    bot_question = ""
    candidate_answer = ""
    for line in transcript_lines:
        if line.startswith("Bot:"):
            # If we have a previous Q&A pair, display it
            if bot_question and candidate_answer:
                st.markdown(f"**Bot:** {bot_question}")
                st.markdown(f"<i>Candidate:</i> {candidate_answer}", unsafe_allow_html=True)
                st.markdown("---")
            # Start a new Q&A pair
            bot_question = line.replace("Bot: ", "")
            candidate_answer = ""
        elif line.startswith("Candidate:"):
            candidate_answer += line.replace("Candidate: ", "")
        
    # Display the last Q&A pair if it exists
    if bot_question:
        st.markdown(f"**Bot:** {bot_question}")
        if candidate_answer:
            st.markdown(f"<i>Candidate:</i> {candidate_answer}", unsafe_allow_html=True)
        st.markdown("---")
    
    if st.button("Back to Homepage"):
        st.session_state.page = "landing"
        st.experimental_rerun()
    
# -----------------------------
# Main routing
# -----------------------------
if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "interview":
    interview_page()
elif st.session_state.page == "post_interview":
    post_interview_page()
elif st.session_state.page == "summary":
    summary_page()
