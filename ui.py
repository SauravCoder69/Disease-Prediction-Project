import streamlit as st
import requests

# UI: Page branding and centered column width (prediction request unchanged).
st.set_page_config(
    page_title="Disease Prediction · API Client",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
  .block-container { padding-top: 1.5rem; max-width: 640px; }
  [data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(180deg, #f0f7ff 0%, #eef2f7 100%);
  }
  .api-hero {
    background: linear-gradient(135deg, #0b3a5c 0%, #0f766e 100%);
    color: #f8fafc;
    padding: 1.25rem 1.35rem;
    border-radius: 14px;
    margin-bottom: 1.25rem;
    box-shadow: 0 10px 30px rgba(11, 58, 92, 0.2);
    border: 1px solid rgba(255,255,255,0.12);
  }
  .api-hero h1 { margin: 0; font-size: 1.5rem; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="api-hero"><h1>Disease Prediction System 🏥</h1></div>',
    unsafe_allow_html=True,
)

symptoms = st.text_input("Enter symptoms (comma separated)")

if st.button("Predict", type="primary", use_container_width=True):
    symptom_list = [s.strip() for s in symptoms.split(",")]

    response = requests.get(
        "http://127.0.0.1:5000/predict_get",
        params={"symptoms": ",".join(symptom_list)},
    )

    result = response.json()

    # UI: Visual grouping only — same success + writes as the original flow.
    st.markdown("##### Prediction output")
    st.success(f"Disease: {result['disease']}")
    st.write("Description:", result["description"])
    st.write("Precautions:", result["precaution"])
