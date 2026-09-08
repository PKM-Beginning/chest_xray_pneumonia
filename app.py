import ast
import os
import re
import subprocess
import tempfile

import streamlit as st

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Chest X-Ray Pneumonia Detection",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Design tokens / global styling
# --------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root{
    --bg-0:#080b12;
    --bg-1:#0d1420;
    --panel: rgba(255,255,255,0.035);
    --panel-border: rgba(255,255,255,0.09);
    --panel-border-soft: rgba(255,255,255,0.06);
    --text-hi:#eef1f7;
    --text-mid:#aab2c5;
    --text-low:#707a91;
    --brand:#7c93ff;
    --brand-soft: rgba(124,147,255,0.14);
    --teal:#2fd6ae;
    --teal-soft: rgba(47,214,174,0.14);
    --rose:#fb7189;
    --rose-soft: rgba(251,113,137,0.14);
    --amber:#f4b860;
}

html, body, [class*="css"]{
    font-family: 'Inter', -apple-system, sans-serif;
}

.stApp{
    background:
        radial-gradient(circle at 12% 8%, rgba(124,147,255,0.10), transparent 42%),
        radial-gradient(circle at 88% 4%, rgba(47,214,174,0.08), transparent 40%),
        radial-gradient(circle at 50% 100%, rgba(124,147,255,0.06), transparent 55%),
        var(--bg-0);
    color: var(--text-hi);
}

#MainMenu, footer, header {visibility: hidden;}

.block-container{
    padding-top: 2.2rem;
    max-width: 1180px;
}

h1, h2, h3, h4 { font-family: 'Space Grotesk', 'Inter', sans-serif; letter-spacing: -0.01em; }

hr{ border-color: var(--panel-border-soft) !important; margin: 2.2rem 0 !important; }

/* ---- hero ---- */
.hero-eyebrow{
    display:inline-flex; align-items:center; gap:.5rem;
    color: var(--brand); font-size:0.82rem; font-weight:600;
    background: var(--brand-soft); border:1px solid rgba(124,147,255,0.25);
    padding: 0.3rem 0.75rem; border-radius: 100px; margin-bottom: 1rem;
}
.hero-title{
    font-size: 2.5rem; font-weight: 700; line-height:1.15; color: var(--text-hi); margin:0 0 .6rem 0;
}
.hero-sub{
    font-size: 1.02rem; color: var(--text-mid); max-width: 640px; line-height:1.55; margin-bottom: 1.4rem;
}

/* ---- glass panel ---- */
.panel{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 18px;
    padding: 1.5rem 1.6rem;
    backdrop-filter: blur(18px);
}
.panel-tight{ padding: 1.1rem 1.3rem; }

.section-label{
    color: var(--text-low); font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.02em; margin-bottom: 0.35rem;
}
.section-title{
    font-size: 1.35rem; font-weight: 700; color: var(--text-hi); margin: 0 0 1.1rem 0;
}

/* ---- disclaimer banner ---- */
.disclaimer{
    display:flex; gap:.7rem; align-items:flex-start;
    background: var(--amber); background: rgba(244,184,96,0.09);
    border: 1px solid rgba(244,184,96,0.28);
    border-radius: 14px; padding: 0.85rem 1.1rem; margin-bottom: 2rem;
    color: #f1d3a3; font-size: 0.88rem; line-height:1.5;
}

/* ---- stat cards ---- */
.stat-card{
    background: var(--panel); border:1px solid var(--panel-border); border-radius:16px;
    padding: 1.25rem 1.3rem; height: 100%;
}
.stat-value{ font-family:'Space Grotesk',sans-serif; font-size: 2rem; font-weight:700; color: var(--text-hi); }
.stat-label{ color: var(--text-mid); font-size: 0.85rem; margin-top:.15rem; }
.stat-bar-track{ height:5px; border-radius:4px; background: rgba(255,255,255,0.08); margin-top:.85rem; overflow:hidden; }
.stat-bar-fill{ height:100%; border-radius:4px; }

/* ---- model info chips ---- */
.chip-row{ display:flex; flex-wrap:wrap; gap:.55rem; margin-top:.9rem; }
.chip{
    background: rgba(255,255,255,0.05); border:1px solid var(--panel-border-soft);
    color: var(--text-mid); font-size:0.82rem; padding: 0.32rem 0.7rem; border-radius:100px;
}

/* ---- upload dropzone ---- */
[data-testid="stFileUploaderDropzone"]{
    background: var(--panel) !important;
    border: 1.5px dashed rgba(124,147,255,0.35) !important;
    border-radius: 16px !important;
}
[data-testid="stFileUploaderDropzone"] button{
    background: var(--brand) !important; color:#08101f !important; border:none !important; font-weight:600 !important;
}

/* ---- status badge ---- */
.status-badge{
    display:inline-flex; align-items:center; gap:.5rem;
    font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700;
    padding: .6rem 1.1rem; border-radius: 14px; margin-bottom: 1rem;
}
.status-normal{ background: var(--teal-soft); color: var(--teal); border:1px solid rgba(47,214,174,0.35); }
.status-pneumonia{ background: var(--rose-soft); color: var(--rose); border:1px solid rgba(251,113,137,0.35); }
.status-dot{ width:10px; height:10px; border-radius:50%; background: currentColor; }

/* ---- confidence ---- */
.conf-label{ display:flex; justify-content:space-between; color:var(--text-mid); font-size:0.85rem; margin-bottom:.35rem; }
.conf-track{ height:10px; border-radius:6px; background: rgba(255,255,255,0.07); overflow:hidden; }
.conf-fill{ height:100%; border-radius:6px; }

/* ---- probability rows ---- */
.prob-row{ margin-bottom: .85rem; }
.prob-row .conf-label{ font-size:0.86rem; color: var(--text-hi); }
.prob-track{ height:8px; border-radius:5px; background: rgba(255,255,255,0.07); overflow:hidden; }
.prob-fill{ height:100%; border-radius:5px; }

/* how-it-works */
.step-item{ display:flex; gap:.8rem; margin-bottom:1rem; align-items:flex-start; }
.step-num{
    flex:0 0 auto; width:24px; height:24px; border-radius:50%;
    background: var(--brand-soft); color: var(--brand); font-size:0.78rem; font-weight:700;
    display:flex; align-items:center; justify-content:center; margin-top:1px;
}
.step-text{ color: var(--text-mid); font-size:0.87rem; line-height:1.45; }

[data-testid="stMetric"]{ background: transparent; }
.stTabs [data-baseweb="tab-list"]{ gap: 4px; }

.footer-note{ text-align:center; color: var(--text-low); font-size:0.8rem; margin-top: 2.5rem; padding-bottom: 1rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def status_color(cls_name: str) -> str:
    return "var(--rose)" if cls_name.upper() == "PNEUMONIA" else "var(--teal)"


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🩺 Model")
    st.markdown(
        """
        <div class="panel panel-tight">
            <div class="chip-row" style="margin-top:0;">
                <span class="chip">ResNet18</span>
                <span class="chip">Transfer learning</span>
                <span class="chip">Grad-CAM</span>
            </div>
            <div style="margin-top:1rem; color:var(--text-mid); font-size:0.85rem; line-height:1.6;">
                Binary classifier distinguishing <b style="color:var(--teal)">NORMAL</b> and
                <b style="color:var(--rose)">PNEUMONIA</b> chest X-rays, with Grad-CAM
                heatmaps for visual interpretability.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    st.markdown("### How it works")
    st.markdown(
        """
        <div class="panel panel-tight">
            <div class="step-item">
                <div class="step-num">1</div>
                <div class="step-text">Upload a chest X-ray image (JPG or PNG).</div>
            </div>
            <div class="step-item">
                <div class="step-num">2</div>
                <div class="step-text">The ResNet18 model runs inference on the image.</div>
            </div>
            <div class="step-item" style="margin-bottom:0;">
                <div class="step-num">3</div>
                <div class="step-text">View the prediction, confidence, and Grad-CAM explanation.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-eyebrow">● Machine learning portfolio demo</div>
    <div class="hero-title">Chest X-Ray Pneumonia Detection</div>
    <div class="hero-sub">
        A ResNet18 model fine-tuned to classify chest X-rays as normal or
        pneumonia, paired with Grad-CAM so you can see exactly which regions
        of the image drove each prediction.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer">
        <div>⚠️</div>
        <div><b style="color:#f7dfb3;">Research and educational demo only.</b>
        This model is not a certified medical device and must not be used
        for clinical diagnosis or treatment decisions.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Model overview + evaluation metrics
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">MODEL OVERVIEW</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Evaluated on a held-out test set</div>', unsafe_allow_html=True)

metrics = [
    ("Test Accuracy", "83.17%", 83.17, "var(--brand)"),
    ("ROC-AUC", "95.97%", 95.97, "var(--teal)"),
    ("Pneumonia Recall", "99.74%", 99.74, "var(--rose)"),
]

m_cols = st.columns(3)
for col, (label, value, pct, color) in zip(m_cols, metrics):
    with col:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
                <div class="stat-bar-track">
                    <div class="stat-bar-fill" style="width:{pct}%; background:{color};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="panel panel-tight" style="margin-top:1.2rem;">
        <div class="chip-row" style="margin-top:0;">
            <span class="chip">Architecture · ResNet18</span>
            <span class="chip">Task · Binary classification</span>
            <span class="chip">Classes · NORMAL / PNEUMONIA</span>
            <span class="chip">Explainability · Grad-CAM</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<hr/>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">STEP 1</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Upload a chest X-ray</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload a chest X-ray image",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed",
)

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
    ) as tmp:
        tmp.write(uploaded_file.getbuffer())
        image_path = tmp.name

    output_path = "streamlit_gradcam.png"
    command = [
        "python", "predict.py",
        "--image", image_path,
        "--checkpoint", "best_model.pt",
        "--gradcam",
        "--out", output_path,
    ]

    with st.spinner("Analyzing X-ray..."):
        result = subprocess.run(command, capture_output=True, text=True)

    output = result.stdout + "\n" + result.stderr

    st.markdown("<hr/>", unsafe_allow_html=True)

    if result.returncode != 0:
        st.markdown('<div class="section-label">RESULT</div>', unsafe_allow_html=True)
        st.error("Prediction failed. See technical details below.")
        with st.expander("Technical error"):
            st.code(output)
    else:
        prediction_match = re.search(r"Prediction:\s*(NORMAL|PNEUMONIA)", output, re.IGNORECASE)
        confidence_match = re.search(r"Confidence:\s*([0-9.]+)", output)
        probabilities_match = re.search(r"Class probabilities:\s*(.*)", output)

        prediction = prediction_match.group(1).upper() if prediction_match else "UNKNOWN"
        confidence = float(confidence_match.group(1)) if confidence_match else None

        probs_dict = None
        if probabilities_match:
            try:
                probs_dict = ast.literal_eval(probabilities_match.group(1).strip())
            except (ValueError, SyntaxError):
                probs_dict = None

        st.markdown('<div class="section-label">STEP 2</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Prediction result</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.image(uploaded_file, caption="Uploaded X-ray", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            badge_class = "status-pneumonia" if prediction == "PNEUMONIA" else "status-normal"
            badge_icon = "🔴" if prediction == "PNEUMONIA" else "🟢"

            conf_html = ""
            if confidence is not None:
                pct = confidence * 100
                color = status_color(prediction)
                conf_html = f"""
                <div style="margin-top:1.1rem;">
                    <div class="conf-label"><span>Confidence</span><span style="color:var(--text-hi); font-weight:600;">{pct:.2f}%</span></div>
                    <div class="conf-track"><div class="conf-fill" style="width:{pct}%; background:{color};"></div></div>
                </div>
                """

            prob_rows = ""
            if probs_dict:
                for cls_name, p in probs_dict.items():
                    p_pct = float(p) * 100
                    color = status_color(cls_name)
                    prob_rows += f"""
                    <div class="prob-row">
                        <div class="conf-label"><span>{cls_name}</span><span>{p_pct:.2f}%</span></div>
                        <div class="prob-track"><div class="prob-fill" style="width:{p_pct}%; background:{color};"></div></div>
                    </div>
                    """

            st.markdown(
                f"""
                <div class="panel">
                    <div class="status-badge {badge_class}">
                        <span class="status-dot"></span>{badge_icon} {prediction}
                    </div>
                    {conf_html}
                    <div style="margin-top:1.4rem;">
                        <div class="section-label" style="margin-bottom:.6rem;">CLASS PROBABILITIES</div>
                        {prob_rows if prob_rows else '<div style="color:var(--text-low); font-size:0.85rem;">Probability breakdown unavailable.</div>'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown("<hr/>", unsafe_allow_html=True)

        # ------------------------------------------------------------
        # Grad-CAM
        # ------------------------------------------------------------
        st.markdown('<div class="section-label">STEP 3</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Grad-CAM explainability</div>', unsafe_allow_html=True)

        if os.path.exists(output_path):
            gc_col1, gc_col2 = st.columns([1, 1], gap="large")
            with gc_col1:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.image(uploaded_file, caption="Original X-ray", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with gc_col2:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.image(
                    output_path,
                    caption="Grad-CAM: regions that most influenced the prediction",
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                """
                <div class="panel panel-tight" style="margin-top:1rem; color:var(--text-mid); font-size:0.87rem; line-height:1.55;">
                    ℹ️ Grad-CAM is an interpretability visualization. Highlighted regions
                    indicate areas that influenced the model's prediction; they do not
                    constitute clinical evidence of pathology.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning("Grad-CAM output image was not generated.")

        with st.expander("Raw model output"):
            st.code(output)

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="footer-note">
        Built with PyTorch, ResNet18, Grad-CAM, and Streamlit ·
        For research and educational purposes only
    </div>
    """,
    unsafe_allow_html=True,
)
