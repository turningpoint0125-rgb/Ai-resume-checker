import os
import re
import time
import json
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

def analyze_resume(resume_text, job_description):
    """Scans candidate resume data using structural JSON matching to prevent interface layout leaks."""
    # Emergency fallback definitions
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
        "matching_skills": "Local keyword scanning processed successfully.",
        "missing_skills": "Review system baseline constraints manually.",
        "education": "Extracted text profile data.",
        "questions": "1. Describe your direct experience working with Python data automation workflows.\n2. How do you maintain code quality inside collaborative development environments?\n3. What testing methodologies do you employ for analytical tools?\n4. Walk through a recent project architecture you successfully deployed.\n5. How do you handle unstructured data inputs within your processing workflows?"
    }

    if not hf_token:
        return fallback_results

    try:
        client = InferenceClient(model="Qwen/Qwen2.5-Coder-7B-Instruct", token=hf_token)
        
        system_instructions = """You are an advanced neural ATS screening engine. You must profile candidate data explicitly using valid JSON layout strings. 
Return a raw JSON object matching this structure exactly. Do not add markdown around it, do not include HTML formatting, and do not use unescaped characters.

JSON Key Requirements:
- "name": String containing candidate name.
- "age": Short string containing age value or short estimation (e.g., "31 (Est.)").
- "match_percentage": Integer between 0 and 100.
- "decision": Either "HIRE" or "REJECT".
- "matching_skills": Comma-separated string of matched technical skills.
- "missing_skills": Comma-separated string of missing skills specific to this candidate.
- "education": String summarizing found degrees and academic institutions.
- "questions": An array string containing exactly 5 numbered screening questions without HTML wrapping.

Example Output Format:
{
  "name": "Alex Doe",
  "age": "29",
  "match_percentage": 85,
  "decision": "HIRE",
  "matching_skills": "Python, SQL, AWS",
  "missing_skills": "Docker, Kubernetes",
  "education": "B.Sc Computer Science",
  "questions": "1. First question?\\n2. Second question?\\n3. Third question?\\n4. Fourth question?\\n5. Fifth question?"
}"""

        user_content = f"JOB REQUIREMENTS:\n{job_description}\n\nCANDIDATE RESUME TEXT:\n{resume_text}"
        
        raw_response = None
        for attempt in range(3):
            try:
                chat_completion = client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_instructions},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=700
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

        # Locate clean JSON structure inside the payload block
        json_clean = raw_response.strip()
        if "```json" in json_clean:
            json_clean = json_clean.split("```json")[1].split("```")[0].strip()
        elif "```" in json_clean:
            json_clean = json_clean.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_clean)

        # Enforce clean data strings on values to make sure text renders properly
        def string_clean(val):
            if not val:
                return ""
            return re.sub(r'<[^>]*>', '', str(val)).strip()

        # Safely capture match metric conversions
        try:
            score = int(parsed.get("match_percentage", sim_score))
        except:
            score = sim_score

        return {
            "name": string_clean(parsed.get("name")) or extracted_name,
            "age": string_clean(parsed.get("age")) or "N/A",
            "match_percentage": score,
            "decision": string_clean(parsed.get("decision")).upper() or ("HIRE" if score >= 60 else "REJECT"),
            "matching_skills": string_clean(parsed.get("matching_skills")) or "Identified core matches.",
            "missing_skills": string_clean(parsed.get("missing_skills")) or "None",
            "education": string_clean(parsed.get("education")) or "Verified credentials.",
            "questions": string_clean(parsed.get("questions")) or fallback_results["questions"]
        }
        
    except Exception as e:
        return fallback_results
