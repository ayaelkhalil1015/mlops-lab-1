import os
import requests
import streamlit as st

INFERENCE_URL = os.environ.get("INFERENCE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Food-11 Classifier",
    page_icon="🍽️",
    layout="centered",
)

st.markdown("""
<style>
    .block-container {
        max-width: 750px;
        padding-top: 3rem;
    }

    .title {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 2rem;
    }

    .result {
        padding: 20px;
        border-radius: 12px;
        background: rgba(128, 128, 128, 0.1);
        text-align: center;
        margin-top: 20px;
        font-size: 1.3rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🍽️ Food-11</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Upload a food image and let the model classify it.</div>',
    unsafe_allow_html=True
)

uploaded = st.file_uploader(
    "Choose an image",
    type=["jpg", "jpeg", "png"]
)

if uploaded is not None:
    st.image(uploaded, width=400)

    with st.spinner("Analyzing image..."):
        files = {
            "file": (
                uploaded.name,
                uploaded.getvalue(),
                uploaded.type
            )
        }

        try:
            response = requests.post(
                f"{INFERENCE_URL}/predict",
                files=files,
                timeout=30
            )

            if response.ok:
                result = response.json()

                st.markdown(
                    f"""
                    <div class="result">
                        Prediction<br>
                        <strong>{result['category']}</strong><br>
                        {result['confidence']:.1%} confidence
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.error(
                    f"Inference service returned "
                    f"{response.status_code}: {response.text}"
                )

        except requests.RequestException:
            st.error("Could not connect to the inference service.")
