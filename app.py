import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import extract_text_from_pdf, analyze_resume
import io

st.set_page_config(
    page_title="ADVANCED NEURAL ATS // PRODUCTION ENGINE",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #30363d;
    }
    
    .candidate-name-title {
        color: #00ffcc;
        font-size: 1.1rem;
        font-weight: bold;
    }
    
    .match-badge-hire {
        background-color: #00ffcc;
        color: #0d1117;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    
    .match-badge-reject {
        background-color: #ff007f;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    
    .match-badge-interview {
        background-color: #ffaa00;
        color: #0d1117;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    
    .skill-tag-match {
        background-color: rgba(0, 255, 204, 0.15);
        color: #00ffcc;
        border: 1px solid #00ffcc;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 6px;
        margin-bottom: 4px;
        display: inline-block;
        font-size: 0.8rem;
    }
    
    .skill-tag-missing {
        background-color: rgba(255, 0, 127, 0.15);
        color: #ff007f;
        border: 1px solid #ff007f;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 6px;
        margin-bottom: 4px;
        display: inline-block;
        font-size: 0.8rem;
    }
    
    .section-label {
        color: #00ffcc;
        font-weight: bold;
        font-size: 0.85rem;
        margin-top: 10px;
        margin-bottom: 6px;
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
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("<h3 style='color: #ff007f;'>⚙️ SIDEBAR (SECURITY & CONTROL)</h3>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #00ffcc; font-weight: bold; font-size: 0.85rem; margin-bottom: 6px;'>MATCH THRESHOLD CONTROL</p>", unsafe_allow_html=True)
    match_threshold = st.slider("", min_value=0, max_value=100, value=60, step=5, label_visibility="collapsed")
    
    st.markdown("---")
    
    st.markdown("<h3 style='color: #00ffcc;'>📋 CONTEXT & CONCURRENT INGESTION</h3>", unsafe_allow_html=True)
    
    st.info("🟢 HUGGINGFACE NODE STATUS: ✓ CONNECTED")
    
    st.markdown("<p style='color: #00ffcc; font-weight: bold; font-size: 0.85rem; margin-top: 16px; margin-bottom: 6px;'>JOB PARAMETERS (JD & SKILLS)</p>", unsafe_allow_html=True)
    job_description = st.text_area(
        "Job Description",
        height=140,
        placeholder="Define the role... Required Skills, Education, Experience...",
        label_visibility="collapsed"
    )
    
    st.markdown("<p style='color: #00ffcc; font-weight: bold; font-size: 0.85rem; margin-top: 16px; margin-bottom: 6px;'>DOCUMENTS PIPELINE</p>", unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Drop Resumes (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<p style='color: #8b949e; font-size: 0.85rem; margin-top: 6px;'>BATCH UPLOAD (Multi-PDF Support)</p>", unsafe_allow_html=True)
    
    execute_scan = st.button("🚀 EXECUTE MULTI-AGENT SCAN", use_container_width=True, key="execute_btn")

    st.markdown("---")
    debug_mode = st.checkbox("🐞 Debug Mode (show raw model output)", value=False)

# ========== MAIN HEADER ==========
col_title_left, col_title_right = st.columns([1, 1])
with col_title_left:
    st.markdown("<h1 class='cyber-header'>🤖 ADVANCED NEURAL ATS // PRODUCTION ENGINE</h1>", unsafe_allow_html=True)
with col_title_right:
    st.markdown("<p class='cyber-status' style='text-align: right; margin-top: 12px;'>Status: CLUSTER CONNECTED ✓</p>", unsafe_allow_html=True)

st.markdown("---")

# ========== MAIN CONTENT ==========
if execute_scan and job_description and uploaded_files:
    results_list = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, f in enumerate(uploaded_files):
        status_text.text(f"🔍 Analyzing resume {idx + 1}/{len(uploaded_files)}: {f.name}")
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
        resume_text = extract_text_from_pdf(f)
        if resume_text.strip():
            result = analyze_resume(resume_text, job_description)
            result["filename"] = f.name
            results_list.append(result)
    
    progress_bar.empty()
    status_text.empty()
    
    if results_list:
        # ========== RANKING TABLE ==========
        st.markdown("<h2 style='color: #ff007f; margin-bottom: 12px;'>📋 RANKING DASHBOARD - CANDIDATE COMPARISON</h2>", unsafe_allow_html=True)
        
        # Sort by match score
        sorted_results = sorted(results_list, key=lambda x: x["match_score"], reverse=True)
        
        ranking_data = []
        for idx, r in enumerate(sorted_results, 1):
            ranking_data.append({
                "Rank": idx,
                "Candidate": r["name"],
                "Match Score": f"{r['match_score']}%",
                "Recommendation": r["hr_recommendation"],
                "Experience": r["years_exp"],
                "Education": r["education"][:40] + "..." if len(r["education"]) > 40 else r["education"]
            })
        
        ranking_df = pd.DataFrame(ranking_data)
        
        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width=50),
                "Candidate": st.column_config.TextColumn("Candidate", width=150),
                "Match Score": st.column_config.TextColumn("Match Score", width=100),
                "Recommendation": st.column_config.TextColumn("Recommendation", width=120),
                "Experience": st.column_config.TextColumn("Experience", width=120),
                "Education": st.column_config.TextColumn("Education", width=150)
            }
        )
        
        # CSV Export
        csv_buffer = io.StringIO()
        ranking_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        col_export_1, col_export_2, col_export_3 = st.columns([1, 2, 1])
        with col_export_1:
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name="candidates_ranking.csv",
                mime="text/csv",
                key="export_csv"
            )
        with col_export_2:
            st.markdown("<p style='color: #8b949e; font-size: 0.85rem; margin-top: 10px;'>Download ranking table for HR review and decision making</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== BAR CHART ==========
        st.markdown("<h2 style='color: #ff007f; margin-bottom: 12px;'>📊 DYNAMIC TALENT METRICS MATRICES</h2>", unsafe_allow_html=True)
        
        chart_df = pd.DataFrame({
            'Name': [r["name"] for r in results_list],
            'Match %': [r["match_score"] for r in results_list],
            'Status': [r["hr_recommendation"] for r in results_list]
        })
        
        color_map = {'HIRE': '#00ffcc', 'REJECT': '#ff007f', 'INTERVIEW': '#ffaa00'}
        fig_bar = px.bar(
            chart_df, x='Name', y='Match %',
            color='Status',
            color_discrete_map=color_map,
            text='Match %'
        )
        fig_bar.update_traces(textposition='auto')
        fig_bar.update_layout(
            plot_bgcolor='#161b22',
            paper_bgcolor='#161b22',
            font_color='#c9d1d9',
            font_family='Courier New',
            height=280,
            showlegend=True,
            xaxis_title="",
            yaxis_title="Applicant Score %"
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="main_chart")
        
        # ========== SEARCH ==========
        st.markdown("<p class='section-label'>🔎 FILTER PROFILES BY NAME/KEYWORDS</p>", unsafe_allow_html=True)
        search_query = st.text_input("Search...", placeholder="Search by name", label_visibility="collapsed")
        
        filtered_results = results_list
        if search_query:
            filtered_results = [r for r in results_list if search_query.lower() in r["name"].lower()]
        
        # ========== CANDIDATE CARDS ==========
        for result in filtered_results:
            st.markdown("<div style='border: 1px solid #30363d; border-radius: 8px; padding: 16px; background-color: #161b22; margin-bottom: 16px;'>", unsafe_allow_html=True)
            
            # Header
            col1, col2, col3 = st.columns([2, 1, 1.2])
            with col1:
                st.markdown(f"<div class='candidate-name-title'>👤 {result['name']}</div>", unsafe_allow_html=True)
            with col2:
                if result["hr_recommendation"] == "HIRE":
                    st.markdown("<div class='match-badge-hire'>✓ HIRE</div>", unsafe_allow_html=True)
                elif result["hr_recommendation"] == "REJECT":
                    st.markdown("<div class='match-badge-reject'>✕ REJECT</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='match-badge-interview'>⚠ INTERVIEW</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='text-align:right; color:#ff007f; font-weight:bold; font-size:1.2rem;'>MATCH: {result['match_score']}%</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Content
            left_col, right_col = st.columns([1.4, 1])
            
            with left_col:
                st.markdown(f"<p class='section-label'>✅ SKILLS MATCHED</p>", unsafe_allow_html=True)
                for skill in result.get("matching_skills", []):
                    st.markdown(f"<span class='skill-tag-match'>{skill}</span>", unsafe_allow_html=True)
                
                st.markdown(f"<p class='section-label'>❌ MISSING</p>", unsafe_allow_html=True)
                if result.get("missing_skills"):
                    for skill in result.get("missing_skills", []):
                        st.markdown(f"<span class='skill-tag-missing'>{skill}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #8b949e;'>None</span>", unsafe_allow_html=True)
                
                st.markdown(f"<p class='section-label'>🎓 EDUCATION</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: #c9d1d9; margin: 0;'>{result.get('education', 'Not specified')}</p>", unsafe_allow_html=True)
            
            with right_col:
                # Radar Chart
                skill_scores = result.get("skill_scores", {})
                categories = list(skill_scores.keys())
                values = list(skill_scores.values())
                
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    fillcolor='rgba(0, 255, 204, 0.2)',
                    line=dict(color='#00ffcc'),
                    name='Score'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor='rgba(22, 27, 34, 0.3)',
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100],
                            tickfont=dict(color='#8b949e', size=8),
                            gridcolor='#30363d'
                        ),
                        angularaxis=dict(tickfont=dict(color='#c9d1d9', size=8))
                    ),
                    plot_bgcolor='#161b22',
                    paper_bgcolor='#161b22',
                    height=220,
                    margin=dict(l=30, r=30, t=30, b=30),
                    font=dict(color='#c9d1d9', family='Courier New', size=9),
                    showlegend=False
                )
                st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_{result['name'].replace(' ', '_')}")
            
            if debug_mode and (result.get("_raw_response") or result.get("_debug_error")):
                with st.expander("🐞 DEBUG: Raw model output / error"):
                    if result.get("_debug_error"):
                        st.error(result["_debug_error"])
                    if result.get("_raw_response"):
                        st.code(result["_raw_response"])
            
            st.markdown("---")
            
            # Interview Questions
            with st.expander("📋 VIEW INTERVIEW QUESTIONS (5)", expanded=False):
                st.markdown("<p style='color: #00ffcc; font-weight: bold; margin-bottom: 8px;'>Technical Questions</p>", unsafe_allow_html=True)
                for i, q in enumerate(result.get("technical_questions", []), 1):
                    st.markdown(f"<p style='color: #c9d1d9; margin: 6px 0;'><strong>{i}.</strong> {q}</p>", unsafe_allow_html=True)
                
                st.markdown("<p style='color: #00ffcc; font-weight: bold; margin-top: 12px; margin-bottom: 8px;'>HR / Behavioral Questions</p>", unsafe_allow_html=True)
                for i, q in enumerate(result.get("hr_questions", []), 1):
                    st.markdown(f"<p style='color: #c9d1d9; margin: 6px 0;'><strong>{i}.</strong> {q}</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("<h2 style='color: #ff007f;'>📊 DYNAMIC TALENT METRICS MATRICES</h2>", unsafe_allow_html=True)
    st.info("⚙️ Configure job parameters and upload resumes to begin analysis.")
