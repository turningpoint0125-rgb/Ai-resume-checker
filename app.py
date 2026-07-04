import streamlit as st
import pandas as pd
import io
import plotly.express as px
from utils import extract_text_from_pdf, analyze_resume

# 1. Page Configuration for Wide High-Tech Telemetry Layout
st.set_page_config(
    page_title="ADVANCED NEURAL ATS // PRODUCTION ENGINE", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CYBERPUNK NEON GLOW CUSTOM CSS INJECTION ---
# This style matches the aesthetic of image_1.png and image_2.png
st.markdown("""
<style>
    /* Global Background and Text Style Overrides */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Neon Glowing Headers (Matches reference screenshot) */
    .cyber-title {
        color: #00ffcc;
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.6);
        font-size: 2.5rem;
        margin-bottom: 5px;
    }
    .cyber-subtitle {
        color: #8b949e;
        font-size: 1rem;
        margin-bottom: 25px;
    }
    
    /* High-Tech Container Styling for layout blocks */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
    }
    
    /* Input Highlights (Focus Glow) */
    textarea, input {
        background-color: #0d1117 !important;
        border: 1px solid #00ffcc !important;
        color: #00ffcc !important;
    }
    
    /* Neon Pink / Purple Action Button Styles (Matches 'EXECUTE MULTI-AGENT SCAN') */
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
        transform: scale(1.01);
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (SECURITY & CONTROL) ---
with st.sidebar:
    st.markdown("<h3 style='color: #ff007f;'>SIDEBAR CONTROL</h3>", unsafe_allow_html=True)
    # Match Threshold Slider
    match_threshold = st.slider("MATCH THRESHOLD CONTROL", min_value=0, max_value=100, value=60, step=5)
    st.markdown("---")
    # Connection Status indicator (as seen in image_1.png)
    st.markdown("<span style='color: #00ffcc;'>● STATUS: CLUSTER CONNECTED</span>", unsafe_allow_html=True)

# --- MAIN ENGINE HEADER ---
# This matches the neon glow and title verbatim from screenshot_2026-07-04-11-12-41-83.jpg
st.markdown("<h1 class='cyber-title'>🤖 ADVANCED NEURAL ATS // PRODUCTION ENGINE</h1>", unsafe_allow_html=True)
st.markdown("<p class='cyber-subtitle'>Next-generation multi-agent pipeline using Streamlit Cloud secured token keys.</p>", unsafe_allow_html=True)

# --- Main Grid Setup split between Input Directives & Metrics Dashboard ---
# Matches the side-by-side telemetry structure from the reference dashboard mockup
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("<h3 style='color: #00ffcc;'>📋 CONTEXT & CONCURRENT INGESTION</h3>", unsafe_allow_html=True)
    
    # Status Block mimicking image_1.png
    st.info("🟢 HUGGINGFACE NODE STATUS: CONNECTED")
    
    # JD Input Area (Matches reference placeholder)
    job_description = st.text_area(
        "JOB PARAMETERS (JD & SKILLS)", 
        height=200, 
        placeholder="Define operational prerequisites, academic standards, and targeted key components..."
    )
    
    # Document Input Area
    uploaded_file = st.file_uploader("DOCUMENTS PIPELINE (Drop Resumes PDF)", type=["pdf"])
    
    # Pink Glow Action Button
    execute_scan = st.button("🚀 EXECUTE MULTI-AGENT SCAN", use_container_width=True)

with col_right:
    st.markdown("<h3 style='color: #ff007f;'>📊 DYNAMIC TALENT METRICS MATRICES</h3>", unsafe_allow_html=True)
    
    # Execution Logic
    if execute_scan and job_description and uploaded_file:
        with st.spinner("Processing deep analysis matrix diagnostics..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            
            if resume_text.strip():
                # Call LLM backend in utils.py
                results = analyze_resume(resume_text, job_description)
                
                # Dynamic Bar Chart for multiple profiles comparison (mocked Bob, Charlie, David for demo visual)
                chart_data = pd.DataFrame({
                    'Applicant': [results["name"], 'Bob Smith', 'Charlie Davis', 'David Kim'],
                    'Match %': [results["match_percentage"], 42, 91, 65],
                    'Status': [results["decision"], 'REJECT', 'HIRE', 'REJECT']
                })
                
                # Chart styling matching image_1.png cyan/pink aesthetic
                fig = px.bar(
                    chart_data, x='Applicant', y='Match %', color='Status',
                    color_discrete_map={'HIRE': '#00ffcc', 'REJECT': '#ff007f'},
                    text='Match %'
                )
                fig.update_layout(
                    plot_bgcolor='#161b22', paper_bgcolor='#161b22',
                    font_color='#c9d1d9', margin=dict(l=10, r=10, t=30, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Assessment Details Card
                st.markdown(f"### 👤 Profile Assessment: {results['name']}")
                
                # Compare Match against Sidebar Slider Threshold
                if results["match_percentage"] >= match_threshold:
                    st.markdown("### STATUS: <span style='color:#00ffcc;'>HIRE  (PASSED MATCH THRESHOLD)</span>", unsafe_allow_html=True)
                else:
                    st.markdown("### STATUS: <span style='color:#ff007f;'>REJECT (BELOW MATCH THRESHOLD)</span>", unsafe_allow_html=True)
                
                # Two-column detailed breakdown panel
                p_left, p_right = st.columns(2)
                with p_left:
                    st.markdown("**Core Capabilities Identified:**")
                    st.success(results["matching_skills"] if results["matching_skills"] else "None identified.")
                    st.markdown("**Extracted Academic Credentials:**")
                    st.code(results["education"])
                
                with p_right:
                    st.markdown("**Identified Technical Deficits:**")
                    st.error(results["missing_skills"] if results["missing_skills"] else "No missing skills flagged.")
                    
                st.markdown("---")
                st.markdown("**Generated Screening Assessment Directives:**")
                st.text(results["questions"])
            else:
                st.error("Text processing matrix failure. Check document formatting stream integrity.")
    else:
        # Default Chart Preview State for initial load
        default_data = pd.DataFrame({
            'Applicant': ['Alice Chen', 'Bob Smith', 'Charlie Davis', 'David Kim'],
            'Match %': [78, 42, 91, 65],
            'Status': ['HIRE', 'REJECT', 'HIRE', 'REJECT']
        })
        fig = px.bar(default_data, x='Applicant', y='Match %', color='Status',
                     color_discrete_map={'HIRE': '#00ffcc', 'REJECT': '#ff007f'})
        fig.update_layout(plot_bgcolor='#161b22', paper_bgcolor='#161b22', font_color='#c9d1d9')
        st.plotly_chart(fig, use_container_width=True)
        st.info("Waiting for configuration payload... Populate parameters and execute scanner matrix pipelines.")
