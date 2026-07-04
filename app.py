import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from utils import extract_text_from_pdf, analyze_resume

# 1. Page Configuration
st.set_page_config(
    page_title="Resume Matcher // AI Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

ACCENT = "#7C5CFF"      # violet — brand / AI identity
ACCENT_2 = "#00D9A3"    # teal — success / match
DANGER = "#FF4D6A"      # coral-red — reject / missing
BG = "#0A0E17"
PANEL = "#111726"
BORDER = "#232B3D"
TEXT = "#E7EAF3"
TEXT_MUTED = "#7C8698"

# --- FUTURISTIC CORE CSS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap');

    .stApp {{
        background:
            radial-gradient(circle at 15% 0%, rgba(124,92,255,0.08), transparent 40%),
            radial-gradient(circle at 85% 100%, rgba(0,217,163,0.06), transparent 40%),
            {BG};
        color: {TEXT};
        font-family: 'Inter', sans-serif;
    }}

    section[data-testid="stSidebar"] {{
        background: {PANEL};
        border-right: 1px solid {BORDER};
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] > div {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 14px;
    }}

    .engine-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.75rem;
    }}
    .engine-title {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.9rem;
        letter-spacing: 0.5px;
        margin: 0;
        background: linear-gradient(90deg, {ACCENT}, {ACCENT_2});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .engine-subtitle {{
        color: {TEXT_MUTED};
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 2px;
    }}
    .pulse-wrap {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: {ACCENT_2};
    }}
    .pulse-dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {ACCENT_2};
        box-shadow: 0 0 8px {ACCENT_2};
        animation: pulse 1.6s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.35; transform: scale(0.75); }}
    }}

    .section-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        color: {ACCENT};
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }}

    textarea, .stTextArea textarea {{
        background: {BG} !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT} !important;
        border-radius: 10px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }}
    textarea:focus {{
        border: 1px solid {ACCENT} !important;
        box-shadow: 0 0 0 3px rgba(124,92,255,0.15) !important;
    }}

    div[data-testid="stFileUploaderDropzone"] {{
        background: {BG} !important;
        border: 1px dashed {BORDER} !important;
        border-radius: 10px !important;
    }}

    .stButton>button {{
        background: linear-gradient(90deg, {ACCENT}, #5B3FE0) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        border-radius: 10px !important;
        padding: 0.6rem 0 !important;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        box-shadow: 0 0 20px rgba(124,92,255,0.45) !important;
        transform: translateY(-1px);
    }}

    .tag {{
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        padding: 3px 10px;
        border-radius: 6px;
        margin: 2px 4px 2px 0;
    }}
    .tag-match {{ background: rgba(0,217,163,0.12); color: {ACCENT_2}; border: 1px solid rgba(0,217,163,0.3); }}
    .tag-missing {{ background: rgba(255,77,106,0.12); color: {DANGER}; border: 1px solid rgba(255,77,106,0.3); }}

    .mono-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: {TEXT_MUTED};
        text-transform: lowercase;
        letter-spacing: 0.5px;
    }}

    .status-pill {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 6px;
        letter-spacing: 1px;
    }}
    .status-hire {{ background: rgba(0,217,163,0.12); color: {ACCENT_2}; border: 1px solid rgba(0,217,163,0.35); }}
    .status-reject {{ background: rgba(255,77,106,0.12); color: {DANGER}; border: 1px solid rgba(255,77,106,0.35); }}

    .rank-card {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        background: {PANEL};
    }}
</style>
""", unsafe_allow_html=True)


def score_ring_html(score: int, color: str) -> str:
    """Renders an animated SVG match-score ring."""
    circumference = 264
    return f"""
    <div style="display:flex; align-items:center; justify-content:center; padding: 6px 0;">
      <div style="position:relative; width:150px; height:150px;">
        <svg width="150" height="150" viewBox="0 0 96 96" style="transform:rotate(-90deg);">
          <circle cx="48" cy="48" r="42" fill="none" stroke="{BORDER}" stroke-width="7"></circle>
          <circle id="ring" cx="48" cy="48" r="42" fill="none" stroke="{color}"
            stroke-width="7" stroke-linecap="round"
            stroke-dasharray="{circumference}" stroke-dashoffset="{circumference}"
            style="filter: drop-shadow(0 0 6px {color});"></circle>
        </svg>
        <div style="position:absolute; inset:0; display:flex; flex-direction:column;
                    align-items:center; justify-content:center; font-family:'JetBrains Mono',monospace;">
          <span id="num" style="font-size:26px; font-weight:700; color:{TEXT};">0</span>
          <span style="font-size:10px; color:{TEXT_MUTED};">match</span>
        </div>
      </div>
    </div>
    <script>
      const target = {score};
      const circumference = {circumference};
      const ring = document.getElementById('ring');
      const num = document.getElementById('num');
      let i = 0;
      const steps = 40;
      const timer = setInterval(() => {{
        i++;
        let current = Math.min(target, Math.round((target / steps) * i));
        num.textContent = current;
        ring.setAttribute('stroke-dashoffset', circumference - (circumference * current / 100));
        if (i >= steps) clearInterval(timer);
      }}, 20);
    </script>
    """


def render_skill_tags(skills_str, tag_class):
    if not skills_str:
        st.markdown("<span class='mono-label'>none identified</span>", unsafe_allow_html=True)
        return
    tags = "".join(f"<span class='tag {tag_class}'>{s.strip()}</span>" for s in skills_str.split(",") if s.strip())
    st.markdown(tags, unsafe_allow_html=True)


def render_candidate_detail(results, threshold):
    passed = results["match_percentage"] >= threshold
    ring_color = ACCENT_2 if passed else DANGER

    top_l, top_r = st.columns([1, 1.3])
    with top_l:
        components.html(score_ring_html(results["match_percentage"], ring_color), height=170)

    with top_r:
        st.markdown(f"<p style='font-size:1.1rem; font-weight:600; margin-bottom:2px;'>{results['name']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='mono-label' style='margin-bottom:10px;'>{results['education']}</p>", unsafe_allow_html=True)
        pill_class = "status-hire" if passed else "status-reject"
        pill_text = "HIRE — passed threshold" if passed else "REJECT — below threshold"
        st.markdown(f"<span class='status-pill {pill_class}'>{pill_text}</span>", unsafe_allow_html=True)

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    skill_l, skill_r = st.columns(2)
    with skill_l:
        st.markdown("<p class='mono-label'>matching_skills</p>", unsafe_allow_html=True)
        render_skill_tags(results["matching_skills"], "tag-match")
    with skill_r:
        st.markdown("<p class='mono-label'>missing_skills</p>", unsafe_allow_html=True)
        render_skill_tags(results["missing_skills"], "tag-missing")

    st.markdown(f"<div style='height:18px; border-top:1px solid {BORDER}; margin-top:14px;'></div>", unsafe_allow_html=True)
    st.markdown("<p class='mono-label' style='margin-top:14px;'>generated_questions</p>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-family:\"JetBrains Mono\",monospace; font-size:0.85rem; color:{TEXT_MUTED}; line-height:1.8; white-space:pre-line;'>{results['questions']}</p>",
        unsafe_allow_html=True
    )


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<p class='section-label'>Sidebar control</p>", unsafe_allow_html=True)
    match_threshold = st.slider("Match threshold", min_value=0, max_value=100, value=60, step=5)
    st.markdown("---")
    st.markdown(
        "<div class='pulse-wrap'><span class='pulse-dot'></span>cluster connected</div>",
        unsafe_allow_html=True
    )

# --- HEADER ---
st.markdown(f"""
<div class="engine-header">
  <div>
    <p class="engine-title">◈ Resume matcher</p>
    <p class="engine-subtitle">multi-agent AI pipeline // huggingface inference</p>
  </div>
  <div class="pulse-wrap"><span class="pulse-dot"></span>engine online</div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("<p class='section-label'>Job parameters</p>", unsafe_allow_html=True)
    job_description = st.text_area(
        "Job description",
        height=200,
        placeholder="Paste the role's requirements and key skills",
        label_visibility="collapsed"
    )

    st.markdown("<p class='section-label'>Resume upload</p>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Resumes",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        st.markdown(
            f"<p class='mono-label'>{len(uploaded_files)} file(s) queued</p>",
            unsafe_allow_html=True
        )

    execute_scan = st.button("Run scan", use_container_width=True)

with col_right:
    st.markdown("<p class='section-label'>Match results</p>", unsafe_allow_html=True)

    if execute_scan and job_description and uploaded_files:
        results_list = []
        with st.spinner(f"Running multi-agent analysis on {len(uploaded_files)} resume(s)..."):
            for f in uploaded_files:
                resume_text = extract_text_from_pdf(f)
                if resume_text.strip():
                    result = analyze_resume(resume_text, job_description)
                    result["filename"] = f.name
                    results_list.append(result)
                else:
                    st.warning(f"Couldn't extract text from **{f.name}**. Skipped.")

        if not results_list:
            st.error("No resumes could be processed. Check the uploaded files.")
        elif len(results_list) == 1:
            render_candidate_detail(results_list[0], match_threshold)
        else:
            results_list.sort(key=lambda r: r["match_percentage"], reverse=True)

            fig = go.Figure(go.Bar(
                x=[r["match_percentage"] for r in results_list],
                y=[r["name"] for r in results_list],
                orientation="h",
                marker_color=[ACCENT_2 if r["match_percentage"] >= match_threshold else DANGER for r in results_list],
                text=[f"{r['match_percentage']}%" for r in results_list],
                textposition="auto"
            ))
            fig.update_layout(
                plot_bgcolor=PANEL, paper_bgcolor=PANEL,
                font_color=TEXT, font_family="JetBrains Mono",
                margin=dict(l=10, r=10, t=10, b=10),
                height=max(180, 60 * len(results_list)),
                xaxis=dict(range=[0, 100], gridcolor=BORDER),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            for r in results_list:
                passed = r["match_percentage"] >= match_threshold
                pill_class = "status-hire" if passed else "status-reject"
                pill_text = "HIRE" if passed else "REJECT"
                st.markdown(f"""
                <div class="rank-card">
                  <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div>
                      <p style="font-weight:600; font-size:14px; margin:0;">{r['name']}</p>
                      <p class="mono-label" style="margin-top:2px;">{r['filename']}</p>
                    </div>
                    <div style="display:flex; align-items:center; gap:10px;">
                      <span style="font-family:'JetBrains Mono',monospace; font-size:15px; font-weight:700;">{r['match_percentage']}%</span>
                      <span class="status-pill {pill_class}">{pill_text}</span>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander(f"View details — {r['name']}"):
                    render_candidate_detail(r, match_threshold)
    else:
        placeholder_fig = go.Figure()
        placeholder_fig.add_annotation(
            text="awaiting scan input",
            font=dict(family="JetBrains Mono, monospace", size=14, color=TEXT_MUTED),
            showarrow=False
        )
        placeholder_fig.update_layout(
            plot_bgcolor=PANEL, paper_bgcolor=PANEL,
            height=260, margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(visible=False), yaxis=dict(visible=False)
        )
        st.plotly_chart(placeholder_fig, use_container_width=True)
        st.markdown("<p class='mono-label'>populate job parameters and upload one or more resumes to run the scan</p>", unsafe_allow_html=True)
