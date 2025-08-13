import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

client = OpenAI(api_key=API_KEY, base_url="https://api.groq.com/openai/v1")

def safe_get_response_content(response):
    if response and response.choices and len(response.choices) > 0:
        return response.choices[0].message.content.strip()
    return "No response generated."

def generate_intro_and_questions(role_title: str, role_description: str) -> str:
    prompt = f"""
You are an AI interviewer.
1. Start with a friendly greeting for the {role_title} role.
2. Include the first profile question: 'Tell me about yourself'.
3. Provide exactly 6 interview questions tailored to this role.
Role Description: {role_description}
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are an expert interviewer."},
            {"role": "user", "content": prompt}
        ],
    )
    return safe_get_response_content(response)

def generate_conclusion(role_title: str, role_description: str) -> str:
    prompt = f"""
You are an AI interviewer. The interview for the {role_title} role has concluded.
Provide a short, professional closing statement.
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are an expert interviewer."},
            {"role": "user", "content": prompt}
        ],
    )
    return safe_get_response_content(response)

def evaluate_candidate(role_title: str, role_description: str, transcript_text: str) -> str:
    prompt = f"""
Role: {role_title}
Description: {role_description}
Transcript: {transcript_text}

Summarize the candidate's performance and provide a JSON object with:
- Communication (1-10)
- Technical Skills (1-10)
- Problem Solving (1-10)
- Overall Summary
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are an expert interviewer."},
            {"role": "user", "content": prompt}
        ],
    )
    return safe_get_response_content(response)
