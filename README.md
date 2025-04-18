# rkd-semantic-tagger

This repository contains the code for **rkd-semantic-tagger**, a pipeline developed as part of my Master's thesis in *Cultural Data & AI* at the University of Amsterdam. It automates the tagging of historical artworks based on semantic similarity, using multilingual sentence embeddings and a logistic regression classifier.

The tool was designed to process Dutch art exhibition catalogues and enrich them with descriptive tags, supporting art historical research and data structuring efforts at the RKD (Netherlands Institute for Art History).

---

## 📌 Project Description

The core pipeline uses [LaBSE (Language-Agnostic BERT Sentence Embedding)](https://tfhub.dev/google/LaBSE/1) to convert Dutch (and occasionally French) artwork titles into multilingual sentence embeddings. These embeddings are passed to a trained logistic regression classifier that predicts a controlled vocabulary of tags derived from RKD thesauri.

The interface allows users to review, edit, and export tags via a Streamlit web app, supporting both automated and manual modes of tagging.

---

## 📁 Project Structure

```
rkd-semantic-tagger/
├── pipeline/
│   ├── pipeline.py
│   ├── labse_logreg_model.pkl
│   ├── labse_label_binarizer.pkl
│   ├── SUBJECT_all_terms_DUTCH.csv
│   ├── SUBJECT_all_terms_ENGLISH.csv
│   ├── rkd_aat_term_mapping.csv
│   └── example_input.csv
│
├── interface/
│   ├── interface.py
│
├── requirements.txt
├── screenshots/
└── README.md
```

---

## 🚀 How to Use

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/rkd-semantic-tagger.git
cd rkd-semantic-tagger
```

### 2. Install dependencies

We recommend using Python 3.9+ and a virtual environment:

```bash
pip install -r requirements.txt
```

### 3. Run the pipeline

Make sure your input CSV contains a column titled `"Artwork"` with Dutch or French titles.

```bash
cd pipeline
python pipeline.py --input example_input.csv
```

### 4. Launch the Streamlit interface

```bash
cd interface
streamlit run interface.py
```

You’ll be able to upload data, run the tagging pipeline, review predicted tags, edit them, and export results.

---

## Example Input

An example input file is included under `pipeline/example_input.csv`:

```csv
Artist Name,Artwork
ABRAHAMS (Mej. Anna),Tulpen
ABRAHAMS (Mej. Anna),Pensées
AKKERINGA (Jan),In 't Duin
ALMA TADEMA (Mrs Laura),Well employed
```

This allows you to immediately test the pipeline without uploading your own data.

---

## 📄 Requirements

All required packages are listed in `requirements.txt`. Key libraries:
- `sentence-transformers`
- `scikit-learn` (via `joblib`)
- `spacy`
- `streamlit`

---

## 🎥 Demo Video

Watch a short demo of the tagging tool in action:

[▶️ Watch the video](https://drive.google.com/file/d/1ADH8aDXvNWzVFxZ-QoGr_0MXIhfTh3zg/view?usp=sharing)

---

## ✉️ Contact

**Maria Elpiniki Zafeiraki**  
[LinkedIn](https://www.linkedin.com/in/marnikzaf) | [marnikzaf@gmail.com](mailto:marnikzaf@gmail.com)

---

## 📝 License

This project is provided for academic purposes. Please contact me if you intend to reuse or adapt it.