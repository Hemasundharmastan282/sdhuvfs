import os
from datetime import datetime
import json

def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_transcript(role_title, transcript_text):
    """
    Save the interview transcript as a .txt file.
    """
    os.makedirs("data/transcripts", exist_ok=True)
    filename = f"data/transcripts/{role_title}_{_timestamp()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(transcript_text)
    return filename

def save_report(role_title, report_text):
    """
    Save the AI-generated evaluation report as a .txt file.
    """
    os.makedirs("data/reports", exist_ok=True)
    filename = f"data/reports/{role_title}_{_timestamp()}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    return filename

def save_recording(file_bytes, role_title):
    """
    Save raw video/audio bytes as .webm file.
    This function would be called with bytes from the webrtc streamer
    if full video recording is needed.
    """
    os.makedirs("data/recordings", exist_ok=True)
    filename = f"data/recordings/{role_title}_{_timestamp()}.webm"
    with open(filename, "wb") as f:
        f.write(file_bytes)
    return filename

def save_session_log(role_title, log_data):
    """
    Save detailed Q&A session logs as JSON.
    """
    os.makedirs("data/session_logs", exist_ok=True)
    filename = f"data/session_logs/{role_title}_{_timestamp()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=4)
    return filename
