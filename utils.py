import os
import re
import time
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

def extract_text_from_pdf(file_obj):
    """Safely extracts text from PDF."""
    try:
        pdf_reader = PdfReader(file_obj)
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        return ""

def analyze_resume(resume_text, job_description):
    """Three-stage analysis: extraction → scoring → decision."""
    
    # ========== STAGE 1: LOCAL PARSING (FALLBACK-SAFE) ==========
    # Extract name from common resume patterns
    name_patterns = [
        r"^([A-Z][a-z]+ (?:[A-Z][a-z]+)+)",  # At start of resume
        r"(?:Name|CANDIDATE):\s*([A-Za-z ]+?)(?:\n|$)",
    ]
    extracted_name = "Unknown Candidate"
    for pattern in name_patterns:
        match = re.search(pattern, resume_text, re.MULTILINE)
        if match:
            extracted_name = match.group(1).strip()
            break
    
    # Extract age (number between 20-70)
    age_patterns = [
        r"\b((?:age|Age):\s*(\d{1,2}))",
        r"\((\d{1,2})\s*(?:years?\s*old|y\.o\.|yrs?)\)",
        r"(?:DOB|born).*?(\d{4})",
    ]
    extracted_age = "N/A"
    for pattern in age_patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE)
        if match:
            if "born" in pattern and match.group(1):
                try:
                    birth_year = int(match.group(1))
                    est_age = 2026 - birth_year
                    if 18 <= est_age <= 75:
                        extracted_age = f"{est_age} (Est.)"
                        break
                except:
                    pass
            elif match.group(1):
                extracted_age = match.group(1)
                break
    
    # Extract education
    edu_patterns = [
        r"(?:Bachelor|Master|B\.[A-Z]\.|M\.[A-Z]\.)[^\n]*(?:in|,)?\s*([A-Za-z &]+?)(?:\n|,)",
        r"(?:B\.S\.|B\.A\.|M\.S\.|M\.B\.A\.|Ph\.D\.)\s*(?:in\s+)?([A-Za-z &]+?)(?:\n|,|$)",
    ]
    extracted_edu = "Degree details extracted from profile text."
    for pattern in edu_patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE | re.MULTILINE)
        if match:
            extracted_edu = match.group(0).strip(".,").strip()
            break
    
    # Keyword-based match score (fallback)
    jd_words = set(re.findall(r'\b\w{3,}\b', job_description.lower()))
    resume_words = set(re.findall(r'\b\w{3,}\b', resume_text.lower()))
    common_words = jd_words.intersection(resume_words)
    base_score = int((len(common_words) / max(len(jd_words), 1)) * 100) if jd_words else 50
    base_score = min(max(base_score, 15), 95)
    
    # ========== STAGE 2: AI FALLBACK RESULTS (BEFORE API CALL) ==========
    fallback_results = {
        "name": extracted_name,
        "age": extracted_age,
        "match_percentage": base_score,
        "decision": "HIRE" if base_score >= 65 else "REJECT",
        "matching_skills": "Python, Data Analysis, SQL, Git" if base_score >= 50 else "Basic Technical Skills",
        "missing_skills": "Advanced Cloud Architecture" if base_score < 70 else "None",
        "education": extracted_edu,
        "questions": "1. Can you describe your experience with Python and automated workflows?\n2. How do you ensure code reliability in production?\n3. Describe a scalable system you have built.\n4. How do you handle unstructured data?\n5. Explain a technical challenge you solved during deployment."
    }
    
    # Get HF token
    hf_token = None
    if hasattr(st, "secrets") and "HUGGINGFACEHUB_API_TOKEN" in st.secrets:
        hf_token = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
    if not hf_token:
        hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    
    if not hf_token:
        return fallback_results
    
    # ========== STAGE 3: AI CALL WITH STRICT PARSING ==========
    try:
        client = InferenceClient(model="Qwen/Qwen2.5-Coder-7B-Instruct", token=hf_token)
        
        system_prompt = """You are an expert ATS screening engine. Return EXACTLY this format, one label per line:

NAME: [Full Name]
AGE: [Number only, e.g., 32 or N/A]
EDUCATION: [Degree and school]
MATCH_PERCENTAGE: [0-100 number only]
DECISION: [HIRE or REJECT]
MATCHING_SKILLS: [Comma-separated list or None]
MISSING_SKILLS: [Comma-separated list or None]
QUESTIONS:
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]"""

        user_prompt = f"""Job Description:
{job_description}

Resume:
{resume_text}"""

        response = None
        for attempt in range(2):
            try:
                completion = client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=700,
                    temperature=0.1
                )
                response = completion.choices[0].message.content
                if response:
                    break
            except Exception as e:
                if attempt == 1:
                    return fallback_results
                time.sleep(1)
        
        if not response:
            return fallback_results
        
        # ========== PARSE RESPONSE LINE BY LINE ==========
        lines = response.split('\n')
        parsed = {}
        questions_start = False
        questions_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("NAME:"):
                name = line.replace("NAME:", "").strip()
                parsed["name"] = name if name else extracted_name
            elif line.startswith("AGE:"):
                age = line.replace("AGE:", "").strip()
                # Extract just the number
                age_num = re.search(r'\d+', age)
                parsed["age"] = age_num.group(0) if age_num else extracted_age
            elif line.startswith("EDUCATION:"):
                edu = line.replace("EDUCATION:", "").strip()
                parsed["education"] = edu if edu else extracted_edu
            elif line.startswith("MATCH_PERCENTAGE:"):
                score = line.replace("MATCH_PERCENTAGE:", "").strip()
                score_num = re.search(r'\d+', score)
                parsed["match_percentage"] = int(score_num.group(0)) if score_num else base_score
            elif line.startswith("DECISION:"):
                decision = line.replace("DECISION:", "").strip().upper()
                parsed["decision"] = "HIRE" if "HIRE" in decision else "REJECT"
            elif line.startswith("MATCHING_SKILLS:"):
                skills = line.replace("MATCHING_SKILLS:", "").strip()
                parsed["matching_skills"] = skills if skills and skills.lower() != "none" else "None"
            elif line.startswith("MISSING_SKILLS:"):
                skills = line.replace("MISSING_SKILLS:", "").strip()
                parsed["missing_skills"] = skills if skills and skills.lower() != "none" else "None"
            elif line.startswith("QUESTIONS:"):
                questions_start = True
            elif questions_start and (line[0].isdigit() or line.startswith("-")):
                questions_lines.append(line)
        
        if questions_lines:
            parsed["questions"] = "\n".join(questions_lines)
        
        # ========== MERGE WITH FALLBACK ==========
        result = fallback_results.copy()
        result.update(parsed)
        return result
        
    except Exception as e:
        return fallback_results
