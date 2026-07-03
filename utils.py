import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from langchain_community.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

llm = HuggingFaceHub(
    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
    model_kwargs={"temperature": 0.2, "max_new_tokens": 1000}
)

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def analyze_resume(resume_text, job_description):
    profile_template = """
    Extract the candidate's full name and their highest educational degree from the following resume text.
    If you cannot find the name, use 'Unknown Candidate'.
    Format your response exactly like this:
    Name: [Name here]
    Education: [Education here]
    
    Resume: {resume}
    """
    profile_prompt = PromptTemplate(template=profile_template, input_variables=["resume"])
    profile_chain = LLMChain(llm=llm, prompt=profile_prompt)
    profile_output = profile_chain.run(resume=resume_text)
    
    name = "Unknown"
    education = "Not Specified"
    name_match = re.search(r"Name:\s*(.*)", profile_output)
    edu_match = re.search(r"Education:\s*(.*)", profile_output)
    if name_match: name = name_match.group(1).strip()
    if edu_match: education = edu_match.group(1).strip()

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
    analysis_chain = LLMChain(llm=llm, prompt=analysis_prompt)
    analysis_output = analysis_chain.run(jd=job_description, resume=resume_text)

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
    decision_chain = LLMChain(llm=llm, prompt=decision_prompt)
    decision_output = decision_chain.run(match_pct=match_pct, jd=job_description)

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
