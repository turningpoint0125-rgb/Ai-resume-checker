import os
import re
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
    """
    Sends data to Hugging Face Inference API with a safety fallback 
    if a requests.exceptions.ConnectionError or timeout occurs.
    """
    # Default fallback data structure if connection drops
    fallback_results = {
        "name": "Unknown Candidate",
        "match_percentage": 10,
        "decision": "REJECT",
        "matching_skills": "Connection timeout.",
        "missing_skills": "Unable to reach evaluation engine.",
        "education": "N/A",
        "questions": "Engine offline. Please re-execute scan."
    }
    
    # Try to grab candidate name safely from the top of the text
    name_match = re.search(r"CANDIDATE PROFILE:\s*([^\n]+)", resume_text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"Name:\s*([^\n]+)", resume_text, re.IGNORECASE)
    
    extracted_name = name_match.group(1).strip() if name_match else "Candidate Engine Profile"
    fallback_results["name"] = extracted_name

    # Retrieve your API token from Streamlit Secrets
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    
    # Simple rule-based calculation to guess matching terms if the API is offline
    jd_words = set(re.findall(r'\w+', job_description.lower()))
    resume_words = set(re.findall(r'\w+', resume_text.lower()))
    common_words = jd_words.intersection(resume_words)
    
    # Primitive calculation string matching for emergency fallback score
    sim_score = int((len(common_words) / max(len(jd_words), 1)) * 100)
    sim_score = min(max(sim_score, 15), 95) # cap it realistically

    try:
        # Use a reliable public endpoint (Qwen or Llama model)
        client = InferenceClient("Qwen/Qwen2.5-72B-Instruct", token=hf_token)
        
        prompt = f"""
        You are an advanced neural ATS screening engine parsing raw applicant text streams.
        Compare the candidate's resume text to the target job description criteria.

        TARGET JOB DESCRIPTION:
        {job_description}

        APPLICANT RESUME TEXT STREAM:
        {resume_text}

        Respond STRICTLY in the following text format template without markdown headers:
        NAME: [Full Name]
        MATCH_PERCENTAGE: [0 to 100 integer score only]
        DECISION: [HIRE or REJECT]
        MATCHING_SKILLS: [Comma separated list of keywords found]
        MISSING_SKILLS: [Key requirements missing]
        EDUCATION: [Degrees found]
        QUESTIONS: [1 or 2 core diagnostic screening questions]
        """
        
        response = client.text_generation(prompt, max_new_tokens=500, timeout=12)
        
        # Parse output dictionary arrays safely
        parsed = {}
        for line in response.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                parsed[key.strip().upper()] = val.strip()
                
        return {
            "name": parsed.get("NAME", extracted_name),
            "match_percentage": int(re.sub(r'\D', '', parsed.get("MATCH_PERCENTAGE", str(sim_score)))),
            "decision": parsed.get("DECISION", "HIRE" if sim_score > 60 else "REJECT"),
            "matching_skills": parsed.get("MATCHING_SKILLS", "Keyword parsed logs complete."),
            "missing_skills": parsed.get("MISSING_SKILLS", "Review manual logs."),
            "education": parsed.get("EDUCATION", "Extracted text data streams."),
            "questions": parsed.get("QUESTIONS", "Describe an enterprise deployment you maintained using Python.")
        }
        
    except Exception as e:
        # If API drops connection (the error from your screenshot), activate engine fallback safely
        fallback_results["match_percentage"] = sim_score
        fallback_results["decision"] = "HIRE" if sim_score >= 60 else "REJECT"
        return fallback_results
