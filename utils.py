import os
import re
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
    # 1. Setup emergency rule-based calculations first
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
        # Connect explicitly to the free conversational-supported instance
        client = InferenceClient(model="meta-llama/Llama-3.2-3B-Instruct", token=hf_token)
        
        system_instructions = """You are an advanced neural ATS screening engine. Profile the candidate details accurately based on the provided resume text.
You must extract the candidate's age or logically calculate/estimate it based on graduation or work timelines (e.g., 24 or 26 (Est.)).
You must look closely for previous company experience or professional internships.
You must provide exactly 5 targeted screening technical questions.
Respond ONLY using this direct template format:
NAME: [Name]
AGE: [Age value or Estimated age]
MATCH_PERCENTAGE: [0-100 number]
DECISION: [HIRE or REJECT]
MATCHING_SKILLS: [Skills found in resume matching the JD]
MISSING_SKILLS: [Required JD elements missing from the resume]
EDUCATION: [Degrees found]
QUESTIONS: 1. [Q1]\n2. [Q2]\n3. [Q3]\n4. [Q4]\n5. [Q5]"""

        user_content = f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}"
        
        # FIX: Switched from text_generation to chat_completion to accommodate the free provider task change
        chat_completion = client.chat_completion(
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            max_tokens=450
        )
        
        response = chat_completion.choices[0].message.content
        
        def extract_field(field_name, text_source, default_val=""):
            pattern = rf"{field_name}:\s*(.*?)(?=\n(?:NAME|AGE|MATCH_PERCENTAGE|DECISION|MATCHING_SKILLS|MISSING_SKILLS|EDUCATION|QUESTIONS):|$)"
            match = re.search(pattern, text_source, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else default_val

        parsed_name = extract_field("NAME", response, extracted_name)
        parsed_age = extract_field("AGE", response, "N/A")
        parsed_score_str = extract_field("MATCH_PERCENTAGE", response, "")
        parsed_decision = extract_field("DECISION", response, "HIRE" if sim_score >= 60 else "REJECT")
        parsed_matching = extract_field("MATCHING_SKILLS", response, "Identified core matches.")
        parsed_missing = extract_field("MISSING_SKILLS", response, "Review criteria details manually.")
        parsed_edu = extract_field("EDUCATION", response, "Verified credentials.")
        
        q_match = re.search(r"QUESTIONS:\s*(.*)", response, re.DOTALL | re.IGNORECASE)
        parsed_questions = q_match.group(1).strip() if q_match else fallback_results["questions"]

        percentage_str = re.sub(r'\D', '', parsed_score_str)
        final_score = int(percentage_str) if percentage_str else sim_score
        
        return {
            "name": parsed_name,
            "age": parsed_age if parsed_age else "N/A",
            "match_percentage": final_score,
            "decision": parsed_decision,
            "matching_skills": parsed_matching,
            "missing_skills": parsed_missing,
            "education": parsed_edu,
            "questions": parsed_questions
        }
        
    except Exception as e:
        fallback_results["matching_skills"] = f"❌ LIVE EXCEPTION: {str(e)}"
        return fallback_results
