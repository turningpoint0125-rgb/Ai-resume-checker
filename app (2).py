import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import extract_text_from_pdf, analyze_resume

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="ADVANCED NEURAL ATS // PRODUCTION ENGINE", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CYBERPUNK NEON CSS ==========
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Courier New', Courier, monospace;
    }
    
    .cyber-title {
        color: #00ffcc;
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.6);
        font-size: 2rem;
        margin-bottom: 5px;
    }
    
    .cyber-status {
        color: #00ffcc;
        font-size: 0.9rem;
        text-shadow: 0 0 8px rgba(0, 255, 204, 0.4);
    }
    
    .candidate-card {
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        background-color: #161b22;
        margin-bottom: 20px;
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 12px;
    }
    
    .candidate-name {
        color: #00ffcc;
        font-size: 1.3rem;
        font-weight: bold;
    }
    
    .match-score {
        color: #ff007f;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    .hire-badge {
        background-color: #00ffcc;
        color: #0d1117;
        padding: 6px 14px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    
    .reject-badge {
        background-color: #ff007f;
        color: white;
        padding: 6px 14px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    
    .skills-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    
    .skill-tag-match {
        display: inline-block;
        background-color: rgba(0, 255, 204, 0.15);
        color: #00ffcc;
        border: 1px solid #00ffcc;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 6px;
        margin-bottom: 4px;
        font-size: 0.85rem;
    }
    
    .skill-tag-missing {
        display: inline-block;
        background-color: rgba(255, 0, 127, 0.15);
        color: #ff007f;
        border: 1px solid #ff007f;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 6px;
        margin-bottom: 4px;
        font-size: 0.85rem;
    }
    
    .section-label {
        color: #00ffcc;
        font-weight: bold;
        font-size: 0.9rem;
        margin-top: 12px;
        margin-bottom: 6px;
    }
    
    .questions-box {
        background-color: #0d1117;
        border-left: 3px solid #ff007f;
        padding: 12px;
        border-radius: 4px;
        margin-top: 12px;
        color: #c9d1d9;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("<h3 style='color: #ff007f;'>⚙️ SIDEBAR CONTROL</h3>", unsafe_allow_html=True)
    match_threshold = st.slider("MATCH THRESHOLD", min_value=0, max_value=100, value=60, step=5)
    st.markdown("---")
    st.markdown("<span class='cyber-status'>● STATUS: CLUSTER CONNECTED</span>", unsafe_allow_html=True)

# ========== MAIN HEADER ==========
st.markdown("<h1 class='cyber-title'>🤖 ADVANCED NEURAL ATS // PRODUCTION ENGINE</h1>", unsafe_allow_html=True)

col_header_left, col_header_right = st.columns([1, 1])
with col_header_left:
    st.markdown("<p style='color: #8b949e; margin: 0;'>Next-generation multi-agent pipeline using Streamlit Cloud</p>", unsafe_allow_html=True)
with col_header_right:
    st.markdown("<p class='cyber-status' style='text-align: right;'>STATUS: CLUSTER CONNECTED 🟢</p>", unsafe_allow_html=True)

st.markdown("---")

# ========== INPUT SECTION ==========
col_input_left, col_input_right = st.columns([1, 1.2])

with col_input_left:
    st.markdown("<h3 style='color: #00ffcc;'>📋 CONTEXT & CONCURRENT INGESTION</h3>", unsafe_allow_html=True)
    
    st.info("🟢 HUGGINGFACE NODE STATUS: CONNECTED")
    
    job_description = st.text_area(
        "JOB PARAMETERS (JD & SKILLS)",
        height=180,
        placeholder="Define operational prerequisites, academic standards, and targeted key components..."
    )
    
    st.markdown("<p style='color: #00ffcc; font-weight: bold; margin-top: 15px;'>📄 DOCUMENTS PIPELINE</p>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Drop Resumes (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    execute_scan = st.button("🚀 EXECUTE MULTI-AGENT SCAN", use_container_width=True)

with col_input_right:
    st.markdown("<h3 style='color: #ff007f;'>📊 DYNAMIC TALENT METRICS MATRICES</h3>", unsafe_allow_html=True)
    
    # Results Section
    if execute_scan and job_description and uploaded_files:
        results_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, f in enumerate(uploaded_files):
            status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {f.name}")
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
            resume_text = extract_text_from_pdf(f)
            if resume_text.strip():
                result = analyze_resume(resume_text, job_description)
                result["filename"] = f.name
                results_list.append(result)
        
        progress_bar.empty()
        status_text.empty()
        
        if results_list:
            # ========== COMPARISON BAR CHART ==========
            chart_df = pd.DataFrame({
                'Name': [r["name"] for r in results_list],
                'Match %': [r["match_percentage"] for r in results_list],
                'Status': [r["decision"] for r in results_list]
            })
            
            fig_bar = px.bar(
                chart_df, x='Name', y='Match %',
                color='Status',
                color_discrete_map={'HIRE': '#00ffcc', 'REJECT': '#ff007f'},
                text='Match %'
            )
            fig_bar.update_traces(textposition='auto')
            fig_bar.update_layout(
                plot_bgcolor='#161b22',
                paper_bgcolor='#161b22',
                font_color='#c9d1d9',
                font_family='Courier New',
                height=320,
                showlegend=True,
                hovermode='x unified'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # ========== INDIVIDUAL CANDIDATE CARDS ==========
            for result in results_list:
                with st.container():
                    # Header Row: Name | Age | Match% | HIRE/REJECT
                    card_col1, card_col2, card_col3, card_col4 = st.columns([2, 1, 1.2, 1.2])
                    
                    with card_col1:
                        st.markdown(f"<div class='candidate-name'>{result['name']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color: #8b949e; font-size: 0.85rem;'>{result['filename']}</span>", unsafe_allow_html=True)
                    
                    with card_col2:
                        st.markdown(f"<div style='color: #8b949e;'>AGE</div><div style='color: #00ffcc; font-size: 1.2rem;'>{result['age']}</div>", unsafe_allow_html=True)
                    
                    with card_col3:
                        st.markdown(f"<div style='color: #8b949e;'>MATCH</div><div class='match-score'>{result['match_percentage']}%</div>", unsafe_allow_html=True)
                    
                    with card_col4:
                        if result["match_percentage"] >= match_threshold:
                            st.markdown("<div class='hire-badge'>✓ HIRE</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='reject-badge'>✕ REJECT</div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Skills and Chart Row
                    skills_col, chart_col = st.columns([1.5, 1])
                    
                    with skills_col:
                        st.markdown("<div class='section-label'>SKILLS MATCHED</div>", unsafe_allow_html=True)
                        if result["matching_skills"] and result["matching_skills"].lower() != "none":
                            for skill in result["matching_skills"].split(","):
                                st.markdown(
                                    f"<span class='skill-tag-match'>{skill.strip()}</span>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown("<span style='color: #8b949e;'>None identified</span>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='section-label' style='margin-top: 16px;'>MISSING SKILLS</div>", unsafe_allow_html=True)
                        if result["missing_skills"] and result["missing_skills"].lower() != "none":
                            for skill in result["missing_skills"].split(","):
                                st.markdown(
                                    f"<span class='skill-tag-missing'>{skill.strip()}</span>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown("<span style='color: #8b949e;'>None</span>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='section-label' style='margin-top: 16px;'>EDUCATION</div>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color: #c9d1d9;'>{result['education']}</span>", unsafe_allow_html=True)
                    
                    with chart_col:
                        # Pie/Donut Chart
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=['Match', 'Gap'],
                            values=[result['match_percentage'], 100 - result['match_percentage']],
                            hole=0.4,
                            marker=dict(colors=['#00ffcc', '#ff007f'])
                        )])
                        fig_pie.update_layout(
                            plot_bgcolor='#161b22',
                            paper_bgcolor='#161b22',
                            font_color='#c9d1d9',
                            height=200,
                            margin=dict(l=10, r=10, t=10, b=10),
                            showlegend=True
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Questions Section (Collapsible)
                    with st.expander("📋 VIEW INTERVIEW QUESTIONS (5)", expanded=False):
                        st.markdown("<div class='questions-box'>", unsafe_allow_html=True)
                        st.markdown("<p style='color: #00ffcc; font-weight: bold; margin-bottom: 8px;'>Active Interview Evaluation Framework</p>", unsafe_allow_html=True)
                        st.text(result["questions"])
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("")  # Spacing
    else:
        # Default state
        default_data = pd.DataFrame({
            'Name': ['Alice Chen', 'Bob Smith', 'Charlie Davis'],
            'Match %': [78, 42, 91],
            'Status': ['HIRE', 'REJECT', 'HIRE']
        })
        fig = px.bar(default_data, x='Name', y='Match %', color='Status',
                     color_discrete_map={'HIRE': '#00ffcc', 'REJECT': '#ff007f'})
        fig.update_layout(
            plot_bgcolor='#161b22', paper_bgcolor='#161b22', font_color='#c9d1d9',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("Waiting for configuration payload... Populate parameters and execute scanner matrix pipelines.")
