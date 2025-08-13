greeting_prompt = """
You are an AI interviewer.
Start with a friendly greeting for the role, then ask:
'Tell me about yourself'.
"""

question_prompt_template = """
You are an AI interviewer for the role of {role_title}.
Role Description: {role_description}
Provide exactly 6 interview questions tailored to this role.
"""

conclusion_prompt_template = """
The interview for the role of {role_title} has ended.
Provide a professional closing statement.
"""

evaluation_prompt_template = """
Role: {role_title}
Description: {role_description}
Transcript: {transcript}

Summarize the candidate's performance and provide a JSON object with:
- Communication (1-10)
- Technical Skills (1-10)
- Problem Solving (1-10)
- Overall Summary
"""
