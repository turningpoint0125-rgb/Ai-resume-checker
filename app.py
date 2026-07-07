import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import extract_text_from_pdf, analyze_resume_deeply

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
    
    .cyber-header {
        color: #00ffcc;
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.6);
    }
    
    .cyber-status {
        color: #00ffcc;
        text-shadow: 0 0 8px rgba(0, 255, 204, 0.4);
    }
    
    .candidate-card {
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        background-color: #161b22;
        margin-bottom: 12px;
    }
    
    .card-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .candidate-name {
        color: #00ffcc;
        font-size: 1.1rem;
        font-weight: bold;
    }
    
    .match-badge {
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    
    .hire-badge {
        background-color: #00ffcc;
        color: #0d1117;
    }
    
    .reject-badge {
        background-color: #ff007f;
        color: white;
    }
    
    .skill-tag {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 6px;
        margin-bottom: 4px;
        font-size: 0.8rem;
    }
    
    .skill-tag-match {
        background-color: rgba(0, 255, 204, 0.15);
        color: #00ffcc;
        border: 1px solid #00ffcc;
    }
    
    .skill-tag-missing {
        background-color: rgba(255, 0, 127, 0.15);
        color: #ff007f;
        border: 1px solid #ff007f;
    }
    
    .section-label {
        color: #00ffcc;
        font-weight: bold;
        font-size: 0.85rem;
        margin-top: 8px;
        margin-bottom: 4px;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
    }
    
    .stTextInput>div>div>input {
        background-color: #0d1117 !important;
        border: 1px solid #00ffcc !important;
        color: #00ffcc !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("<h3 style='color: #ff007f;'>⚙️ SIDEBAR (SECURITY & CONTROL)</h3>", unsafe_allow_html=True)
    
    st.markdown("<p class='section-label'>MATCH THRESHOLD CONTROL</p>", unsafe_allow_html=True)
    match_threshold = st.slider("", min_value=0, max_value=100, value=60, step=5)
    
    st.markdown("---")
    st.markdown("<h3 style='color: #00ffcc;'>📋 CONTEXT & CONCURRENT INGESTION</h3>", unsafe_allow_html=True)
    
    st.info("🟢 HUGGINGFACE NODE STATUS: ✓ CONNECTED")
    
    st.markdown("<p class='section-label'>JOB PARAMETERS (JD & SKILLS)</p>", unsafe_allow_html=True)
    job_description = st.text_area(
        "Job Description",
        height=150,
        placeholder="Define the role... Required Skills, Education, Experience... Contextual qualifications: Python, Data Analysis, Missing: Python, AWS/Azure and Azure Learning exDriences to do Vor need...",
        label_visibility="collapsed"
    )
    
    st.markdown("<p class='section-label' style='margin-top: 16px;'>DOCUMENTS PIPELINE</p>", unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Drop Resumes (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<p style='color: #8b949e; font-size: 0.85rem; margin-top: 8px;'>BATCH UPLOAD (Multi-PDF Support)</p>", unsafe_allow_html=True)
    
    execute_scan = st.button("🚀 EXECUTE MULTI-AGENT SCAN", use_container_width=True, key="execute_btn")

# ========== MAIN HEADER ==========
col_title_left, col_title_right = st.columns([1, 1])
with col_title_left:
    st.markdown("<h1 class='cyber-header'>🤖 ADVANCED NEURAL ATS // PRODUCTION ENGINE</h1>", unsafe_allow_html=True)
with col_title_right:
    st.markdown("<p class='cyber-status' style='text-align: right; margin-top: 12px;'>Status: CLUSTER CONNECTED ✓</p>", unsafe_allow_html=True)

st.markdown("---")

# ========== MAIN CONTENT AREA ==========
if execute_scan and job_description and uploaded_files:
    results_list = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, f in enumerate(uploaded_files):
        status_text.text(f"🔍 Analyzing resume {idx + 1}/{len(uploaded_files)}: {f.name}")
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
        resume_text = extract_text_from_pdf(f)
        if resume_text.strip():
            result = analyze_resume_deeply(resume_text, job_description)
            result["filename"] = f.name
            results_list.append(result)
    
    progress_bar.empty()
    status_text.empty()
    
    if results_list:
        # ========== COMPARISON BAR CHART ==========
        st.markdown("<h2 style='color: #ff007f;'>📊 DYNAMIC TALENT METRICS MATRICES</h2>", unsafe_allow_html=True)
        
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
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="main_chart")
        
        # ========== SEARCH / FILTER ==========
        st.markdown("<p class='section-label'>🔎 FILTER PROFILES BY NAME/KEYWORDS</p>", unsafe_allow_html=True)
        search_query = st.text_input("Search candidates...", placeholder="Search by name or skill", label_visibility="collapsed")
        
        # Filter results
        if search_query:
            results_list = [
                r for r in results_list
                if search_query.lower() in r["name"].lower() or
                   search_query.lower() in (r.get("matching_skills", "") or "").lower() or
                   search_query.lower() in (r.get("missing_skills", "") or "").lower()
            ]
        
        # ========== INDIVIDUAL CANDIDATE CARDS ==========
        for result in results_list:
            with st.container():
                # Header Row
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"<div class='candidate-name'>👤 {result['name']}</div>", unsafe_allow_html=True)
                with col2:
                    badge_class = "hire-badge" if result["match_percentage"] >= match_threshold else "reject-badge"
                    badge_text = "✓ HIRE" if result["match_percentage"] >= match_threshold else "✕ REJECT"
                    st.markdown(f"<div class='match-badge {badge_class}'>{badge_text}</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div style='text-align:right; color:#ff007f; font-weight:bold; font-size:1.2rem;'>MATCH: {result['match_percentage']}%</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Content Row
                left_col, right_col = st.columns([1.5, 1])
                
                with left_col:
                    st.markdown(f"<p class='section-label'>👥 AGE</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #00ffcc; font-size: 1.1rem;'>{result['age']}</p>", unsafe_allow_html=True)
                    
                    st.markdown(f"<p class='section-label'>✅ SKILLS MATCHED</p>", unsafe_allow_html=True)
                    if result["matching_skills"] and result["matching_skills"].lower() != "none":
                        for skill in result["matching_skills"].split(","):
                            st.markdown(
                                f"<span class='skill-tag skill-tag-match'>{skill.strip()}</span>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("<span style='color: #8b949e;'>None identified</span>", unsafe_allow_html=True)
                    
                    st.markdown(f"<p class='section-label' style='margin-top: 12px;'>❌ MISSING</p>", unsafe_allow_html=True)
                    if result["missing_skills"] and result["missing_skills"].lower() != "none":
                        for skill in result["missing_skills"].split(","):
                            st.markdown(
                                f"<span class='skill-tag skill-tag-missing'>{skill.strip()}</span>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("<span style='color: #8b949e;'>None</span>", unsafe_allow_html=True)
                    
                    st.markdown(f"<p class='section-label' style='margin-top: 12px;'>🎓 EDUCATION</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #c9d1d9;'>{result['education']}</p>", unsafe_allow_html=True)
                
                with right_col:
                    # Radar Chart for Skills
                    skill_scores = result.get("skill_scores", {})
                    categories = list(skill_scores.keys())
                    values = list(skill_scores.values())
                    
                    fig_radar = go.Figure(data=go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        fillcolor='rgba(0, 255, 204, 0.2)',
                        line=dict(color='#00ffcc')
                    ))
                    fig_radar.update_layout(
                        polar=dict(
                            bgcolor='rgba(22, 27, 34, 0.5)',
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                tickfont=dict(color='#8b949e', size=8),
                                gridcolor='#30363d'
                            ),
                            angularaxis=dict(tickfont=dict(color='#c9d1d9', size=9))
                        ),
                        plot_bgcolor='#161b22',
                        paper_bgcolor='#161b22',
                        height=250,
                        margin=dict(l=40, r=40, t=40, b=40),
                        font=dict(color='#c9d1d9', family='Courier New')
                    )
                    st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_{result['name'].replace(' ', '_')}")
                
                st.markdown("---")
                
                # Interview Questions Section
                with st.expander("📋 VIEW INTERVIEW QUESTIONS (5)", expanded=False):
                    st.markdown("<p style='color: #00ffcc; font-weight: bold; margin-bottom: 8px;'>Expandable Active Interview Evaluation Framework</p>", unsafe_allow_html=True)
                    st.text(result.get("questions", "No questions generated."))

else:
    st.markdown("<h2 style='color: #ff007f;'>📊 DYNAMIC TALENT METRICS MATRICES</h2>", unsafe_allow_html=True)
    
    # Default preview chart
    default_data = pd.DataFrame({
        'Name': ['Alice Chen', 'Bob Smith', 'Charlie Davis', 'David Kim', 'Eva Wilson'],
        'Match %': [78, 42, 91, 65, 88],
        'Status': ['HIRE', 'REJECT', 'HIRE', 'REJECT', 'HIRE']
    })
    fig = px.bar(default_data, x='Name', y='Match %', color='Status',
                 color_discrete_map={'HIRE': '#00ffcc', 'REJECT': '#ff007f'})
    fig.update_layout(
        plot_bgcolor='#161b22', paper_bgcolor='#161b22', font_color='#c9d1d9',
        height=300, font_family='Courier New'
    )
    st.plotly_chart(fig, use_container_width=True, key="default_preview")
    st.info("⚙️ Configure job parameters and upload resumes to begin the neural analysis pipeline.")
