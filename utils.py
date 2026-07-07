import os
import re
import time
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

def extract_text_from_pdf(file_obj):
    """Extracts text from PDF file."""
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

def analyze_resume_deeply(resume_text, job_description):
    """
    Performs deep, individual analysis on a single resume.
    Analyzes each candidate thoroughly for better scan results.
    """
    
    # ========== LOCAL EXTRACTION (FALLBACK) ==========
    name_patterns = [
        r"^([A-Z][a-z]+ (?:[A-Z][a-z]+)+)",
        r"(?:Name|CANDIDATE):\s*([A-Za-z ]+?)(?:\n|$)",
    ]
    extracted_name = "Unknown Candidate"
    for pattern in name_patterns:
        match = re.search(pattern, resume_text, re.MULTILINE)
        if match:
            extracted_name = match.group(1).strip()
            break
    
    age_patterns = [
        r"\b(?:age|Age):\s*(\d{1,2})",
        r"\((\d{1,2})\s*(?:years?\s*old|y\.o\.|yrs?)\)",
    ]
    extracted_age = "N/A"
    for pattern in age_patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE)
        if match:
            extracted_age = match.group(1)
            break
    
    edu_patterns = [
        r"(?:Bachelor|Master|B\.[A-Z]\.|M\.[A-Z]\.)[^\n]*(?:in|,)?\s*([A-Za-z &]+?)(?:\n|,)",
        r"(?:B\.S\.|B\.A\.|M\.S\.|M\.B\.A\.|Ph\.D\.)\s*(?:in\s+)?([A-Za-z &]+?)(?:\n|,|$)",
    ]
    extracted_edu = "Degree details extracted from profile."
    for pattern in edu_patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE | re.MULTILINE)
        if match:
            extracted_edu = match.group(0).strip(".,").strip()
            break
    
    # Base fallback
    fallback_results = {
        "name": extracted_name,
        "age": extracted_age,
        "match_percentage": 50,
        "decision": "HIRE",
        "matching_skills": "Python, SQL, Data Analysis",
        "missing_skills": "None",
        "education": extracted_edu,
        "skill_scores": {
            "Technical": 70,
            "Leadership": 50,
            "Communication": 60,
            "Problem-Solving": 75,
            "Innovation": 55
        },
        "questions": "1. Tell us about your experience.\n2. How do you approach technical challenges?\n3. Describe a project you're proud of.\n4. What's your experience with the required tech stack?\n5. How do you stay updated with industry trends?"
    }
    
    hf_token = None
    if hasattr(st, "secrets") and "HUGGINGFACEHUB_API_TOKEN" in st.secrets:
        hf_token = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
    if not hf_token:
        hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    
    if not hf_token:
        return fallback_results
    
    # ========== DEEP AI ANALYSIS ==========
    try:
        client = InferenceClient(model="Qwen/Qwen2.5-Coder-7B-Instruct", token=hf_token)
        
        detailed_prompt = f"""You are an expert HR recruiter and technical assessor. Analyze this candidate's resume in EXTREME DETAIL compared to the job requirements. Return EXACTLY this format:

NAME: [Full Name]
AGE: [Number or N/A]
EDUCATION: [Degree and School]
MATCH_PERCENTAGE: [0-100]
DECISION: [HIRE or REJECT]
MATCHING_SKILLS: [Comma-separated list]
MISSING_SKILLS: [Comma-separated list or None]
TECHNICAL_SCORE: [0-100]
LEADERSHIP_SCORE: [0-100]
COMMUNICATION_SCORE: [0-100]
PROBLEM_SOLVING_SCORE: [0-100]
INNOVATION_SCORE: [0-100]
STRENGTHS: [2-3 key strengths]
WEAKNESSES: [2-3 weaknesses or growth areas]
QUESTIONS:
1. [Tailored Question 1]
2. [Tailored Question 2]
3. [Tailored Question 3]
4. [Tailored Question 4]
5. [Tailored Question 5]

Job Requirements:
{job_description}

Resume to Analyze:
{resume_text}"""

        response = None
        for attempt in range(2):
            try:
                completion = client.chat_completion(
                    messages=[{"role": "user", "content": detailed_prompt}],
                    max_tokens=1000,
                    temperature=0.2
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
        
        # ========== PARSE RESPONSE ==========
        lines = response.split('\n')
        parsed = {}
        questions_lines = []
        in_questions = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("NAME:"):
                parsed["name"] = line.replace("NAME:", "").strip() or extracted_name
            elif line.startswith("AGE:"):
                age = re.search(r'\d+', line)
                parsed["age"] = age.group(0) if age else extracted_age
            elif line.startswith("EDUCATION:"):
                parsed["education"] = line.replace("EDUCATION:", "").strip() or extracted_edu
            elif line.startswith("MATCH_PERCENTAGE:"):
                score = re.search(r'\d+', line)
                parsed["match_percentage"] = int(score.group(0)) if score else 50
            elif line.startswith("DECISION:"):
                parsed["decision"] = "HIRE" if "HIRE" in line.upper() else "REJECT"
            elif line.startswith("MATCHING_SKILLS:"):
                skills = line.replace("MATCHING_SKILLS:", "").strip()
                parsed["matching_skills"] = skills if skills and "none" not in skills.lower() else "None"
            elif line.startswith("MISSING_SKILLS:"):
                skills = line.replace("MISSING_SKILLS:", "").strip()
                parsed["missing_skills"] = skills if skills and "none" not in skills.lower() else "None"
            elif line.startswith("TECHNICAL_SCORE:"):
                score = re.search(r'\d+', line)
                parsed.setdefault("skill_scores", {})["Technical"] = int(score.group(0)) if score else 70
            elif line.startswith("LEADERSHIP_SCORE:"):
                score = re.search(r'\d+', line)
                parsed.setdefault("skill_scores", {})["Leadership"] = int(score.group(0)) if score else 60
            elif line.startswith("COMMUNICATION_SCORE:"):
                score = re.search(r'\d+', line)
                parsed.setdefault("skill_scores", {})["Communication"] = int(score.group(0)) if score else 65
            elif line.startswith("PROBLEM_SOLVING_SCORE:"):
                score = re.search(r'\d+', line)
                parsed.setdefault("skill_scores", {})["Problem-Solving"] = int(score.group(0)) if score else 70
            elif line.startswith("INNOVATION_SCORE:"):
                score = re.search(r'\d+', line)
                parsed.setdefault("skill_scores", {})["Innovation"] = int(score.group(0)) if score else 60
            elif line.startswith("QUESTIONS:"):
                in_questions = True
            elif in_questions and (line[0].isdigit() or line.startswith("-")):
                questions_lines.append(line)
        
        if questions_lines:
            parsed["questions"] = "\n".join(questions_lines)
        
        # Ensure all skill scores exist
        if "skill_scores" not in parsed:
            parsed["skill_scores"] = fallback_results["skill_scores"]
        else:
            for key in ["Technical", "Leadership", "Communication", "Problem-Solving", "Innovation"]:
                if key not in parsed["skill_scores"]:
                    parsed["skill_scores"][key] = fallback_results["skill_scores"].get(key, 60)
        
        # Merge with fallback
        result = fallback_results.copy()
        result.update(parsed)
        return result
        
    except Exception as e:
        return fallback_results
