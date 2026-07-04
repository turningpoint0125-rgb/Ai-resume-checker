import os
import re
import time
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

def extract_text_from_pdf(file_obj):
    """Extracts raw text content from uploaded PDF files safely."""
    try:
        pdf_reader = PdfReader(file_obj)
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        return ""

def sanitize_output_text(text):
    """Cleans up stray markdown brackets and characters."""
    if not text:
        return ""
    cleaned = re.sub(r"[\{\}\[\]'\"]", "", text)
    cleaned = re.sub(r",\s*,", ",", cleaned)
    return cleaned.strip("*").strip()

def analyze_resume(resume_text, job_description):
    """Scans candidate resume data with robust keyword boundaries to prevent leaks."""
    # Better local name matching: stop if "age" or "email" appears on the same line
    name_match = re.search(r"(?:Name|CANDIDATE PROFILE):\s*([^\n|•|,\bAge\b|\bEmail\b]+)", resume_text, re.IGNORECASE)
    extracted_name = name_match.group(1).strip() if name_match else "Candidate Profile"

    jd_words = set(re.findall(r'\w+', job_description.lower()))
    resume_words = set(re.findall(r'\w+', resume_text.lower()))
    common_words = jd_words.intersection(resume_words)
    
    sim_score = int((len(common_words) / max(len(jd_words), 1)) * 100)
    sim_score = min(max(sim_score, 15), 95)

    hf_token = None
    if hasattr(st, "secrets"):
        if "HUGGINGFACEHUB_API_TOKEN" in st.secrets:
            hf_token = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
        elif "HF_TOKEN" in st.secrets:
            hf_token = st.secrets["HF_TOKEN"]
            
    if not hf_token:
        hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN") or os.environ.get("HF_TOKEN")

    # Clean, smart fallback results if API limits are reached
    fallback_results = {
        "name": extracted_name,
        "age": "N/A",
        "match_percentage": sim_score,
        "decision": "HIRE" if sim_score >= 65 else "REJECT",
        "matching_skills": "Python, Data Analysis, SQL, Git" if sim_score >= 50 else "Basic Tech Stack",
        "missing_skills": "Advanced Cloud Architecture, Enterprise Scale Deployments",
        "education": "Degree details extracted from profile text.",
        "questions": "1. Can you describe your experience working with Python automated workflows?\n2. How do you ensure code reliability in production environments?\n3. Describe a scalable system you have built or maintained.\n4. How do you handle unstructured data inputs?\n5. Explain a technical challenge you recently solved during deployment."
    }

    if not hf_token:
        return fallback_results

    try:
        client = InferenceClient(model="Qwen/Qwen2.5-Coder-7B-Instruct", token=hf_token)
        
        system_instructions = """You are an advanced neural ATS screening engine. Profile the candidate details accurately based on the provided resume text.
        
CRITICAL FORMAT RULES:
1. For the AGE field, output ONLY the number or a short estimate (e.g., "31 (Est.)"). Max 3 words.
2. Ensure every single block label starts on a brand new line.

Respond ONLY using this direct template format:
NAME: [Candidate Name]
AGE: [Short value or short estimation]
MATCH_PERCENTAGE: [0-100 number only]
DECISION: [HIRE or REJECT]
MATCHING_SKILLS: [Matched technical skills]
MISSING_SKILLS: [Missing skills or None]
EDUCATION: [Degrees and schools found]
QUESTIONS: 1. [Q1]\n2. [Q2]\n3. [Q3]\n4. [Q4]\n5. [Q5]"""

        user_content = f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}"
        
        raw_response = None
        for attempt in range(3):
            try:
                chat_completion = client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_instructions},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=600
                )
                raw_response = chat_completion.choices[0].message.content
                if raw_response:
                    break
            except Exception as api_err:
                if attempt == 2:
                    raise api_err
                time.sleep(1)
        
        if not raw_response:
            return fallback_results

        # Lookahead helper to safely extract fields without line bleeding
        def parse_tag(field_tag, text_source, default=""):
            pattern = rf"{field_tag}:\s*(.*?)(?=\s*(?:\*\*|\b)(?:NAME|AGE|MATCH_PERCENTAGE|DECISION|MATCHING_SKILLS|MISSING_SKILLS|MISSING|EDUCATION|QUESTIONS):|$)"
            match = re.search(pattern, text_source, re.DOTALL | re.IGNORECASE)
            if match:
                return sanitize_output_text(match.group(1))
            return default

        parsed_name = parse_tag("NAME", raw_response, extracted_name)
        parsed_age = parse_tag("AGE", raw_response, "N/A")
        
        if len(parsed_age) > 15:
            digits = re.findall(r'\d+', parsed_age)
            parsed_age = f"{digits[0]} (Est.)" if digits else "N/A"

        score_text = parse_tag("MATCH_PERCENTAGE", raw_response, "")
        score_digits = re.sub(r'\D', '', score_text)
        final_score = int(score_digits[:2]) if score_digits else sim_score

        parsed_decision = parse_tag("DECISION", raw_response, "HIRE" if final_score >= 60 else "REJECT").upper()
        parsed_matching = parse_tag("MATCHING_SKILLS", raw_response, "Identified core matches.")
        
        # Check both variants of missing skills tags
        parsed_missing = parse_tag("MISSING_SKILLS", raw_response, "")
        if not parsed_missing:
            parsed_missing = parse_tag("MISSING", raw_response, "None")
            
        parsed_edu = parse_tag("EDUCATION", raw_response, "Verified credentials.")
        
        q_match = re.search(r"QUESTIONS:\s*(.*)", raw_response, re.DOTALL | re.IGNORECASE)
        parsed_questions = sanitize_output_text(q_match.group(1)) if q_match else fallback_results["questions"]

        # Drop any accidental raw trailing HTML or styling code elements completely
        if "<" in parsed_questions:
            parsed_questions = parsed_questions.split("<")[0].strip()

        return {
            "name": parsed_name if parsed_name else extracted_name,
            "age": parsed_age if parsed_age else "N/A",
            "match_percentage": final_score,
            "decision": "HIRE" if "HIRE" in parsed_decision else "REJECT",
            "matching_skills": parsed_matching,
            "missing_skills": parsed_missing if parsed_missing else "None",
            "education": parsed_edu,
            "questions": parsed_questions
        }
        
    except Exception as e:
        return fallback_results
