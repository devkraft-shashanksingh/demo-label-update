import streamlit as st
import requests

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
API_BASE_URL = "http://13.234.60.125:8000"

PI_UPLOAD_API = f"{API_BASE_URL}/files/upload"
PI_PROCESS_API = f"{API_BASE_URL}/process/process-PI-mistral"
PI_LLM_KEY_API = f"{API_BASE_URL}/processed/llm-key"
PI_RAG_INDEX_API = f"{API_BASE_URL}/rag/index-pi"

ASSET_UPLOAD_API = f"{API_BASE_URL}/files/upload"
ASSET_PROCESS_API = f"{API_BASE_URL}/process/process-asset"

VERIFY_CLAIM_API = f"{API_BASE_URL}/rag/hybrid-single-verify-claim"

# -----------------------------------------------
# COLLECTION NAME
# -----------------------------------------------
def get_collection_and_endpage(filename: str):
    name = filename.lower()

    if "braftovi" in name or "mektovi" in name:
        return "label_poc_1", 1

    if "cibinqo" in name or "abrocitinib" in name:
        return "label_poc_2", 1

    if "prolia" in name:
        return "label_poc_3", 1

    if "imlygic" in name:
        return "label_poc_4", 1

    # fallback
    return "label_poc_default", 1



# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
for key in ["pi_done", "asset_done"]:
    if key not in st.session_state:
        st.session_state[key] = False

# -------------------------------------------------
# UI
# -------------------------------------------------
st.set_page_config(page_title="Label Update", layout="centered")
st.markdown(
    """
    <style>
    /* Make Verify Claim button bigger & professional */
    div.stButton > button {
        width: 100%;
        height: 3.6rem;
        font-size: 1.15rem;
        font-weight: 700;
        border-radius: 12px;
        background: linear-gradient(90deg, #2563eb, #1d4ed8);
        color: white;
        border: none;
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.35);
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8, #1e40af);
        box-shadow: 0 12px 26px rgba(37, 99, 235, 0.45);
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("📄 Label Update")

# -------------------------------------------------
# STEP 1: PI
# -------------------------------------------------

col_pi, col_asset = st.columns(2)

with col_pi:
    pi_files = st.file_uploader(
        "📁 Upload PI Document(s)",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

with col_asset:
    asset_file = st.file_uploader(
        "📁 Upload Asset Document",
        type=["pdf", "docx"]
    )


if pi_files and not st.session_state.pi_done:

    for idx, pi_file in enumerate(pi_files, 1):
        #st.markdown(f"### Processing PI File {idx} of {len(pi_files)}")

        progress = st.progress(0)
        if "collection" not in st.session_state:
            collection, end_page = get_collection_and_endpage(pi_file.name)
            st.session_state.collection = collection
            st.session_state.end_page = end_page

        with st.spinner(f"Uploading PI document {idx}..."):
            progress.progress(10)
            pi_upload = requests.post(
                PI_UPLOAD_API,
                files={"file": pi_file}
            )
            pi_upload.raise_for_status()

        pi_key = pi_upload.json()["key"]

        with st.spinner("Extracting PI content..."):
            progress.progress(40)
            pi_process = requests.post(
                PI_PROCESS_API,
                json={"key": pi_key}
            )
            pi_process.raise_for_status()

        processed_key = pi_process.json()["processed_key"]

        with st.spinner("Generating Markdown..."):
            progress.progress(70)
            llm_key_resp = requests.get(
                PI_LLM_KEY_API,
                params={"key": processed_key}
            )
            llm_key_resp.raise_for_status()

        llm_md_path = llm_key_resp.text

        with st.spinner(f"Creating Embeddings PI File {idx}..."):
            progress.progress(90)
            rag_resp = requests.post(
                PI_RAG_INDEX_API,
                json={
                    "md_key": llm_md_path,
                    "collection": st.session_state.collection
                }
            )
            rag_resp.raise_for_status()

        progress.progress(100)
        progress.empty()

        st.toast(f"PI File {idx} Processed Successfully", icon="✅")

    st.session_state.pi_done = True


# -------------------------------------------------
# STEP 2: ASSET
# -------------------------------------------------

if asset_file and st.session_state.pi_done and not st.session_state.asset_done:
    progress = st.progress(0)

    with st.spinner("Uploading Asset Document..."):
        progress.progress(20)
        asset_upload = requests.post(ASSET_UPLOAD_API, files={"file": asset_file})
        asset_upload.raise_for_status()

    asset_key = asset_upload.json()["key"]

    with st.spinner("Extracting Asset Claims..."):
        progress.progress(80)
        asset_process = requests.post(
            ASSET_PROCESS_API,
            json={"key": asset_key, "start_page": 1, "end_page": st.session_state.end_page}
        )
        asset_process.raise_for_status()

    st.session_state.asset_done = True
    progress.progress(100)
    progress.empty()
    st.toast("Asset Extraction Completed", icon="✅")

# -------------------------------------------------
# STEP 3: VERIFY CLAIM
# -------------------------------------------------
st.markdown(
    """
    
    <h2 style="
        color: var(--text-color);
        font-weight: 700;
        margin-top: 24px;
        margin-bottom: 10px;
    ">
        🔍 Claim Verification
    </h2>

    <div style="
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--secondary-text-color);
        margin-bottom: 10px;
    ">
        Enter a claim sentence below to verify it against the label sources
    </div>
    
    <style>
    /* Theme-safe textarea styling */
    textarea {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(0,0,0,0.15) !important;
        border-radius: 12px !important;
        font-size: 1.05rem !important;
        line-height: 1.6 !important;
        padding: 14px !important;
    }

    textarea::placeholder {
        color: var(--secondary-text-color) !important;
        font-style: italic;
    }

    textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25);
        outline: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)



claim_sentence = st.text_area(
    "Claim sentence",
    height=240,
    placeholder="Type your claim sentence here...",
    label_visibility="collapsed"
)

verify_btn = st.button("🔍 Verify Claim")

if verify_btn:
    progress = st.progress(0)

    with st.spinner("Verifying Claim..."):
        progress.progress(50)
        response = requests.post(
            VERIFY_CLAIM_API,
            json={
                "claim_sentence": claim_sentence,
                "collection": st.session_state.collection
            },
            timeout=60
        )
        response.raise_for_status()

    progress.progress(100)
    progress.empty()
    result = response.json()

    #st.success("✅ Claim verification completed")
    st.toast("Claim Verification Completed", icon="✅")


    # ---------------- OUTPUT ----------------
    st.subheader("📄 Verification Result")
    replacement = result.get("replacement_text")
    INVALID_VALUES = {None, "", "none", "null", "n/a", "na"}

    has_insufficient_info = not (
            isinstance(replacement, str)
            and replacement.strip().lower() not in INVALID_VALUES
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Valid Claim**")

        if has_insufficient_info:
            st.write("Insufficient Information")
        else:
            st.write("Yes" if result.get("valid") else "No")

    with col2:
        supers = result.get("superscripts", [])
        st.metric("Superscripts", ", ".join(supers) if supers else " ")

    st.divider()

    st.markdown("### Original Sentence")
    st.write(result.get("sentence", "—"))

    # Always show replacement section if info is insufficient OR invalid
    if has_insufficient_info or not result.get("valid", True):

        st.markdown("### Suggested Replacement")

        if isinstance(replacement, str) and replacement.strip().lower() not in INVALID_VALUES:
            # BLUE box (valid replacement)
            st.info(replacement)
        else:
            # RED box (insufficient information)
            st.markdown(
                """
                <div style="
                    background-color: rgba(220, 38, 38, 0.15);
                    border-left: 6px solid #dc2626;
                    padding: 14px;
                    border-radius: 10px;
                    font-weight: 600;
                    color: #7f1d1d;
                ">
                    Not enough information is provided in the document.
                </div>
                """,
                unsafe_allow_html=True
            )

        # Show confidence score ONLY for invalid claims with a real replacement
        score = result.get("score")

        if (
                not result.get("valid", True) and
                not has_insufficient_info and
                isinstance(score, (int, float))
        ):
            st.metric("Confidence Score", f"{score:.2f}")

    st.markdown("### Explanation")
    st.write(result.get("explanation", " "))

    st.markdown("### Reasoning")
    st.write(result.get("reasoning", " "))

    st.markdown("### Sources Summary")
    for src in result.get("sources", []):
        st.write(f"- {src}")

    struc_sources = result.get("struc_sources", [])
    st.divider()

    if not struc_sources:
        st.info("No detailed structured sources available.")
    else:
        st.markdown("### 📚 All Sources")
        for idx, src in enumerate(struc_sources, 1):
            with st.container(border=False):

                # ----- Source title -----
                st.markdown(f"#### Source {idx}")

                # ----- Page + File (BLACK) -----
                page = src.get("page_number", "N/A")
                file = src.get("source", "N/A")

                st.markdown(
                    f"""
                            <div style="color:inherit; font-weight:500;">
                                Page No: {page} &nbsp;|&nbsp; File: {file}
                            </div>
                            """,
                    unsafe_allow_html=True
                )
                # st.write(f"Page No: {page} &nbsp;|&nbsp; File: {file}")

                # ----- Heading (GREEN) -----
                heading = src.get("headings", "N/A")
                if heading:
                    st.markdown(
                        f"""
                                <div style="color:#22c55e; font-weight:600; margin-top:6px;">
                                    {heading}
                                </div>
                                """,
                        unsafe_allow_html=True
                    )

                # ----- Text (NORMAL) -----
                text = src.get("text")
                # st.markdown(f"""<div style="margin-top:8px;">{text}</div>""", unsafe_allow_html=True)
                st.write(text)
                st.write(" ")
