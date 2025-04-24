import streamlit as st

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Kaushan+Script&family=Questrial&display=swap" rel="stylesheet">
<h1 class="kaushan-title" style="
    font-family: 'Kaushan Script', cursive !important;
    font-size: 4rem;
    font-weight: 400;
    letter-spacing: 2px;
    margin-bottom: 0.5em;
">
    About
</h1>
<style>
/* Title styling */
.kaushan-title {
    font-family: 'Kaushan Script', cursive !important;
    font-weight: 400 !important;
    letter-spacing: 2px;
}

/* Global font styling for all other text */
body, div, p, ul, li, h2, h3, h4, h5, h6, .stMarkdown {
    font-family: 'Questrial', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
**semARTagger** is a human–AI collaborative tagging interface developed as part of my Master’s thesis in Cultural Data & AI at the University of Amsterdam. It was created to support the Netherlands Institute for Art History (RKD) in enhancing the discoverability and structure of its digitized archival material, specifically the _Living Masters_ art exhibition catalogues.

- Developed by: Maria Elpiniki Zafeiraki
under the supervision of Dr. H. Lamqaddam,
in collaboration with the RKD – Netherlands Institute for Art History
- Version: 1.0
- Contact: [marnikzaf@gmail.com]

### Features
- **Smart Tag Suggestions** Get automatic tag suggestions for Dutch and French artwork titles using a multilingual AI model.
- **Batch Processing** Process multiple artworks at once for efficient tagging.
- **Easy-to-Use Interface** A user-friendly interface for easy tagging and editing.
- **Top Tags Sidebar** Quickly access the most commonly used tags to speed up your workflow and keep things consistent.
- **Export Your Work** Save your tagged artworks in CSV format for easy sharing and further analysis.
- And more!

You can find the full code for this interface and tagging pipeline in the GitHub repository: semARTagger (https://github.com/marnikzaf/semARTagger)

---
_This project is open source and welcomes contributions!_
""")