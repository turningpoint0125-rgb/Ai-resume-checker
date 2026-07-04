import streamlit as st
import pandas as pd
import plotly.express as px
from utils import extract_text_from_pdf, analyze_resume

st.set_page_config(
    page_title="ADVANCED NEURAL ATS // PRODUCTION ENGINE", 
    page_icon="🤖", 
    layout="wide"
)

# Cyberpunk UI Custom Styling Blocks
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: monospace; }
    .cyber-title { color: #00ffcc; text-shadow: 0 0 10px rgba(0, 255, 204, 0.6); font-size: 2.2rem; font-weight: bold; }
    .stButton>button { background: linear-gradient(45deg, #ff007f, #7928ca) !important; color: white !important; font-weight: bold; box-shadow: 0 0 15px rgba(255, 0, 127, 0.4); }
    /* Card design styling */
    .candidate-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h3 style='color: #ff007f;'>SIDEBAR CONTROL</h3>", unsafe_allow_html=True)
    match_threshold = st.slider("MATCH THRESHOLD CONTROL", min_value=0, max_value=100, value=60, step=5)
    st.markdown("---")
    st.markdown("<span style='color: #00ffcc;'>● STATUS: CLUSTER CONNECTED</span>", unsafe_allow_html=True)

st.markdown("<h1 class='cyber-title'>🤖 ADVANCED NEURAL ATS // MULTI-SCAN PRODUCTION ENGINE</h1>", unsafe_allow_html=True)
st.markdown("---")

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.markdown("<h3 style='color: #00ffcc;'>📋 CONTEXT CONFIGURATION</h3>", unsafe_allow_html=True)
    
    job_description = st.text_area(
        "JOB PARAMETERS (JD & SKILLS)", 
        height=180, 
        placeholder="Define operational prerequisites and targeted key components..."
    )
    
    uploaded_files = st.file_uploader(
        "DOCUMENTS PIPELINE (Upload Multiple Resumes)", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    
    execute_scan = st.button("🚀 EXECUTE MULTI-AGENT SCAN", use_container_width=True)

with col_right:
    st.markdown("<h3 style='color: #ff007f;'>📊 DYNAMIC PROFILE ASSESSMENT</h3>", unsafe_allow_html=True)
    
    if execute_scan and job_description and uploaded_files:
        all_results = []
        
        with st.spinner("Processing deep analysis batch telemetry matrices..."):
            for file in uploaded_files:
                text_stream = extract_text_from_pdf(file)
                if text_stream.strip():
                    analysis = analyze_resume(text_stream, job_description)
                    # Override decision based on your real-time slider threshold
                    analysis["decision"] = "PASS ✅" if analysis["match_percentage"] >= match_threshold else "REJECT ❌"
                    all_results.append(analysis)
            
            if all_results:
                df = pd.DataFrame(all_results)
                
                # Global visual bar overview chart
                fig = px.bar(
                    df, x='name', y='match_percentage', color='decision',
                    color_discrete_map={'PASS ✅': '#00ffcc', 'REJECT ❌': '#ff007f'},
                    text='match_percentage', title="Comparative Fit Spectrum Matrix"
                )
                fig.update_layout(plot_bgcolor='#161b22', paper_bgcolor='#161b22', font_color='#c9d1d9')
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### 🗂️ CANDIDATE ASSESSMENT MATRICES")
                
                # CREATE INTERACTIVE TABS FOR EACH APPLICANT
                candidate_names = [candidate["name"] for candidate in all_results]
                tabs = st.tabs(candidate_names)
                
                for idx, tab in enumerate(tabs):
                    candidate = all_results[idx]
                    status_color = "#00ffcc" if "PASS" in candidate["decision"] else "#ff007f"
                    
                    with tab:
                        st.markdown(f"""
                        <div class="candidate-card">
                            <h2 style="color: {status_color}; margin-top:0;">{candidate['name']}</h2>
                            <p><b>STATUS EVALUATION:</b> <span style="color:{status_color}; font-weight:bold; font-size:1.2rem;">{candidate['decision']} ({candidate['match_percentage']}%)</span></p>
                            <p><b>🎓 ACADEMIC CREDENTIALS:</b> {candidate['education']}</p>
                            <hr style="border-color: #30363d;">
                            <p style="color: #00ffcc;"><b>🎯 MATCHING SKILLS IDENTIFIED:</b><br>{candidate['matching_skills']}</p>
                            <p style="color: #ff007f;"><b>⚠️ DEFICIT VULNERABILITIES (MISSING):</b><br>{candidate['missing_skills']}</p>
                            <hr style="border-color: #30363d;">
                            <div style="background-color: #0d1117; padding: 12px; border-left: 4px solid {status_color}; border-radius: 4px;">
                                <span style="color: #8b949e;"><b>💡 TARGETED INTERVIEW QUESTION:</b></span><br>
                                <span style="font-size: 1.05rem; color: #ffffff;">{candidate['questions']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("Matrix processing failure. Ensure valid PDF content fields.")
    else:
        st.info("Awaiting file payload stream array inputs. Select multiple files to execute.")
