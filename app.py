import streamlit as st
import pandas as pd
import io
import plotly.express as px
from utils import extract_text_from_pdf, analyze_resume

# Page Configuration
st.set_page_config(page_title="AI Resume Intelligence Platform", page_icon="🤖", layout="wide")

# Modern High-Tech UI Layout Injections
st.markdown("""
    <style>
    .main { background-color: #0a0c10; color: #f0f6fc; }
    h1 { color: #00ffcc; text-shadow: 0 0 15px rgba(0,255,204,0.6); font-family: 'Courier New', monospace; font-weight: 800; }
    h2, h3 { color: #ff007f; text-shadow: 0 0 10px rgba(255,0,127,0.3); }
    .stButton>button { 
        background: linear-gradient(45deg, #00ffcc, #0099ff); color: #000000; font-weight: bold; 
        border-radius: 8px; border: none; box-shadow: 0 0 20px rgba(0,255,204,0.4);
        width: 100%; transition: all 0.3s ease; font-size: 1.1rem; padding: 10px;
    }
    .stButton>button:hover { background: linear-gradient(45deg, #ff007f, #ff00cc); color: #ffffff; box-shadow: 0 0 20px rgba(255,0,127,0.6); }
    .card { 
        background: #161b22; padding: 25px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .hire-tag { color: #00ff66; font-weight: bold; font-size: 1.4rem; text-shadow: 0 0 10px rgba(0,255,102,0.5); }
    .reject-tag { color: #ff3333; font-weight: bold; font-size: 1.4rem; text-shadow: 0 0 10px rgba(255,51,51,0.5); }
    .skill-container { background: #0d1117; padding: 10px; border-radius: 6px; border-left: 3px solid #00ffcc; margin: 8px 0; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 ADVANCED NEURAL ATS // PRODUCTION ENGINE")
st.write("Next-generation multi-agent pipeline using Streamlit Cloud secured token keys.")

# Inject token securely from Streamlit Secrets backend
if "HUGGINGFACEHUB_API_TOKEN" in st.secrets:
    import os
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
else:
    st.sidebar.error("⚠️ Config Error: 'HUGGINGFACEHUB_API_TOKEN' missing from Streamlit secrets setup.")

# Sidebar Controls (Cleaned up - no token text box)
st.sidebar.header("🎛️ CONTROLS & THRESHOLDS")
min_match_slider = st.sidebar.slider("Minimum Match Threshold Filter (%)", min_value=0, max_value=100, value=60)
st.sidebar.markdown("---")
st.sidebar.write("⚡ Cluster Engine Status: Secure Node Connected")

# Primary Grid Layout split
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Context & Directives")
    job_description = st.text_area("Paste Corporate Job Requirements Framework:", height=180, placeholder="Define operational prerequisites, academic standards, and targeted key components...")
    
    st.subheader("📂 Concurrent File Ingestion Pipeline")
    uploaded_files = st.file_uploader("Drop Target Candidate Resumes (Batch Multi-PDF Processing)", type=["pdf"], accept_multiple_files=True)

# Application Memory State Initialization
if "results_cache" not in st.session_state:
    st.session_state.results_cache = []

if st.button("🚀 EXECUTE MULTI-AGENT SCAN"):
    import os
    if "HUGGINGFACEHUB_API_TOKEN" not in os.environ:
        st.error("Operation Denied: Hugging Face API key is missing from backend secrets setup.")
    elif not job_description or not uploaded_files:
        st.warning("Buffer Error: Provide complete parameters (Job Requirements Context + Input Target Files).")
    else:
        temporary_results = []
        with st.spinner("Decoding document vector spaces and tracking skill matrices..."):
            for file in uploaded_files:
                raw_text = extract_text_from_pdf(file)
                analysis = analyze_resume(raw_text, job_description)
                analysis['file_name'] = file.name
                temporary_results.append(analysis)
        st.session_state.results_cache = temporary_results

# Analytics Engine Render Process
if st.session_state.results_cache:
    df_full = pd.DataFrame(st.session_state.results_cache)
    df_filtered = df_full[df_full['match_percentage'] >= min_match_slider]

    with col2:
        st.subheader("📊 Dynamic Talent Metrics Plot")
        if not df_filtered.empty:
            fig = px.bar(
                df_filtered, x='name', y='match_percentage', 
                color='decision',
                color_discrete_map={'HIRE': '#00ff66', 'REJECT': '#ff3333'},
                title=f"Applicants Crossing Threshold Target (>= {min_match_slider}%)",
                labels={'match_percentage': 'Match Compatibility Score (%)', 'name': 'Candidate Identity'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                df_full.to_excel(writer, index=False, sheet_name='ATS_Evaluation_Summary')
            excel_data = output_buffer.getvalue()
            
            st.download_button(
                label="📥 EXPORT BATCH REPORT TO EXCEL",
                data=excel_data,
                file_name="ATS_Neural_Evaluation_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No candidates match your minimum slider criteria target.")

    # Lower Grid Layout Output Row
    st.markdown("---")
    st.subheader("🗂️ Decoded Candidate Log Records")
    
    if not df_filtered.empty:
        search_query = st.text_input("🔍 Filter Profiles by Name or Keywords:", "")
        
        for _, row in df_filtered.iterrows():
            if search_query.lower() in row['name'].lower() or search_query.lower() in row['file_name'].lower():
                with st.container():
                    st.markdown(f"""
                    <div class="card">
                        <h3>👤 Profile Identity: {row['name']}</h3>
                        <p><b>Data Track File Source:</b> {row['file_name']} | <b>Academic Verification:</b> {row['education']}</p>
                        <p><b>Pipeline Match Coefficient Index:</b> {row['match_percentage']}%</p>
                    """, unsafe_allow_html=True)
                    
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        st.markdown(f'<div class="skill-container"><b>✅ Verified Matching Skills:</b><br>{row["matching_skills"] if row["matching_skills"] else "None Detected"}</div>', unsafe_allow_html=True)
                    with col_s2:
                        st.markdown(f'<div class="skill-container" style="border-left-color: #ff007f;"><b>⚠️ Identified Discrepancies / Missing Skills:</b><br>{row["missing_skills"] if row["missing_skills"] else "None Detected"}</div>', unsafe_allow_html=True)
                    
                    if row['decision'] == 'HIRE':
                        st.markdown("<p class='hire-tag'>🟢 ROUTING DISPATCH: HIGH PRIORITY GREEN LIGHT // INITIATE HIRING</p>", unsafe_allow_html=True)
                        with st.expander("🎯 Active Technical Interview Matrix & Grading Panel"):
                            st.code(row['questions'], language="text")
                            st.write("---")
                            st.write("💡 *Live Recruiter Scoring Panel:*")
                            r1 = st.select_slider(f"Candidate Response Track Rating ({row['name']})", options=["Unsatisfactory", "Adequate", "Exemplary"], key=f"score_{row['name']}")
                    else:
                        st.markdown("<p class='reject-tag'>🔴 ROUTING DISPATCH: RED LIGHT // TERMINATE RUNTIME PROFILE</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
