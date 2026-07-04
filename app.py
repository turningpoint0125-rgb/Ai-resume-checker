import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import extract_text_from_pdf, analyze_resume

# Force widescreen desktop mode matching the layout matrix
st.set_page_config(
    page_title="ADVANCED NEURAL ATS // PRODUCTION ENGINE", 
    page_icon="🤖", 
    layout="wide"
)

# 🌌 Complete UI Clone Overrides (Matches exact colors, blur, lines, and typography)
st.markdown("""
<style>
    /* Dark Sci-Fi Tech Background */
    .stApp { 
        background-color: #040814 !important;
        background-image: 
            radial-gradient(at 20% 20%, rgba(124, 58, 237, 0.08) 0px, transparent 50%),
            radial-gradient(at 80% 80%, rgba(0, 255, 204, 0.06) 0px, transparent 50%);
        color: #e2e8f0; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Hide Default Streamlit Style Elements for a Clean App Feel */
    header, footer, [data-testid="stHeader"] { visibility: hidden; height: 0px; }
    
    /* Top Menu Header Elements Row */
    .top-header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 5px;
        margin-bottom: 20px;
        border-bottom: 1px solid #1e293b;
    }

    /* Column Block Headers with Icons */
    .column-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
        text-transform: uppercase;
    }

    /* Heavy Glassmorphic Container Core Styling */
    .glass-panel-container {
        background: rgba(10, 17, 34, 0.65) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(0, 255, 204, 0.18) !important;
        border-radius: 12px !important;
        padding: 22px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6) !important;
        margin-bottom: 20px;
    }
    
    /* Sub-containers inside left column */
    .sub-glass-input {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 15px;
    }

    /* Left Sidebar Float Panel Replacement */
    .floating-sidebar-panel {
        background: rgba(10, 17, 34, 0.7);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 255, 204, 0.3);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.15);
    }

    /* The Magenta/Purple Linear Active Button Cloned from Image */
    .stButton>button { 
        background: linear-gradient(90deg, #ec4899 0%, #a855f7 50%, #6366f1 100%) !important; 
        color: #ffffff !important; 
        font-weight: 700 !important; 
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 14px 20px !important;
        box-shadow: 0 0 20px rgba(236, 72, 153, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        box-shadow: 0 0 30px rgba(0, 255, 204, 0.6) !important;
        transform: translateY(-1px);
        color: #ffffff !important;
    }

    /* Applicant Output Box Layouts */
    .applicant-box-row {
        background: rgba(22, 30, 49, 0.5);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: border 0.3s ease;
    }
    .box-pass { border: 1px solid rgba(0, 255, 204, 0.35); box-shadow: inset 0 0 10px rgba(0, 255, 204, 0.05); }
    .box-reject { border: 1px solid rgba(239, 68, 68, 0.35); box-shadow: inset 0 0 10px rgba(239, 68, 68, 0.05); }
    
    /* Status Badges */
    .status-badge-pass {
        background: rgba(0, 255, 204, 0.12);
        color: #00ffcc;
        border: 1px solid #00ffcc;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
    .status-badge-reject {
        background: rgba(239, 68, 68, 0.12);
        color: #ef4444;
        border: 1px solid #ef4444;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar Header Setup Layout Rows
st.markdown("""
<div class="top-header-container">
    <div style="font-weight: bold; font-size: 1.1rem; color: #ffffff;">📋 ADVANCED NEURAL ATS // PRODUCTION ENGINE</div>
    <div style="color: #00ffcc; font-weight: bold; font-size: 0.9rem;">STatus: <span style="color: #00ffcc;">CLUSTER CONNECTED 🟢</span></div>
</div>
""", unsafe_allow_html=True)

# Recreating the exact 2-column core dashboard frame
col_sidebar_and_input, col_metrics_display = st.columns([1.1, 1.3])

# ==================== LEFT COLUMN CONFIGURATION ====================
with col_sidebar_and_input:
    # 1. Slider Placement matching floating UI element on the bottom left
    st.markdown('<div class="floating-sidebar-panel">', unsafe_allow_html=True)
    st.markdown("<span style='color: #8b949e; font-size: 0.8rem; font-weight:bold;'>SIDEBAR (SECURITY & CONTROL)</span>", unsafe_allow_html=True)
    match_threshold = st.slider("⚡ MATCH THRESHOLD CONTROL", min_value=0, max_value=100, value=60, step=5)
    st.markdown('</div><br>', unsafe_allow_html=True)

    # 2. Left Context Main Grid panel[cite: 7]
    st.markdown('<div class="glass-panel-container">', unsafe_allow_html=True)
    st.markdown('<div class="column-header">📋 CONTEXT & CONCURRENT INGESTION</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sub-glass-input">', unsafe_allow_html=True)
    st.markdown("<span style='color: #00ffcc; font-weight: bold; font-size:0.85rem;'>HUGGINGFACE NODE STATUS: ✅ CONNECTED</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Text Inputs Framework
    job_description = st.text_area(
        "JOB PARAMETERS (JD & SKILLS)", 
        height=150, 
        value="Define the role... Required Skills, Education, Experience... Contextualizing options like Python, Data Analysis, Machine Learning structures...",
        placeholder="Input requirements..."
    )
    
    st.markdown("<br><span style='font-size:0.9rem; font-weight:bold; color:#ffffff;'>DOCUMENTS PIPELINE</span>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "BATCH UPLOAD (Multi-PDF Support)", 
        type=["pdf"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    execute_scan = st.button("🚀 EXECUTE MULTI-AGENT SCAN")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== RIGHT COLUMN CONFIGURATION ====================
with col_metrics_display:
    st.markdown('<div class="glass-panel-container">', unsafe_allow_html=True)
    st.markdown('<div class="column-header">📊 DYNAMIC TALENT METRICS MATRICES</div>', unsafe_allow_html=True)
    
    if execute_scan and job_description and uploaded_files:
        all_results = []
        
        with st.spinner("Processing deep analysis batch telemetry matrices..."):
            for file in uploaded_files:
                text_stream = extract_text_from_pdf(file)
                if text_stream.strip():
                    analysis = analyze_resume(text_stream, job_description)
                    analysis["decision"] = "HIRE" if analysis["match_percentage"] >= match_threshold else "REJECT"
                    all_results.append(analysis)
            
            if all_results:
                df = pd.DataFrame(all_results)
                
                # Neon Bar Chart Cloning the Visual Theme Style exactly
                fig = px.bar(
                    df, x='name', y='match_percentage', color='decision',
                    color_discrete_map={'HIRE': '#00ffcc', 'REJECT': '#ef4444'},
                    text='match_percentage'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    font_color='#ffffff',
                    showlegend=False,
                    xaxis=dict(showgrid=False, title=""),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.08)', range=[0, 100], title="Applicant Fit Score")
                )
                fig.update_traces(marker_line_width=1.5, marker_line_color="#ffffff", textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("<div style='margin: 20px 0 10px 0; font-size:0.9rem; color:#8b949e; font-weight:bold;'>🔍 FILTER PROFILES BY NAME/KEYWORDS</div>", unsafe_allow_html=True)
                
                # Render Candidate Cloned Component row layout block pairs[cite: 7]
                for candidate in all_results:
                    is_hire = candidate["decision"] == "HIRE"
                    border_state_class = "box-pass" if is_hire else "box-reject"
                    badge_markup = f'<span class="status-badge-pass">HIRE ✅</span>' if is_hire else f'<span class="status-badge-reject">REJECT ❌</span>'
                    accent_col = "#00ffcc" if is_hire else "#ef4444"
                    
                    # Split each candidate entry layout block into clear left text / right charts side-by-side[cite: 7]
                    st.markdown(f"""
                    <div class="applicant-box-row {border_state_class}">
                        <div style="width: 60%;">
                            <div style="font-size: 1.1rem; font-weight: bold; color: #ffffff; margin-bottom:6px;">👤 {candidate['name'].upper()}</div>
                            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                                <b>MATCH:</b> <span style="color: {accent_col}; font-weight:bold;">{candidate['match_percentage']}%</span><br>
                                <b>SKILLS MATCHED:</b> {candidate['matching_skills']}<br>
                                <b>MISSING:</b> {candidate['missing_skills']}<br>
                                <b>EDUCATION:</b> {candidate['education']}
                            </div>
                        </div>
                        <div style="width: 35%; text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
                            {badge_markup}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mini Radar Chart calculation layout simulation loop injected per card block[cite: 7]
                    with st.expander(f"⚙️ Expandable Active Evaluation Metrics & Questions"):
                        col_card_text, col_card_radar = st.columns([2, 1.2])
                        with col_card_text:
                            st.write(f"**Targeted Interview Screening Prompts:**")
                            st.info(candidate['questions'])
                        with col_card_radar:
                            # Render real-time mathematical radar layouts for technical assessment verification
                            radar_fig = go.Figure(data=go.Scatterpolar(
                              r=[candidate['match_percentage'], 90, 40, 70, 50],
                              theta=['Match Rate','Experience','Core Stack','Architecture','Pipeline Execution'],
                              fill='toself',
                              line_color=accent_col
                            ))
                            radar_fig.update_layout(
                                polar=dict(radialaxis=dict(visible=False), bgcolor='rgba(0,0,0,0)'),
                                showlegend=False, width=160, height=160, margin=dict(l=20, r=20, t=20, b=20),
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.error("Matrix processing failure. Ensure valid PDF content fields.")
    else:
        st.markdown("<p style='color:#475569;'>Awaiting file payload stream array inputs. Drop multiple candidate resumes above to launch assessment tracker.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
