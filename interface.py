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

# Set Desktop path for saving files
desktop = os.path.join(os.path.expanduser("~"), "Desktop")

st.set_page_config(page_title="Art Tagging Tool", layout="wide")
st.title("Art Tagging Tool")

# --- Apply custom CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Questrial&display=swap');

    html, body, [class*="css"] {
        font-family: 'Questrial', sans-serif !important;
        transition: all 0.3s ease-in-out;
    }

    body {
        background-color: #111;
        color: #eee;
    }

    .stButton>button {
        background-color: transparent;
        color: inherit;
        font-size: 16px;
        padding: 10px 20px;
        border: 1px solid currentColor;
        border-radius: 8px;
        cursor: pointer;
    }

    .stButton>button:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }

    .stTextInput input, .stTextArea textarea, .stMultiselect>div>div>input {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #888;
        background-color: inherit;
        color: inherit;
    }

    h1, h2, h3, h4, h5, h6 {
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
</style>
""", unsafe_allow_html=True)

# --- Load vocabularies ---
dutch_keywords, english_keywords = [], []
try:
    dutch_terms = pd.read_csv("SUBJECT_all_terms_DUTCH.csv")
    english_terms = pd.read_csv("SUBJECT_all_terms_ENGLISH.csv")
    dutch_keywords = sorted(dutch_terms["term"].dropna().unique().tolist())
    english_keywords = sorted(english_terms["term"].dropna().unique().tolist())
except Exception as e:
    st.error(f"Error loading keywords: {e}")

# --- Session Management ---
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

saved_sessions = [
    f.replace("session_", "").replace(".json", "")
    for f in os.listdir(SESSION_DIR)
    if f.startswith("session_") and "_backup_" not in f and os.path.isfile(os.path.join(SESSION_DIR, f))
]

st.sidebar.subheader("\U0001F9D1 Session Management")
session_to_delete = st.sidebar.selectbox("Delete a session (optional)", ["None"] + saved_sessions)
if session_to_delete != "None" and st.sidebar.button("\u274C Delete Session"):
    try:
        os.remove(os.path.join(SESSION_DIR, f"session_{session_to_delete}.json"))
        st.sidebar.success(f"Deleted session: {session_to_delete}")
    except Exception as e:
        st.sidebar.error(f"Failed to delete: {e}")

session_name = st.sidebar.selectbox(
    "Select or create a session",
    options=["(new session)"] + saved_sessions,
    index=0,
    format_func=lambda x: "\U0001F195 Create new session" if x == "(new session)" else x
)

session_path = None
if session_name == "(new session)":
    new_session_input = st.sidebar.text_input("Enter a new session name")
    if new_session_input:
        session_name = sanitize_filename(new_session_input)
        session_path = os.path.join(SESSION_DIR, f"session_{session_name}.json")
        with open(session_path, "w") as f:
            json.dump({"index": 0, "edited_data": [], "metadata_cols": []}, f)
        st.sidebar.success(f"Session '{session_name}' created!")
else:
    session_name = sanitize_filename(session_name)
    session_path = os.path.join(SESSION_DIR, f"session_{session_name}.json")

output_filename = os.path.join(desktop, f"temp_output_{session_name}.csv") if session_name else None

if saved_sessions:
    st.sidebar.markdown("---")
    st.sidebar.caption("\U0001F4C1 Saved Sessions:")
    for s in sorted(saved_sessions):
        try:
            path = os.path.join(SESSION_DIR, f"session_{s}.json")
            timestamp = time.ctime(os.path.getmtime(path))
            st.sidebar.markdown(f"- `{s}` _(last modified: {timestamp})_")
        except FileNotFoundError:
            continue

mode = st.sidebar.radio("Choose input mode:", ["Run tagging pipeline", "Upload pre-tagged CSV"])

if output_filename and os.path.exists(output_filename):
    st.session_state["output_ready"] = output_filename

if mode == "Run tagging pipeline":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv", key="pipeline_upload")
    if uploaded_file:
        input_filename = f"temp_input_{session_name}.csv"
        with open(input_filename, "wb") as f:
            f.write(uploaded_file.read())
        output_name = st.text_input("Name your output CSV", value="tagged_output")
        if st.button("Run Tagging Pipeline ✅"):
            with st.spinner("Running the tagging pipeline..."):
                try:
                    result = subprocess.run(["python", SCRIPT_NAME, input_filename, output_filename], capture_output=True, text=True)
                    if result.returncode != 0:
                        st.error("❌ Error running the pipeline:")
                        st.code(result.stderr)
                    else:
                        st.success("✅ Pipeline completed successfully!")
                        st.session_state["output_ready"] = output_filename
                except Exception as e:
                    st.error(f"Exception occurred: {e}")

elif mode == "Upload pre-tagged CSV":
    pretagged_file = st.file_uploader("Upload a pre-tagged CSV file", type="csv", key="pretagged_upload")
    if pretagged_file and output_filename:
        with open(output_filename, "wb") as f:
            f.write(pretagged_file.read())
        st.session_state["output_ready"] = output_filename
        st.success("✅ File uploaded and ready for review!")

# --- REVIEW UI SECTION ---
if session_path and "output_ready" in st.session_state:

    if "index" not in st.session_state:
        st.session_state.index = 0
    if "edited_data" not in st.session_state:
        st.session_state.edited_data = []
    if "metadata_cols" not in st.session_state:
        st.session_state.metadata_cols = []
    if "last_autosave" not in st.session_state:
        st.session_state.last_autosave = time.time()

    def autosave():
        while True:
            time.sleep(5)
            if time.time() - st.session_state.last_autosave >= 10:
                with open(session_path, "w") as f:
                    json.dump({"index": st.session_state.index, "edited_data": st.session_state.edited_data, "metadata_cols": st.session_state.metadata_cols}, f)
                backup_path = session_path.replace(".json", f"_backup_{int(time.time())}.json")
                with open(backup_path, "w") as f:
                    json.dump({"index": st.session_state.index, "edited_data": st.session_state.edited_data, "metadata_cols": st.session_state.metadata_cols}, f)
                st.session_state.last_autosave = time.time()

    if "autosave_thread" not in st.session_state or not st.session_state.autosave_thread.is_alive():
        st.session_state.autosave_thread = threading.Thread(target=autosave, daemon=True)
        st.session_state.autosave_thread.start()

    output_path = st.session_state.get("output_ready")
    if output_path and os.path.exists(output_path):
        df = pd.read_csv(output_path)
    else:
        st.error(f"❌ File not found: {output_path}")
        st.stop()

    if os.path.exists(session_path):
        with open(session_path, "r") as f:
            saved_data = json.load(f)
            st.session_state.index = saved_data.get("index", 0)
            st.session_state.edited_data = saved_data.get("edited_data", [])
            st.session_state.metadata_cols = saved_data.get("metadata_cols", [col for col in df.columns if col not in ["tags EN", "tags NL"]])

    if len(st.session_state.edited_data) > 0:
        edited_df = pd.DataFrame(st.session_state.edited_data)
        for index, row in edited_df.iterrows():
            df.loc[index, :] = row

    st.sidebar.markdown("## \U0001F4C8 Progress")
    st.sidebar.markdown(f"**{st.session_state.index + 1} / {len(df)} artworks reviewed**")

    all_titles = df["Artwork"].tolist()
    selected_title = st.sidebar.selectbox("\U0001F50D Jump to artwork:", options=all_titles, index=st.session_state.index)
    st.session_state.index = all_titles.index(selected_title)

    with st.expander("⚙️ Select metadata columns to display"):
        st.session_state.metadata_cols = st.multiselect("Choose columns to show:", options=[col for col in df.columns if col not in ["tags EN", "tags NL"]], default=st.session_state.metadata_cols)

    current_row = df.iloc[st.session_state.index]
    st.markdown(f"### Artwork {st.session_state.index + 1} of {len(df)}")
    st.progress((st.session_state.index + 1) / len(df))

    for col in st.session_state.metadata_cols:
        st.write(f"**{col.capitalize()}**: {current_row[col]}")

    st.subheader("\U0001F1EC\U0001F1E7 English Tags")
    default_en = [tag.strip() for tag in str(current_row.get("tags EN", "") or '').split(";") if tag.strip()]
    selected_en = st.multiselect("Edit English tags", options=sorted(set(default_en + english_keywords)), default=default_en, key=f"en_{st.session_state.index}")
    new_en = st.text_input("Add new English tags (comma-separated)", key=f"new_en_{st.session_state.index}")
    if new_en:
        new_en_tag_list = [tag.strip() for tag in new_en.split(",") if tag.strip()]
        for tag in new_en_tag_list:
            if tag not in selected_en:
                selected_en.append(tag)
        st.markdown("New Tags: " + " • ".join(new_en_tag_list), unsafe_allow_html=True)

    st.subheader("\U0001F1F3\U0001F1F1 Dutch Tags")
    default_nl = [tag.strip() for tag in str(current_row.get("tags NL", "") or '').split(";") if tag.strip()]
    selected_nl = st.multiselect("Edit Dutch tags", options=sorted(set(default_nl + dutch_keywords)), default=default_nl, key=f"nl_{st.session_state.index}")
    new_nl = st.text_input("Add new Dutch tags (comma-separated)", key=f"new_nl_{st.session_state.index}")
    if new_nl:
        new_nl_tag_list = [tag.strip() for tag in new_nl.split(",") if tag.strip()]
        for tag in new_nl_tag_list:
            if tag not in selected_nl:
                selected_nl.append(tag)
        st.markdown("New Tags: " + " • ".join(new_nl_tag_list), unsafe_allow_html=True)

    def save_edits():
        updated_row = current_row.to_dict()
        updated_row["tags EN"] = "; ".join(selected_en)
        updated_row["tags NL"] = "; ".join(selected_nl)
        if len(st.session_state.edited_data) > st.session_state.index:
            st.session_state.edited_data[st.session_state.index] = updated_row
        else:
            st.session_state.edited_data.append(updated_row)

    def go_back():
        save_edits()
        st.session_state.index = max(0, st.session_state.index - 1)

    def go_next():
        save_edits()
        st.session_state.index = min(len(df) - 1, st.session_state.index + 1)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Back"):
            go_back()
    with col2:
        if st.button("➡️ Next"):
            go_next()

    # --- Save Now button ---
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Save Now"):
        with open(session_path, "w") as f:
            json.dump({
                "index": st.session_state.index,
                "edited_data": st.session_state.edited_data,
                "metadata_cols": st.session_state.metadata_cols
            }, f)
        st.session_state.last_autosave = time.time()
        st.sidebar.markdown("**Saved.**")

    last_saved_time = datetime.datetime.fromtimestamp(st.session_state.last_autosave).strftime('%H:%M:%S')
    st.sidebar.caption(f"🕒 Last saved: {last_saved_time}")

    all_tags = [
        tag.strip()
        for row in st.session_state.edited_data
        for tag in row.get("tags EN", "").split(";") + row.get("tags NL", "").split(";")
        if tag.strip()
    ]
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
                    const nextButton = [...document.querySelectorAll('button')].find(btn => btn.innerText.includes('Next'));
                    if (nextButton) nextButton.click();
                }
                if (e.key === 'ArrowLeft') {
                    const backButton = [...document.querySelectorAll('button')].find(btn => btn.innerText.includes('Back'));
                    if (backButton) backButton.click();
                }
            });
            </script>
        """, unsafe_allow_html=True)