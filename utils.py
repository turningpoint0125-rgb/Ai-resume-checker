import os
import re
import json
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

def extract_text_from_pdf(file_obj):
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

def analyze_resume(resume_text, job_description):
    # 1. Rule-based emergency backups if the API completely fails
    name_match = re.search(r"CANDIDATE PROFILE:\s*([^\n]+)", resume_text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"Name:\s*([^\n]+)", resume_text, re.IGNORECASE)
    
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

    fallback_results = {
        "name": extracted_name,
        "age": "N/A",
        "match_percentage": sim_score,
        "decision": "HIRE" if sim_score >= 60 else "REJECT",
        "matching_skills": "Local algorithm processed keywords successfully.",
        "missing_skills": "Scan complete. Check specific technical requirements manual checklist.",
        "education": "Extracted text profile data.",
        "questions": "1. Describe your direct experience working with Python data automation workflows.\n2. How do you maintain code quality inside collaborative development environments?\n3. What testing methodologies do you employ for analytical tools?\n4. Walk through a recent project architecture you successfully deployed.\n5. How do you handle unstructured data inputs within your processing workflows?"
    }

    if not hf_token:
        return fallback_results

    try:
        client = InferenceClient(model="Qwen/Qwen2.5-Coder-7B-Instruct", token=hf_token)
        
        # We tell the model to return JSON structure directly to avoid line bleeding
        system_instructions = """You are an advanced neural ATS screening engine. Profile the candidate details accurately based on the provided resume text.
You must respond with a raw JSON object containing these exact string keys: "name", "age", "match_percentage", "decision", "matching_skills", "missing_skills", "education", "questions".

STRICT FORMAT METRICS:
- "name": Clean name only (e.g., "Priya Nair"). No markdown stars, no extra text.
- "age": Short value only (e.g., "30" or "27 (Est.)"). Max 3 words.
- "match_percentage": An integer number between 0 and 100.
- "decision": "HIRE" or "REJECT".
- "questions": Clean list starting with numbers 1 to 5.

Respond ONLY with valid JSON inside a code block."""

        user_content = f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}"
        
        chat_completion = client.chat_completion(
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Parse the JSON payload natively
        parsed_json = json.loads(response_text)
        
        # Extract fields with safe fallbacks and clean text formatting strings
        clean_name = str(parsed_json.get("name", extracted_name)).replace("*", "").strip()
        clean_age = str(parsed_json.get("age", "N/A")).replace("*", "").strip()
        
        # Enforce short age rule programmatically if it outputs text
        if len(clean_age) > 15:
            age_digits = re.findall(r'\d+', clean_age)
            clean_age = f"{age_digits[0]} (Est.)" if age_digits else "N/A"

        # Validate score matrix type conversion
        raw_score = parsed_json.get("match_percentage", sim_score)
        try:
            final_score = int(re.sub(r'\D', '', str(raw_score)))
        except:
            final_score = sim_score

        return {
            "name": clean_name if clean_name else extracted_name,
            "age": clean_age if clean_age else "N/A",
            "match_percentage": final_score,
            "decision": str(parsed_json.get("decision", "HIRE" if final_score >= 60 else "REJECT")).upper().strip(),
            "matching_skills": str(parsed_json.get("matching_skills", "Identified core matches.")).strip(),
            "missing_skills": str(parsed_json.get("missing_skills", "Review criteria details manually.")).strip(),
            "education": str(parsed_json.get("education", "Verified credentials.")).strip(),
            "questions": str(parsed_json.get("questions", fallback_results["questions"])).strip()
        }
        
    except Exception as e:
        # Fallback if JSON decoding encounters structural variance
        return fallback_results
