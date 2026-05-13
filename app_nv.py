import streamlit as st
import pickle, json, pandas as pd, os, datetime
import matplotlib.pyplot as plt
import html

# UI: Page config must be the first Streamlit command — wide layout and app branding for a clinical dashboard feel.
st.set_page_config(
    page_title="Clinical Disease Intelligence",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_clinical_ui_styles():
    # UI: Lightweight global CSS — typography, spacing, sidebar, cards, and primary actions (no logic impact).
    st.markdown(
        """
<style>
  html, body, [class*="css"]  { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .block-container { padding-top: 1.25rem; padding-bottom: 3rem; max-width: 1200px; }
  [data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(180deg, #f4f7fb 0%, #eef3f9 45%, #e8eef6 100%);
  }
  [data-testid="stSidebar"] {
    background: linear-gradient(195deg, #0f2744 0%, #153a5c 55%, #1a4a6e 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
  }
  [data-testid="stSidebar"] * { color: #e8f1ff !important; }
  [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p { color: #dbeafe !important; opacity: 0.95; }
  [data-testid="stSidebar"] .stRadio label { font-weight: 500; }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12); }
  [data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #22d3ee, #38bdf8) !important;
    color: #0b1e33 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 0.75rem !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover { filter: brightness(1.05); }
  .clinical-hero {
    background: linear-gradient(135deg, #0b3a5c 0%, #0d4f6e 40%, #0f766e 100%);
    color: #f0fdfc;
    padding: 1.35rem 1.5rem 1.25rem;
    border-radius: 14px;
    margin-bottom: 1.25rem;
    box-shadow: 0 12px 40px rgba(11, 58, 92, 0.22);
    border: 1px solid rgba(255,255,255,0.12);
  }
  .clinical-hero h1 { margin: 0 0 0.35rem 0; font-size: 1.65rem; font-weight: 700; letter-spacing: -0.02em; }
  .clinical-hero p { margin: 0; opacity: 0.92; font-size: 0.98rem; }
  .clinical-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 1rem 1.15rem 1.05rem;
    margin: 0 0 1rem 0;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
    border-left: 4px solid #0d9488;
  }
  .clinical-card h3 { margin: 0 0 0.5rem 0; font-size: 1.15rem; color: #0f172a; }
  .clinical-muted { color: #64748b; font-size: 0.88rem; margin-bottom: 0.35rem; }
  .clinical-badge {
    display: inline-block;
    background: #ecfdf5;
    color: #047857;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
    letter-spacing: 0.02em;
  }
  .clinical-section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0 0 0.65rem 0;
    display: flex;
    align-items: center;
    gap: 0.45rem;
  }
  div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #e2e8f0; }
  /* UI: Chatbot — thread and bubbles only (distinct user vs assistant surfaces). */
  .chatbot-thread {
    max-width: 720px;
    margin-top: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .chat-row-user { align-self: flex-end; max-width: min(85%, 100%); }
  .chat-row-bot { align-self: flex-start; max-width: min(92%, 100%); }
  .chat-bubble {
    border-radius: 14px;
    padding: 0.8rem 1rem 1rem;
    line-height: 1.55;
    box-shadow: 0 2px 14px rgba(15, 23, 42, 0.07);
  }
  .chat-bubble-user {
    background: linear-gradient(160deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #93c5fd;
    color: #0f172a;
  }
  .chat-bubble-bot {
    background: linear-gradient(165deg, #ecfdf5 0%, #d1fae5 35%, #f8fafc 100%);
    border: 1px solid #6ee7b7;
    border-left: 4px solid #059669;
    color: #064e3b;
  }
  .chat-meta {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.4rem;
    display: block;
  }
  .chat-bubble-user .chat-meta { color: #1d4ed8; }
  .chat-bubble-bot .chat-meta { color: #047857; }
  .chat-body { font-size: 0.97rem; margin: 0; word-wrap: break-word; }
  .chat-bubble-user .chat-body { color: #1e293b; }
  .chat-bubble-bot .chat-body { color: #14532d; }
  /* Report Analyzer: metric cards (isolated from disease prediction UI). */
  .report-finding-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 0.95rem 1.1rem;
    margin-bottom: 0.75rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
    border-left: 4px solid #64748b;
  }
  .report-finding-card.report-st-normal { border-left-color: #059669; }
  .report-finding-card.report-st-high { border-left-color: #dc2626; }
  .report-finding-card.report-st-low { border-left-color: #d97706; }
  .report-finding-card.report-st-unknown { border-left-color: #64748b; }
  .report-finding-card h4 { margin: 0 0 0.25rem 0; font-size: 0.95rem; color: #475569; font-weight: 600; }
  .report-finding-card .report-val { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0.15rem 0; }
  .report-finding-card .report-pill {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .report-pill-normal { background: #d1fae5; color: #065f46; }
  .report-pill-high { background: #fee2e2; color: #991b1b; }
  .report-pill-low { background: #ffedd5; color: #9a3412; }
  .report-pill-unknown { background: #f1f5f9; color: #475569; }
  .report-summary-box {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.15rem;
    margin-top: 0.5rem;
  }
</style>
""",
        unsafe_allow_html=True,
    )


_inject_clinical_ui_styles()


def _render_report_analyzer_page():
    # Report Analyzer: UI + orchestration only — disease ML / auth / chatbot untouched.
    try:
        import report_analyzer_helpers as ra
    except ImportError:
        st.error(
            "Report Analyzer optional dependencies are missing. Install them, then restart the app."
        )
        st.code("pip install pdfplumber PyPDF2 pytesseract Pillow", language="bash")
        return

    st.markdown(
        '<p class="clinical-section-title">📄 Medical Report Analyzer</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Upload a lab PDF/image or paste text. Values are parsed with heuristics and compared to "
        "demo reference bands — not a medical device; confirm all results with your clinician."
    )

    uploaded = st.file_uploader(
        "Upload report (PDF, JPG, PNG, or TXT)",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        help="Maximum 15 MB. Files stay in memory for this session only.",
    )
    pasted = st.text_area(
        "Or paste report text",
        height=140,
        placeholder="Optional — same analysis as a .txt upload.",
        key="report_analyzer_paste",
    )

    if st.button("Analyze report", type="primary", use_container_width=True, key="report_analyzer_btn"):
        if uploaded is not None:
            data = uploaded.getvalue()
            filename = uploaded.name or "report"
            mime = uploaded.type or "application/octet-stream"
        elif pasted and pasted.strip():
            data = pasted.strip().encode("utf-8")
            filename = "pasted_report.txt"
            mime = "text/plain"
        else:
            st.warning("Please upload a file or paste report text.")
            return

        prog = st.progress(0)
        with st.spinner("Analyzing report - extracting text and parsing values..."):
            verr = ra.validate_upload_bytes(data)
            if verr:
                prog.empty()
                st.error(verr)
                return

            prog.progress(25)
            text, xerr = ra.run_extraction(data, mime, filename)
            prog.progress(55)
            if not text or not text.strip():
                prog.empty()
                st.error(xerr or "No text could be extracted. Try another file format or a clearer scan.")
                return
            if xerr:
                if xerr.startswith("Used "):
                    st.info(xerr)
                else:
                    st.warning(xerr)

            findings = ra.parse_lab_findings(text)
            summary = ra.build_health_summary(findings)
            prog.progress(90)
        prog.progress(100)
        prog.empty()

        with st.expander("Extracted text preview (truncated)", expanded=False):
            st.text(text[:12000] + ("..." if len(text) > 12000 else ""))

        st.markdown("##### Lab parameters")
        if not findings:
            st.info("No supported parameters detected. Check spelling, units, or try OCR on a sharper image.")
        else:
            ncols = 3
            rows = (len(findings) + ncols - 1) // ncols
            idx = 0
            for _r in range(rows):
                cols = st.columns(ncols)
                for c in range(ncols):
                    if idx >= len(findings):
                        break
                    f = findings[idx]
                    idx += 1
                    st_cl = {
                        "Normal": "normal",
                        "High": "inverse",
                        "Low": "off",
                        "Unknown": "off",
                    }.get(f.status, "off")
                    with cols[c]:
                        st.metric(f.label, f.value_display, delta=f.status, delta_color=st_cl)
                        st.caption(f.note)

            st.markdown("##### Dashboard view")
            for f in findings:
                pill = {
                    "Normal": "report-pill-normal",
                    "High": "report-pill-high",
                    "Low": "report-pill-low",
                    "Unknown": "report-pill-unknown",
                }.get(f.status, "report-pill-unknown")
                st_class = {
                    "Normal": "report-st-normal",
                    "High": "report-st-high",
                    "Low": "report-st-low",
                    "Unknown": "report-st-unknown",
                }.get(f.status, "report-st-unknown")
                st.markdown(
                    f"""
<div class="report-finding-card {st_class}">
  <h4>{html.escape(f.label)}</h4>
  <div class="report-val">{html.escape(f.value_display)}</div>
  <span class="report-pill {pill}">{html.escape(f.status)}</span>
  <p class="clinical-muted" style="margin-top:0.5rem;margin-bottom:0;">{html.escape(f.note)}</p>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.markdown("##### Health summary (plain language)")
        st.markdown(
            f'<div class="report-summary-box"><p style="margin:0;line-height:1.55;color:#334155;">{html.escape(summary)}</p></div>',
            unsafe_allow_html=True,
        )


# ================= LOAD MODEL =================
model = pickle.load(open("model_nb.pkl", "rb"))
le = pickle.load(open("label_encoder_nb.pkl", "rb"))
columns = json.load(open("columns_nb.json", "r"))

desc_dict = pickle.load(open("desc_nb.pkl", "rb"))
prec_dict = pickle.load(open("prec_nb.pkl", "rb"))

col_index = {col: i for i, col in enumerate(columns)}


def _load_json_dict(path):
    """Load JSON object from path; tolerate missing, empty, or invalid files (returns {})."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        stripped = raw.strip()
        if not stripped:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return {}
        data = json.loads(stripped)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, TypeError):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}


# ================= FILE INIT =================
for file in ["users.json", "history.json"]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump({}, f)

users = _load_json_dict("users.json")
history = _load_json_dict("history.json")

# ================= SESSION =================
if "user" not in st.session_state:
    st.session_state.user = None

# ================= SIDEBAR LOGIN =================
# UI: Sidebar header and subtle structure for a secure clinical workspace entry.
st.sidebar.markdown("### 🔐 Account")
st.sidebar.caption("Secure access · same login flow as before")
st.sidebar.divider()

menu = st.sidebar.radio("Menu", ["Login", "Signup"])

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if menu == "Signup":
    if st.sidebar.button("Create Account"):
        if username in users:
            st.sidebar.error("User exists")
        else:
            users[username] = password
            json.dump(users, open("users.json", "w"))
            st.sidebar.success("Account created")

if menu == "Login":
    if st.sidebar.button("Login"):
        if username in users and users[username] == password:
            st.session_state.user = username
            st.sidebar.success(f"Welcome {username}")
        else:
            st.sidebar.error("Invalid login")

if st.session_state.user:
    st.sidebar.divider()
    st.sidebar.success(f"Logged in as {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# UI: Main hero — headings and hierarchy only; no change to auth or routing.
st.markdown(
    """
<div class="clinical-hero">
  <h1>🩺 AI Disease Prediction System</h1>
  <p>Evidence-style triage view · symptom mapping · specialist routing (demo)</p>
</div>
""",
    unsafe_allow_html=True,
)

if st.session_state.user:

    page = st.sidebar.selectbox(
        "Navigation",
        ["Prediction", "History", "Chatbot", "Hospitals", "Report Analyzer"],
    )

    # ================= PREDICTION =================
    if page == "Prediction":

        # UI: Two-column layout on wide screens — inputs left, guidance right (inputs unchanged).
        col_symptoms, col_guide = st.columns([1.35, 1], gap="large")
        with col_symptoms:
            st.markdown('<p class="clinical-section-title">🔍 Select Symptoms</p>', unsafe_allow_html=True)
            selected = st.multiselect("Symptoms", columns)
        with col_guide:
            st.markdown('<p class="clinical-section-title">ℹ️ How to use</p>', unsafe_allow_html=True)
            st.info(
                "Choose all that apply from the list. Predictions rank the top three conditions "
                "from the same model as before — layout only changed here."
            )

        predict_clicked = st.button("Predict", type="primary", use_container_width=True)

        if predict_clicked:
            if not selected:
                st.warning("Select symptoms")
            else:
                input_data = [0] * len(columns)

                for s in selected:
                    input_data[col_index[s]] = 1

                probs = model.predict_proba(pd.DataFrame([input_data], columns=columns))[0]

                top3 = probs.argsort()[-3:][::-1]

                st.markdown(
                    '<p class="clinical-section-title">📊 Results</p>',
                    unsafe_allow_html=True,
                )

                results = []

                doctor_map = {
                    "Dengue": "General Physician",
                    "Diabetes": "Endocrinologist",
                    "Heart attack": "Cardiologist",
                    "Migraine": "Neurologist",
                }

                for i in top3:
                    disease = le.classes_[i]
                    prob = round(probs[i] * 100, 2)

                    results.append({"disease": disease, "prob": prob})

                    # UI: Result “card” presentation — same disease, prob, desc, precautions, doctor text.
                    rank = len(results)
                    esc_disease = html.escape(str(disease))
                    st.markdown(
                        f"""
<div class="clinical-card">
  <span class="clinical-badge">Rank #{rank} · confidence</span>
  <h3>{esc_disease}</h3>
  <p class="clinical-muted">Model probability (unchanged calculation)</p>
</div>
""",
                        unsafe_allow_html=True,
                    )
                    pc1, pc2 = st.columns([4, 1], gap="small")
                    with pc1:
                        st.progress(int(prob))
                    with pc2:
                        st.markdown(f"**{prob}%**")

                    st.info(desc_dict.get(disease, ""))

                    for p in prec_dict.get(disease, []):
                        st.write("✔", p)

                    st.success("Doctor: " + doctor_map.get(disease, "General Physician"))

                    st.markdown("---")

                # GRAPH
                labels = [r["disease"] for r in results]
                values = [r["prob"] for r in results]

                fig, ax = plt.subplots(figsize=(8, 3.2))
                # UI: Chart colors and grid only — same barh(labels, values) data.
                fig.patch.set_facecolor("#fafbfc")
                ax.set_facecolor("#fafbfc")
                bars = ax.barh(labels, values, color=["#0d9488", "#14b8a6", "#5eead6"], height=0.55)
                ax.set_xlabel("Probability (%)", color="#475569", fontsize=10)
                ax.tick_params(colors="#475569", labelsize=9)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.grid(axis="x", linestyle="--", alpha=0.35)
                for b in bars:
                    w = b.get_width()
                    ax.text(
                        w + 0.8,
                        b.get_y() + b.get_height() / 2,
                        f"{w:.1f}%",
                        va="center",
                        ha="left",
                        fontsize=9,
                        color="#334155",
                    )
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                # SAVE HISTORY
                user = st.session_state.user
                if user not in history:
                    history[user] = []

                history[user].append(
                    {
                        "symptoms": selected,
                        "results": results,
                        "time": str(datetime.datetime.now()),
                    }
                )

                json.dump(history, open("history.json", "w"), indent=4)

                st.success("Saved!")

    # ================= HISTORY =================
    elif page == "History":

        st.markdown(
            '<p class="clinical-section-title">📜 Consultation history</p>',
            unsafe_allow_html=True,
        )

        user = st.session_state.user
        user_hist = history.get(user, [])

        if not user_hist:
            st.info("No history")
        else:
            for h in reversed(user_hist):
                # UI: Section chrome only — same Time / Symptoms / Prediction lines as before.
                st.write("Time:", h["time"])
                st.write("Symptoms:", h["symptoms"])
                st.write("Prediction:", h["results"][0]["disease"])
                st.markdown("---")

    # ================= CHATBOT (FREE) =================
    elif page == "Chatbot":

        st.markdown(
            '<p class="clinical-section-title">🤖 Health Assistant</p>',
            unsafe_allow_html=True,
        )
        st.caption("Rule-based assistant — same responses as before.")

        user_input = st.text_input("Ask something")

        if st.button("Ask"):
            # SIMPLE RULE-BASED CHATBOT
            if "fever" in user_input.lower():
                reply = "You may have infection. Drink fluids and consult doctor."
            elif "headache" in user_input.lower():
                reply = "Take rest, stay hydrated. If severe, consult doctor."
            elif "cold" in user_input.lower():
                reply = "Common cold. Take steam and warm fluids."
            else:
                reply = "Please consult a doctor for proper diagnosis."

            # UI: Chat bubbles — same user_input and reply strings as before; presentation only.
            esc_q = html.escape(user_input)
            esc_r = html.escape(reply)
            st.markdown(
                f"""
<div class="chatbot-thread">
  <div class="chat-row-user">
    <div class="chat-bubble chat-bubble-user">
      <span class="chat-meta">You</span>
      <p class="chat-body">{esc_q}</p>
    </div>
  </div>
  <div class="chat-row-bot">
    <div class="chat-bubble chat-bubble-bot">
      <span class="chat-meta">Assistant</span>
      <p class="chat-body">{esc_r}</p>
    </div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

    # ================= HOSPITALS =================
    elif page == "Hospitals":

        st.markdown(
            '<p class="clinical-section-title">🏥 Nearby Hospitals</p>',
            unsafe_allow_html=True,
        )
        st.caption("Embedded map — same URL pattern as before.")

        location = st.text_input("Enter city", "Bathinda")

        if location:
            map_url = f"https://www.google.com/maps?q=hospitals+near+{location}&output=embed"
            with st.container():
                st.components.v1.iframe(map_url, height=400)

    # ================= REPORT ANALYZER (separate module) =================
    elif page == "Report Analyzer":
        _render_report_analyzer_page()

else:
    # UI: Clearer empty state for unauthenticated users.
    st.markdown(
        """
<div class="clinical-card" style="border-left-color:#f59e0b;">
  <span class="clinical-badge" style="background:#fffbeb;color:#b45309;">Authentication required</span>
  <h3 style="margin-top:0.5rem;">Please sign in</h3>
  <p class="clinical-muted" style="margin:0;">Use the sidebar to log in or create an account. All features remain the same after login.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.warning("Login first")
