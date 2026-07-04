import os
import re
import time
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

# =========================================================
# PDF AGENT
# =========================================================
def extract_text_from_pdf(file_obj) -> str:
    try:
        reader = PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception:
        return ""


# =========================================================
# TEXT SANITIZER AGENT
# =========================================================
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\{\}\[\]\"']", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================================================
# NAME EXTRACTION AGENT (LOCAL SAFE)
# =========================================================
def extract_candidate_name(resume_text: str) -> str:
    patterns = [
        r"Name:\s*([A-Za-z\s]+)",
        r"CANDIDATE PROFILE:\s*([A-Za-z\s]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Candidate"


# =========================================================
# SCORING AGENT (DETERMINISTIC)
# =========================================================
def keyword_match_score(resume_text: str, job_description: str) -> int:
    jd_words = set(re.findall(r"\w+", job_description.lower()))
    resume_words = set(re.findall(r"\w+", resume_text.lower()))

    if not jd_words:
        return 15

    score = int((len(jd_words & resume_words) / len(jd_words)) * 100)
    return max(15, min(score, 95))


# =========================================================
# LLM EXTRACTION AGENT
# =========================================================
def llm_extract(resume_text: str, job_description: str, token: str) -> str:
    client = InferenceClient(
        model="Qwen/Qwen2.5-Coder-7B-Instruct",
        token=token
    )

    system_prompt = """
You are an ATS extraction engine.

RULES:
- DO NOT guess age
- If age not written → "Not Disclosed"
- Output plain text only
- Follow format strictly

FORMAT:
NAME:
AGE:
MATCHING_SKILLS:
MISSING_SKILLS:
EDUCATION:
QUESTIONS:
1.
2.
3.
4.
5.
"""

    response = client.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}"}
        ],
        max_tokens=500,
        temperature=0
    )

    return response.choices[0].message.content


# =========================================================
# PARSING AGENT
# =========================================================
def parse_field(tag: str, text: str, default=""):
    pattern = rf"{tag}:\s*(.*?)(?=\n[A-Z_]+:|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return clean_text(match.group(1)) if match else default


# =========================================================
# DECISION AGENT (FINAL AUTHORITY)
# =========================================================
def decision_agent(score: int) -> str:
    return "HIRE" if score >= 60 else "REJECT"


# =========================================================
# MAIN ORCHESTRATOR (MULTI-AGENT CONTROLLER)
# =========================================================
@st.cache_data(show_spinner=False)
def analyze_resume(resume_text: str, job_description: str) -> dict:

    # ---- LOCAL AGENTS ----
    name = extract_candidate_name(resume_text)
    score = keyword_match_score(resume_text, job_description)
    decision = decision_agent(score)

    # ---- TOKEN ----
    hf_token = (
        st.secrets.get("HF_TOKEN")
        if hasattr(st, "secrets")
        else os.environ.get("HF_TOKEN")
    )

    # ---- FALLBACK ----
    if not hf_token:
        return {
            "name": name,
            "age": "Not Disclosed",
            "match_percentage": score,
            "decision": decision,
            "matching_skills": "Keyword based extraction",
            "missing_skills": "Manual review required",
            "education": "Not detected",
            "questions": default_questions()
        }

    # ---- LLM AGENT ----
    raw = llm_extract(resume_text, job_description, hf_token)

    age = parse_field("AGE", raw, "Not Disclosed")
    if not re.search(r"\d", age):
        age = "Not Disclosed"

    skills = parse_field("MATCHING_SKILLS", raw, "")
    skills = ", ".join(sorted(set(s.strip().lower() for s in skills.split(",") if s)))

    return {
        "name": parse_field("NAME", raw, name),
        "age": age,
        "match_percentage": score,
        "decision": decision,
        "matching_skills": skills or "None",
        "missing_skills": parse_field("MISSING_SKILLS", raw, "None"),
        "education": parse_field("EDUCATION", raw, "Not Provided"),
        "questions": parse_field("QUESTIONS", raw, default_questions())
    }


# =========================================================
# QUESTIONS AGENT
# =========================================================
def default_questions():
    return """1. Explain your experience with Python-based automation.
2. How do you ensure model reliability in production?
3. Describe a scalable system you built.
4. How do you handle unstructured data?
5. Explain a challenge you solved in deployment."""
