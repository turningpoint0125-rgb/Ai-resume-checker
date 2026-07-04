import os
import re
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

# ======================================================
# PDF AGENT
# ======================================================
def extract_text_from_pdf(file_obj):
    try:
        reader = PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text.strip()
    except Exception:
        return ""


# ======================================================
# BASIC TEXT CLEANER
# ======================================================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ======================================================
# NAME AGENT (LOCAL ONLY)
# ======================================================
def extract_name(resume_text):
    match = re.search(r"(Name|NAME)\s*:\s*(.+)", resume_text)
    if match:
        return match.group(2).strip()
    return "Candidate"


# ======================================================
# SCORING AGENT (STABLE)
# ======================================================
def calculate_match_score(resume_text, job_description):
    jd_words = set(re.findall(r"\w+", job_description.lower()))
    resume_words = set(re.findall(r"\w+", resume_text.lower()))

    if not jd_words:
        return 20

    score = int((len(jd_words & resume_words) / len(jd_words)) * 100)
    return max(20, min(score, 95))


# ======================================================
# LLM EXTRACTION AGENT
# ======================================================
def llm_extract(resume_text, job_description, token):
    client = InferenceClient(
        model="Qwen/Qwen2.5-Coder-7B-Instruct",
        token=token
    )

    system_prompt = """
You are an ATS resume extractor.

RULES:
- NEVER guess age
- If age not written, output: Not Specified
- Extract skills ONLY if present
- Output plain text only

FORMAT:
NAME:
AGE:
MATCHING_SKILLS:
MISSING_SKILLS:
EDUCATION:
"""

    response = client.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}"}
        ],
        temperature=0,
        max_tokens=400
    )

    return response.choices[0].message.content


# ======================================================
# FIELD PARSER (STRICT)
# ======================================================
def parse_field(label, text, default):
    pattern = rf"{label}:\s*(.*)"
    match = re.search(pattern, text)
    return clean_text(match.group(1)) if match else default


# ======================================================
# DECISION AGENT (ONLY SCORE BASED)
# ======================================================
def final_decision(score):
    return "HIRE" if score >= 60 else "REJECT"


# ======================================================
# MAIN MULTI-AGENT ORCHESTRATOR
# ======================================================
@st.cache_data(show_spinner=False)
def analyze_resume(resume_text, job_description):

    name = extract_name(resume_text)
    score = calculate_match_score(resume_text, job_description)
    decision = final_decision(score)

    hf_token = (
        st.secrets.get("HF_TOKEN")
        if hasattr(st, "secrets") and "HF_TOKEN" in st.secrets
        else os.environ.get("HF_TOKEN")
    )

    # -------- FALLBACK (NO LLM) --------
    if not hf_token:
        return {
            "name": name,
            "age": "Not Specified",
            "match_percentage": score,
            "decision": decision,
            "matching_skills": "Detected via keyword match",
            "missing_skills": "Manual review",
            "education": "Not extracted"
        }

    raw = llm_extract(resume_text, job_description, hf_token)

    age = parse_field("AGE", raw, "Not Specified")
    if not re.search(r"\d", age):
        age = "Not Specified"

    skills = parse_field("MATCHING_SKILLS", raw, "None")
    missing = parse_field("MISSING_SKILLS", raw, "None")

    return {
        "name": parse_field("NAME", raw, name),
        "age": age,
        "match_percentage": score,
        "decision": decision,
        "matching_skills": skills,
        "missing_skills": missing,
        "education": parse_field("EDUCATION", raw, "Not Provided")
    }
