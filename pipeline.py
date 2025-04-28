import streamlit as st
import pandas as pd
import subprocess
import os
import uuid
import json
import time
import threading
import datetime
from collections import Counter
import platform
import re

# --- CONFIG ---
SCRIPT_NAME = "pipeline.py"
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

st.set_page_config(layout="wide")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Kaushan+Script&display=swap" rel="stylesheet">
<h1 class="kaushan-title" style='
    font-family: "Kaushan Script", cursive !important;
    font-size: 4rem;
    font-weight: 400;
    letter-spacing: 2px;
    margin-bottom: 0.5em;
'>
    semARTagger
</h1>
<style>
.kaushan-title {
    font-family: 'Kaushan Script', cursive !important;
    font-weight: 400 !important;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Questrial&display=swap" rel="stylesheet">
    <style>
        *:not(.montserrat-title):not(.kaushan-title) { font-family: 'Questrial', sans-serif !important; }
        html, body, [class*="css"] { font-size: 16px; line-height: 1.6; }
        body { background-color: #111; color: #eee; }
        .stButton>button {
           background-color: transparent;
           color: inherit;
           font-size: 13px !important;
           padding: 8px 16px;
           border: 1px solid currentColor;
           border-radius: 8px;
           cursor: pointer;
           white-space: nowrap !important;
        }
        .stButton>button:hover { background-color: rgba(255, 255, 255, 0.1); }
        .stTextInput input, .stTextArea textarea,
        .stMultiselect>div>div>input, .stSelectbox>div>div>input {
           padding: 8px;
           border-radius: 5px;
           border: 1px solid #888;
           background-color: inherit;
           color: inherit;
        }
        /* Make all sidebar labels bigger */
        [data-testid="stSidebar"] label {
            font-size: 13px !important;
            font-weight: 600 !important;
        }
        .montserrat-title {
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 700 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Load full vocabularies for dropdowns ---
dutch_keywords, english_keywords = [], []
try:
    dutch_terms = pd.read_csv("SUBJECT_all_terms_DUTCH.csv")
    english_terms = pd.read_csv("SUBJECT_all_terms_ENGLISH.csv")
    dutch_keywords = sorted(dutch_terms["term"].dropna().unique().tolist())
    english_keywords = sorted(english_terms["term"].dropna().unique().tolist())
except Exception as e:
    st.error(f"Error loading keywords: {e}")

# --- Session Picker with delete option ---
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

session_path = None
saved_sessions = [
    f.replace("session_", "").replace(".json", "")
    for f in os.listdir(SESSION_DIR)
    if f.startswith("session_") and "_backup_" not in f
]
st.sidebar.subheader("Session Management")
session_to_delete = st.sidebar.selectbox("Delete a session (optional)", ["None"] + saved_sessions)
if session_to_delete != "None" and st.sidebar.button("Delete Session"):
    os.remove(os.path.join(SESSION_DIR, f"session_{session_to_delete}.json"))
    st.sidebar.success(f"Deleted session: {session_to_delete}")
    st.rerun()

# --- Session selection and restore ---
session_name = st.sidebar.selectbox(
    "Select or create a session",
    options=["(new session)"] + saved_sessions,
    index=0,
    format_func=lambda x: "Create new session" if x == "(new session)" else x,
    key="session_select"
)

if session_name == "(new session)":
    new_session_input = st.sidebar.text_input("Enter a new session name")
    if new_session_input:
        session_name = sanitize_filename(new_session_input)
        session_path = os.path.join(SESSION_DIR, f"session_{session_name}.json")
        with open(session_path, "w") as f:
            json.dump({"index": 0, "edited_data": [], "metadata_cols": []}, f)
        st.sidebar.success(f"Session '{session_name}' created and saved!")
        st.session_state["restored_session"] = session_name
        st.rerun()
    else:
        st.warning("Please enter a valid session name to create a new session.")
        st.stop()
else:
    session_path = os.path.join(SESSION_DIR, f"session_{session_name}.json")
    # --- Restore session state if changed ---
    if (
        "restored_session" not in st.session_state
        or st.session_state["restored_session"] != session_name
    ):
        if os.path.exists(session_path):
            with open(session_path, "r") as f:
                data = json.load(f)
                st.session_state.index = data.get("index", 0)
                st.session_state.edited_data = data.get("edited_data", [])
            st.session_state["restored_session"] = session_name

if session_name and session_name != "(new session)":
    output_filename = f"temp_output_{session_name}.csv"
else:
    output_filename = None

if saved_sessions:
    st.sidebar.markdown("---")
    st.sidebar.caption("📁 Saved Sessions:")
    for s in sorted(saved_sessions):
        path = os.path.join(SESSION_DIR, f"session_{s}.json")
        timestamp = time.ctime(os.path.getmtime(path))
        st.sidebar.markdown(f"- `{s}` _(last modified: {timestamp})_)")

mode = st.sidebar.radio("Choose input mode:", ["Run tagging pipeline", "Upload pre-tagged CSV"])

if mode == "Run tagging pipeline":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv", key="pipeline_upload")
    if uploaded_file:
        input_filename = f"temp_input_{session_name}.csv"
        with open(input_filename, "wb") as f:
            f.write(uploaded_file.read())
        output_name = st.text_input("Name your output CSV (for download only)", value="tagged_output")
        if st.button("Run Tagging Pipeline"):
            with st.spinner("Running the tagging pipeline..."):
                try:
                    result = subprocess.run(
                        ["python", SCRIPT_NAME, input_filename, output_filename],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        st.error("Error running the pipeline:")
                        st.code(result.stderr)
                    else:
                        st.success("Pipeline completed successfully!")
                        st.session_state["output_ready"] = output_filename
                        st.info(f"Output file created: {output_filename}")
                except Exception as e:
                    st.error(f"Exception occurred while running the pipeline: {e}")

elif mode == "Upload pre-tagged CSV":
    pretagged_file = st.file_uploader("Upload a pre-tagged CSV file", type="csv", key="pretagged_upload")
    if pretagged_file:
        with open(output_filename, "wb") as f:
            f.write(pretagged_file.read())
        st.session_state["output_ready"] = output_filename
        st.success("File uploaded and ready for review!")
    else:
        st.warning("Please upload a pre-tagged CSV file.")

# --- Auto-save function with timestamp ---
def auto_save_session():
    if session_path:
        with open(session_path, "w") as f:
            json.dump({
                "index": st.session_state.index,
                "edited_data": st.session_state.edited_data,
            }, f)
        st.session_state["last_autosave"] = datetime.datetime.now().strftime("%H:%M:%S")

# Guarantee autosave on every rerun (including idle refresh)
auto_save_session()

# --- After Pipeline/Upload: Process the CSV (df) and Show Interface ---
if session_path and "output_ready" in st.session_state:
    if os.path.exists(st.session_state["output_ready"]):
        df = pd.read_csv(st.session_state["output_ready"])
        # Initialize session state variables if needed
        if "index" not in st.session_state:
            st.session_state.index = 0
        if "edited_data" not in st.session_state:
            st.session_state.edited_data = []
        if "selected_en" not in st.session_state:
            st.session_state.selected_en = []
        if "selected_nl" not in st.session_state:
            st.session_state.selected_nl = []
    else:
        st.error("The output file does not exist. Please run the tagging pipeline or upload a pre-tagged CSV file.")
        st.stop()

    st.sidebar.markdown("## 📈 Progress")
    st.sidebar.markdown(f"**{st.session_state.index + 1} / {len(df)} artworks reviewed**")

    # --- Jump-to-Artwork Dropdown ---
    all_titles = df["Artwork"].tolist()
    selected_title = st.sidebar.selectbox(
        "🔍 Jump to artwork:",
        options=all_titles,
        index=st.session_state.index,
        key="nav_sidebar_jumpto"
    )
    st.session_state.index = all_titles.index(selected_title)

    # --- Save Session Button ---
    def save_session():
        with open(session_path, "w") as f:
            json.dump({
                "index": st.session_state.index,
                "edited_data": st.session_state.edited_data,
            }, f)
        st.sidebar.success("Session saved!")
        st.session_state["last_autosave"] = datetime.datetime.now().strftime("%H:%M:%S")
    st.sidebar.button("💾 Save Session", on_click=save_session)

    # --- Show last auto-save time in the sidebar (after Save Session) ---
    last_autosave = st.session_state.get("last_autosave", "Never")
    st.sidebar.info(f"Last saved at {last_autosave}")

    # --- Export to CSV (with editable filename) ---
    export_filename = st.sidebar.text_input(
        "Export CSV filename", value=f"edited_output_{session_name}.csv"
    )
    if st.sidebar.button("📤 Export Edited Tags to CSV"):
        if st.session_state.edited_data:
            export_df = pd.DataFrame(st.session_state.edited_data)
            export_df.to_csv(export_filename, index=False)
            with open(export_filename, "rb") as f:
                st.sidebar.download_button("Download CSV", f, file_name=export_filename, mime="text/csv")
        else:
            st.sidebar.warning("No edited data to export yet!")

    current_row = df.iloc[st.session_state.index]

    # --- Artwork Header and Metadata Display (Bigger Font) ---
    st.markdown(f"### Artwork {st.session_state.index + 1} of {len(df)}")
    st.progress((st.session_state.index + 1) / len(df))
    metadata_columns = {"Artwork": "Artwork", "Artist Name": "Artist Name", "Location": "Location"}
    for col, display_name in metadata_columns.items():
        if col in df.columns:
            st.markdown(
                f"<div class='metadata' style='font-size: 20px;'>"
                f"<strong>{display_name}:</strong> <span>{current_row[col]}</span></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='metadata' style='font-size: 20px;'>"
                f"<strong>{display_name}:</strong> <span>Not available</span></div>",
                unsafe_allow_html=True
            )

    st.subheader("🇬🇧 English Tags")
    default_en = [tag.strip() for tag in str(current_row.get("tags EN", "")).split(";") if tag.strip()]
    selected_en = st.multiselect(
        "Edit English tags",
        options=sorted(set(default_en + english_keywords)),
        default=default_en,
        key=f"en_{st.session_state.index}"
    )
    new_en = st.text_input("Add new English tags (comma-separated)", key=f"new_en_{st.session_state.index}")
    if new_en:
        new_en_tag_list = [tag.strip() for tag in new_en.split(",") if tag.strip()]
        for new_tag in new_en_tag_list:
            if new_tag not in selected_en:
                selected_en.append(new_tag)
        highlighted_new_tags = " | ".join([f'<span style="color:green">{tag}</span>' for tag in new_en_tag_list])
        if highlighted_new_tags:
            st.markdown(f"<div>New Keywords: {highlighted_new_tags}</div>", unsafe_allow_html=True)
    st.session_state.selected_en = selected_en
    auto_save_session()

    st.subheader("🇳🇱 Dutch Tags")
    default_nl = [tag.strip() for tag in str(current_row.get("tags NL", "")).split(";") if tag.strip()]
    selected_nl = st.multiselect(
        "Edit Dutch tags",
        options=sorted(set(default_nl + dutch_keywords)),
        default=default_nl,
        key=f"nl_{st.session_state.index}"
    )
    new_nl = st.text_input("Add new Dutch tags (comma-separated)", key=f"new_nl_{st.session_state.index}")
    if new_nl:
        new_nl_tag_list = [tag.strip() for tag in new_nl.split(",") if tag.strip()]
        for new_tag in new_nl_tag_list:
            if new_tag not in selected_nl:
                selected_nl.append(new_tag)
        highlighted_new_nl_tags = " | ".join([f"<span style='color:green'>{tag}</span>" for tag in new_nl_tag_list])
        if highlighted_new_nl_tags:
            st.markdown(f"<div>New Keywords: {highlighted_new_nl_tags}</div>", unsafe_allow_html=True)
    st.session_state.selected_nl = selected_nl
    auto_save_session()

    # --- Navigation Buttons (Back left, Save & Continue right, aligned) ---
    col1, col2, col3 = st.columns([2, 8, 2])
    with col1:
        back_clicked = st.button("Back", key="back_btn")
    with col2:
        pass  # Spacer
    with col3:
        save_continue_clicked = st.button("Save & Continue", key="save_btn")  # Emoji removed to prevent wrapping

    if save_continue_clicked:
        updated_row = df.iloc[st.session_state.index].to_dict()
        updated_row["tags EN"] = "; ".join(st.session_state.selected_en)
        updated_row["tags NL"] = "; ".join(st.session_state.selected_nl)
        if len(st.session_state.edited_data) > st.session_state.index:
            st.session_state.edited_data[st.session_state.index] = updated_row
        else:
            st.session_state.edited_data.append(updated_row)
        st.session_state.index += 1
        if st.session_state.index >= len(df):
            st.session_state.index = len(df) - 1
        auto_save_session()
        st.rerun()

    if back_clicked:
        if st.session_state.index > 0:
            st.session_state.index -= 1
            auto_save_session()
            st.rerun()

    all_tags = []
    for i, row in df.iterrows():
        current = st.session_state.edited_data[i] if i < len(st.session_state.edited_data) else row.to_dict()
        en_tags = current.get("tags EN", "")
        nl_tags = current.get("tags NL", "")
        for tag in (en_tags + ";" + nl_tags).split(";"):
            if tag.strip():
                all_tags.append(tag.strip())
    if all_tags:
        tag_freq = Counter(all_tags).most_common(10)
        st.sidebar.markdown("### 🏷️ Top Tags")
        for tag, count in tag_freq:
            st.sidebar.markdown(f"- {tag}: {count}")

    if platform.system() != "Windows":
        st.markdown("""
            <script>
            document.addEventListener('keydown', e => {
                if (e.key === 'ArrowRight') {
                    const nextButton = [...document.querySelectorAll('button')]
                        .find(btn => btn.innerText.includes('Next'));
                    if (nextButton) nextButton.click();
                }
                if (e.key === 'ArrowLeft') {
                    const backButton = [...document.querySelectorAll('button')]
                        .find(btn => btn.innerText.includes('Back'));
                    if (backButton) backButton.click();
                }
            });
            </script>
        """, unsafe_allow_html=True)
