import os
import re
import time
import streamlit as st
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient

def extract_text_from_pdf(file_obj):
    """Extract text from PDF."""
    try:
        pdf_reader = PdfReader(file_obj)
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except:
        return ""

def analyze_resume(resume_text, job_description):
    """Analyze resume and return complete structured data."""
    
    # Default complete result
    default_result = {
        "name": "Unknown Candidate",
        "age": "N/A",
        "education": "Education not specified",
        "years_exp": "Not specified",
        "match_score": 50,
        "matching_skills": ["Data Analysis"],
        "missing_skills": ["Docker"],
        "hr_recommendation": "INTERVIEW",
        "justification": "Candidate requires further evaluation.",
        "technical_questions": [
            "Tell us about your technical background.",
            "Describe your experience with the key technologies.",
            "What project are you most proud of?",
            "How do you approach problem-solving?",
            "What's your experience with the required tools?"
        ],
        "hr_questions": [
            "Tell us about yourself.",
            "Why are you interested in this role?",
            "What are your career goals?",
            "How do you work in a team?",
            "What's your greatest achievement?"
        ],
        "skill_scores": {"Technical": 60, "Leadership": 55, "Communication": 65, "Problem-Solving": 70, "Innovation": 50}
    }
    
    # Try to extract basic info locally first
    name = "Unknown Candidate"
    name_match = re.search(r'^([A-Z][a-z]+ [A-Z][a-z]+)', resume_text, re.MULTILINE)
    if name_match:
        name = name_match.group(1)
    
    default_result["name"] = name
    
    # Get token
    hf_token = None
    try:
        if hasattr(st, "secrets"):
            hf_token = st.secrets.get("HUGGINGFACEHUB_API_TOKEN")
    except:
        pass
    if not hf_token:
        hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    
    if not hf_token:
        return default_result
    
    try:
        client = InferenceClient(model="Qwen/Qwen2.5-Coder-7B-Instruct", token=hf_token)
        
        prompt = f"""You are an expert recruiter. Analyze this resume against the job description and extract the EXACT data in this format:

CANDIDATE_NAME: [Full name]
AGE: [Age number or N/A]
EDUCATION: [Degree and school or N/A]
YEARS_EXPERIENCE: [Number of years or Not specified]
MATCH_SCORE: [0-100 number only]
MATCHING_SKILLS: [Skill1, Skill2, Skill3] (comma separated)
MISSING_SKILLS: [Skill1, Skill2, Skill3] (comma separated)
HR_RECOMMENDATION: [HIRE or REJECT or INTERVIEW]
JUSTIFICATION: [One sentence reason]
TECHNICAL_Q1: [Question 1]
TECHNICAL_Q2: [Question 2]
TECHNICAL_Q3: [Question 3]
TECHNICAL_Q4: [Question 4]
TECHNICAL_Q5: [Question 5]
HR_Q1: [Question 1]
HR_Q2: [Question 2]
HR_Q3: [Question 3]
HR_Q4: [Question 4]
HR_Q5: [Question 5]
TECHNICAL_SCORE: [0-100]
LEADERSHIP_SCORE: [0-100]
COMMUNICATION_SCORE: [0-100]
PROBLEM_SOLVING_SCORE: [0-100]
INNOVATION_SCORE: [0-100]

Job Description:
{job_description}

Resume:
{resume_text}"""

        response = None
        for attempt in range(2):
            try:
                completion = client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                    temperature=0.1
                )
                response = completion.choices[0].message.content
                if response:
                    break
            except:
                if attempt == 1:
                    return default_result
                time.sleep(1)
        
        if not response:
            return default_result
        
        # Parse response line by line
        result = default_result.copy()
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().upper()
            value = value.strip()
            
            if key == "CANDIDATE_NAME":
                result["name"] = value or result["name"]
            elif key == "AGE":
                result["age"] = value or "N/A"
            elif key == "EDUCATION":
                result["education"] = value or "Education not specified"
            elif key == "YEARS_EXPERIENCE":
                result["years_exp"] = value or "Not specified"
            elif key == "MATCH_SCORE":
                try:
                    score = int(re.search(r'\d+', value).group(0))
                    result["match_score"] = min(max(score, 0), 100)
                except:
                    pass
            elif key == "MATCHING_SKILLS":
                result["matching_skills"] = [s.strip() for s in value.split(',') if s.strip()]
            elif key == "MISSING_SKILLS":
                result["missing_skills"] = [s.strip() for s in value.split(',') if s.strip()]
            elif key == "HR_RECOMMENDATION":
                if "HIRE" in value.upper():
                    result["hr_recommendation"] = "HIRE"
                elif "REJECT" in value.upper():
                    result["hr_recommendation"] = "REJECT"
                else:
                    result["hr_recommendation"] = "INTERVIEW"
            elif key == "JUSTIFICATION":
                result["justification"] = value or "No justification provided."
            elif key.startswith("TECHNICAL_Q"):
                idx = int(key.replace("TECHNICAL_Q", "")) - 1
                if idx < len(result["technical_questions"]):
                    result["technical_questions"][idx] = value
            elif key.startswith("HR_Q"):
                idx = int(key.replace("HR_Q", "")) - 1
                if idx < len(result["hr_questions"]):
                    result["hr_questions"][idx] = value
            elif key == "TECHNICAL_SCORE":
                try:
                    result["skill_scores"]["Technical"] = min(max(int(re.search(r'\d+', value).group(0)), 0), 100)
                except:
                    pass
            elif key == "LEADERSHIP_SCORE":
                try:
                    result["skill_scores"]["Leadership"] = min(max(int(re.search(r'\d+', value).group(0)), 0), 100)
                except:
                    pass
            elif key == "COMMUNICATION_SCORE":
                try:
                    result["skill_scores"]["Communication"] = min(max(int(re.search(r'\d+', value).group(0)), 0), 100)
                except:
                    pass
            elif key == "PROBLEM_SOLVING_SCORE":
                try:
                    result["skill_scores"]["Problem-Solving"] = min(max(int(re.search(r'\d+', value).group(0)), 0), 100)
                except:
                    pass
            elif key == "INNOVATION_SCORE":
                try:
                    result["skill_scores"]["Innovation"] = min(max(int(re.search(r'\d+', value).group(0)), 0), 100)
                except:
                    pass
        
        return result
        
    except Exception as e:
        return default_result
