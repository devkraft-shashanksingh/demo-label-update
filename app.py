import streamlit as st
import time
import requests

# -----------------------------
# Config
# -----------------------------
API_URL = "http://13.234.60.125:8000/rag/single-verify-claim"  # change later
FIXED_COLLECTION = "label"
FIXED_TOP_K = 9
USE_DUMMY_RESPONSE = False  # set False when API is ready

# -----------------------------
# Dummy API Response
# -----------------------------
def dummy_response(claim_sentence):
    return {
        "sentence": claim_sentence,
        "superscripts": ["¹", "²"],
        "valid": False,
        "replacement_text": (
            "An oral treatment combination for patients with unresectable or "
            "metastatic melanoma with a BRAF V600E or V600K mutation¹˒²"
        ),
        "explanation": (
            "The sources support that BRAFTOVI (encorafenib) in combination with "
            "binimetinib is indicated for patients with unresectable or metastatic "
            "melanoma with a BRAF V600E or V600K mutation. The claim is not fully "
            "supported because it limits the population to adults and does not "
            "specify the mutation subtype."
        ),
        "reasoning": (
            "Source 1 and Source 4 explicitly state the melanoma indication as "
            "treatment of patients with unresectable or metastatic melanoma with "
            "a BRAF V600E or V600K mutation. None specify adults."
        ),
        "sources": ["Source 1", "Source 4"],
        "score": 0.76573133
    }

# -----------------------------
# API Call
# -----------------------------
def verify_claim(claim_sentence):
    payload = {
        "claim_sentence": claim_sentence,
        "collection": FIXED_COLLECTION,
        "top_k": FIXED_TOP_K
    }

    if USE_DUMMY_RESPONSE:
        time.sleep(2)  # simulate API latency
        return dummy_response(claim_sentence)

    response = requests.post(API_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Claim Verification", layout="centered")

st.title("🔍 Claim Verification")
st.write("Enter a claim sentence below to verify it against the label sources.")

claim_sentence = st.text_area(
    "Claim Sentence",
    placeholder="Type your claim sentence here...",
    height=120
)

verify_btn = st.button("Verify Claim")

if verify_btn:
    if not claim_sentence.strip():
        st.warning("Please enter a claim sentence.")
    else:
        with st.spinner("Verifying claim..."):
            progress = st.progress(0)
            for i in range(1, 6):
                time.sleep(0.2)
                progress.progress(i * 20)

            try:
                result = verify_claim(claim_sentence)
                progress.progress(100)
            except Exception as e:
                st.error(f"Error while verifying claim: {e}")
                st.stop()

        st.success("Verification completed")

        # -----------------------------
        # Output Section
        # -----------------------------
        st.subheader("📄 Result")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Valid Claim", "Yes" if result["valid"] else "No")
        with col2:
            st.metric("Confidence Score", f'{result["score"]:.2f}')

        st.markdown("### Original Sentence")
        st.write(result["sentence"])

        st.markdown("### Superscripts")
        st.write(", ".join(result["superscripts"]))

        if not result["valid"]:
            st.markdown("### Suggested Replacement")
            st.info(result["replacement_text"])

        st.markdown("### Explanation")
        st.write(result["explanation"])

        st.markdown("### Reasoning")
        st.write(result["reasoning"])

        st.markdown("### Sources")
        for src in result["sources"]:
            st.write(f"- {src}")
