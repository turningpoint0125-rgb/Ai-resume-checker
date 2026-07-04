import os
import re
import pandas as pd
import streamlit as st  
from PyPDF2 import PdfReader
from langchain_community.llms import HuggingFaceHub
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Fetch token safely from Streamlit secrets or local env variables
hf_token = st.secrets.get("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")

# 2. Clean global initialization of the model endpoint with proper pairing syntax
llm = HuggingFaceHub(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
    task="text-generation",
    huggingfacehub_api_token=hf_token,
    model_kwargs={
        "temperature": 0.2, 
        "max_new_tokens": 1000
    }
)

def extract_text_from_pdf(pdf_file):
    """Safely extracts clean string text from an uploaded PDF binary stream."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF data: {e}")
        return ""

def analyze_resume(resume_text, job_description):
    """Main process utilizing standard modern LCEL pipeline architecture."""
    # Ensure token exists before kicking off execution pipelines
    if not hf_token:
        st.error("🔑 Missing Hugging Face Token! Add it to the Secrets Panel on Streamlit Dashboard.")
        st.stop()

    output_parser = StrOutputParser()
    
    # --- Chain 1: Candidate Basic Information Extraction ---
    profile_template = """
    Extract the candidate's full name and their highest educational degree from the following resume text.
    If you cannot find the name, use 'Unknown Candidate'.
    Format your response exactly like this:
    Name: [Name here]
    Education: [Education here]
    
    Resume: {resume}
    """
    profile_prompt = PromptTemplate(template=profile_template, input_variables=["resume"])
    profile_chain = profile_prompt | llm | output_parser
    profile_output = profile_chain.invoke({"resume": resume_text})
    
    name = "Unknown"
    education = "Not Specified"
    name_match = re.search(r"Name:\s*(.*)", profile_output)
    edu_match = re.search(r"Education:\s*(.*)", profile_output)
    if name_match: name = name_match.group(1).strip()
    if edu_match: education = edu_match.group(1).strip()

    # --- Chain 2: Structural ATS Keyword Analysis ---
    analysis_template = """
    You are an expert ATS (Applicant Tracking System). Compare the Resume against the Job Description (JD).
    1. Provide a Match Percentage (0% to 100%) based on skills, experience, and role alignment.
    2. List the key skills the candidate possesses that match the JD.
    3. List critical skills missing from the resume.

    Job Description: {jd}
    Resume: {resume}

    Respond strictly in this format:
    MATCH_PERCENTAGE: [Only the number, e.g., 85]
    MATCHING_SKILLS: [Comma separated list]
    MISSING_SKILLS: [Comma separated list]
    """
    analysis_prompt = PromptTemplate(template=analysis_template, input_variables=["jd", "resume"])
    analysis_chain = analysis_prompt | llm | output_parser
    analysis_output = analysis_chain.invoke({"jd": job_description, "resume": resume_text})

    match_pct = 50 
    pct_match = re.search(r"MATCH_PERCENTAGE:\s*(\d+)", analysis_output)
    if pct_match:
        match_pct = int(pct_match.group(1))

    matching_skills = ""
    missing_skills = ""
    match_s_match = re.search(r"MATCHING_SKILLS:\s*(.*)", analysis_output)
    miss_s_match = re.search(r"MISSING_SKILLS:\s*(.*)", analysis_output)
    if match_s_match: matching_skills = match_s_match.group(1).strip()
    if miss_s_match: missing_skills = miss_s_match.group(1).strip()

    # --- Chain 3: Automated Decision & Custom Question Generation ---
    decision_template = """
    Based on a {match_pct}% compatibility match for this Job Description, make a hiring decision.
    If the match is 70% or higher, output 'HIRE'. Otherwise, output 'REJECT'.
    Also, generate 5 tailored technical interview questions based on the missing or listed skills to evaluate the candidate.

    Job Description: {jd}
    
    Respond strictly in this format:
    DECISION: [HIRE or REJECT]
    QUESTIONS:
    1. [Question 1]
    2. [Question 2]
    3. [Question 3]
    4. [Question 4]
    5. [Question 5]
    """
    decision_prompt = PromptTemplate(template=decision_template, input_variables=["match_pct", "jd"])
    decision_chain = decision_prompt | llm | output_parser
    decision_output = decision_chain.invoke({"match_pct": match_pct, "jd": job_description})

    decision = "REJECT"
    if "HIRE" in decision_output.split("QUESTIONS:")[0]:
        decision = "HIRE"

    questions = decision_output.split("QUESTIONS:")[-1].strip() if "QUESTIONS:" in decision_output else "No questions generated."

    return {
        "name": name,
        "education": education,
        "match_percentage": match_pct,
        "decision": decision,
        "questions": questions,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills
    }
