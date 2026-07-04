import os
import re
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

# 1. Fetch token safely from Streamlit secrets or local env variables
hf_token = st.secrets.get("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")

# 2. Model used for all three analysis chains.
# Qwen2.5-7B-Instruct is an ungated instruct model widely available across
# Hugging Face's Inference Providers. Override via HF_MODEL_ID in secrets/env
# if you want to point this at a different provider-hosted model.
MODEL_ID = st.secrets.get("HF_MODEL_ID") or os.getenv("HF_MODEL_ID") or "Qwen/Qwen2.5-7B-Instruct"


def _get_client() -> InferenceClient:
    """Builds a Hugging Face Inference Providers client.

    provider='auto' lets Hugging Face route the request to whichever
    provider currently hosts MODEL_ID (Together, Novita, Fireworks, etc.),
    which replaces the old, now-shut-down api-inference.huggingface.co path.
    """
    if not hf_token:
        st.error("🔑 Missing Hugging Face token. Add HUGGINGFACEHUB_API_TOKEN to the Secrets panel on Streamlit Cloud.")
        st.stop()
    return InferenceClient(model=MODEL_ID, provider="auto", token=hf_token)


def _chat(client: InferenceClient, prompt: str, max_tokens: int = 600) -> str:
    """Sends a single-turn chat completion request and returns the text response."""
    try:
        completion = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        st.error(
            f"AI request failed ({e}). The configured model '{MODEL_ID}' may not be "
            "available through any Hugging Face Inference Provider right now. Try "
            "setting HF_MODEL_ID in your Streamlit secrets to a different provider-hosted "
            "model, e.g. 'meta-llama/Llama-3.1-8B-Instruct' or 'mistralai/Mistral-7B-Instruct-v0.3'."
        )
        st.stop()


def extract_text_from_pdf(pdf_file):
    """Safely extracts clean string text from an uploaded PDF binary stream."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF data: {e}")
        return ""


def analyze_resume(resume_text, job_description):
    """Runs the three-stage analysis pipeline (profile, ATS match, decision) for one resume."""
    client = _get_client()

    # --- Stage 1: Candidate Basic Information Extraction ---
    profile_prompt = f"""Extract the candidate's full name and their highest educational degree from the following resume text.
If you cannot find the name, use 'Unknown Candidate'.
Format your response exactly like this:
Name: [Name here]
Education: [Education here]

Resume: {resume_text}
"""
    profile_output = _chat(client, profile_prompt, max_tokens=150)

    name = "Unknown"
    education = "Not Specified"
    name_match = re.search(r"Name:\s*(.*)", profile_output)
    edu_match = re.search(r"Education:\s*(.*)", profile_output)
    if name_match: name = name_match.group(1).strip()
    if edu_match: education = edu_match.group(1).strip()

    # --- Stage 2: Structural ATS Keyword Analysis ---
    analysis_prompt = f"""You are an expert ATS (Applicant Tracking System). Compare the Resume against the Job Description (JD).
1. Provide a Match Percentage (0% to 100%) based on skills, experience, and role alignment.
2. List the key skills the candidate possesses that match the JD.
3. List critical skills missing from the resume.

Job Description: {job_description}
Resume: {resume_text}

Respond strictly in this format:
MATCH_PERCENTAGE: [Only the number, e.g., 85]
MATCHING_SKILLS: [Comma separated list]
MISSING_SKILLS: [Comma separated list]
"""
    analysis_output = _chat(client, analysis_prompt, max_tokens=400)

    match_pct = 50
    pct_match = re.search(r"MATCH_PERCENTAGE:\s*(\d+)", analysis_output)
    if pct_match:
        match_pct = int(pct_match.group(1))

    matching_skills = ""
    missing_skills = ""
    match_s_match = re.search(r"MATCHING_SKILLS:\s*(.*)", analysis_output)
    miss_s_match = re.search(r"MISSING_SKILLS:\s*(.*)", analysis_output)
    if match_s_match: matching_skills = match_s_match.group(1).strip()
    if miss_s_match: missing_skills = miss_s_match.group(1).strip()

    # --- Stage 3: Automated Decision & Custom Question Generation ---
    decision_prompt = f"""Based on a {match_pct}% compatibility match for this Job Description, make a hiring decision.
If the match is 70% or higher, output 'HIRE'. Otherwise, output 'REJECT'.
Also, generate 5 tailored technical interview questions based on the missing or listed skills to evaluate the candidate.

Job Description: {job_description}

Respond strictly in this format:
DECISION: [HIRE or REJECT]
QUESTIONS:
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]
"""
    decision_output = _chat(client, decision_prompt, max_tokens=500)

    decision = "REJECT"
    if "HIRE" in decision_output.split("QUESTIONS:")[0]:
        decision = "HIRE"

    questions = decision_output.split("QUESTIONS:")[-1].strip() if "QUESTIONS:" in decision_output else "No questions generated."

    return {
        "name": name,
        "education": education,
        "match_percentage": match_pct,
        "decision": decision,
        "questions": questions,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills
    }
