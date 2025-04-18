import pandas as pd
import joblib
import numpy as np
import torch
import spacy
import argparse
import logging
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
from langdetect import detect

# === Logging setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

# === CONFIG ===
TITLE_COL = "Artwork"
CONF_THRESHOLD = 0.25
MAX_TAGS = 5
TOP_K = 2
SIM_THRESHOLD = 0.3
MIN_COMPONENT_LEN = 4

# === Load models ===
labse = SentenceTransformer("sentence-transformers/LaBSE")
nlp_ner = spacy.load("xx_ent_wiki_sm")
nl_nlp = spacy.load("nl_core_news_sm")
fr_nlp = spacy.load("fr_core_news_sm")


def batch_encode(texts, model, batch_size=64):
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch = texts[i:i + batch_size]
        emb = model.encode(batch)
        embeddings.extend(emb)
    return embeddings


def step1_predict(df, model_path, binarizer_path):
    logging.info("📦 Loading model and label binarizer...")
    clf = joblib.load(model_path)
    mlb = joblib.load(binarizer_path)

    df = df.dropna(subset=[TITLE_COL])
    titles = df[TITLE_COL].astype(str).tolist()
    X_test = batch_encode(titles, labse)
    Y_prob = clf.predict_proba(X_test)
    class_labels = mlb.classes_

    predicted_tags = []
    for probs in Y_prob:
        tags = [class_labels[idx] for idx, score in enumerate(probs) if score >= CONF_THRESHOLD]
        if not tags:
            top_idxs = np.argsort(probs)[-MAX_TAGS:][::-1]
            tags = [class_labels[i] for i in top_idxs]
        predicted_tags.append("; ".join(tags))

    df["Predicted_Tags"] = predicted_tags
    return df


def load_terms(en_terms_path, nl_terms_path):
    df_en = pd.read_csv(en_terms_path)
    df_nl = pd.read_csv(nl_terms_path)
    terms = pd.concat([df_en, df_nl])["term"].dropna().astype(str).tolist()
    return list(set(t.strip() for t in terms if len(t.strip()) > 3))


def step2_embedder_fallback(df, en_terms_path, nl_terms_path):
    terms = load_terms(en_terms_path, nl_terms_path)
    titles = df[TITLE_COL].astype(str).tolist()
    term_embeddings = labse.encode(terms, convert_to_tensor=True)
    title_embeddings = labse.encode(titles, convert_to_tensor=True)

    fallback_tags = []
    for i, title_emb in enumerate(title_embeddings):
        sim_scores = util.cos_sim(title_emb, term_embeddings)[0]
        top_idxs = torch.topk(sim_scores, k=TOP_K).indices
        fallback = [terms[idx] for idx in top_idxs if sim_scores[idx] >= SIM_THRESHOLD]
        fallback_tags.append("; ".join(fallback))

    df["Fallback_Tags"] = fallback_tags
    return df


def step3_ner_tags(df):
    ner_tags = []
    for text in df[TITLE_COL].astype(str):
        doc = nlp_ner(text)
        ner_tags.append("; ".join(sorted(set(ent.text.strip() for ent in doc.ents if len(ent.text.strip()) > 1))))
    df["NER_Tags"] = ner_tags
    return df


def step5_aat_expansion(df, aat_dict_path):
    aat_map = pd.read_csv(aat_dict_path)
    rkd_to_broader = (
        aat_map.set_index("rkd_term")["broader_terms"]
        .dropna().str.split("; ").to_dict()
    )
    aat_tags = []
    for _, row in df.iterrows():
        original = []
        for col in ["Predicted_Tags", "Fallback_Tags"]:
            original += [t.strip() for t in row.get(col, "").split(";") if t.strip()]
        broader = []
        for tag in original:
            broader += rkd_to_broader.get(tag.lower(), [])
        all_tags = original + broader
        aat_tags.append("; ".join(all_tags))
    df["AAT_Expanded_Tags"] = aat_tags
    return df


def merge_and_split_tags(df, en_terms_path, nl_terms_path):
    df_en = pd.read_csv(en_terms_path)
    df_nl = pd.read_csv(nl_terms_path)
    en_terms = set(df_en["term"].dropna().astype(str).str.strip().str.lower())
    nl_terms = set(df_nl["term"].dropna().astype(str).str.strip().str.lower())

    langs_nl = []
    langs_en = []

    for _, row in df.iterrows():
        all_tags = []
        for col in ["Predicted_Tags", "Fallback_Tags", "NER_Tags", "AAT_Expanded_Tags"]:
            tags = row.get(col, "")
            all_tags += [t.strip() for t in tags.split(";") if t.strip()]

        tags_nl = []
        tags_en = []
        seen_nl = set()
        seen_en = set()

        for tag in all_tags:
            norm_tag = tag.strip().lower()

            if norm_tag in nl_terms and norm_tag not in seen_nl:
                tags_nl.append(tag.strip())
                seen_nl.add(norm_tag)
            elif norm_tag in en_terms and norm_tag not in seen_en:
                tags_en.append(tag.strip())
                seen_en.add(norm_tag)
            else:
                try:
                    lang = detect(tag)
                    if lang == "nl" and norm_tag not in seen_nl:
                        tags_nl.append(tag.strip())
                        seen_nl.add(norm_tag)
                    elif lang == "en" and norm_tag not in seen_en:
                        tags_en.append(tag.strip())
                        seen_en.add(norm_tag)
                except:
                    continue

        langs_nl.append("; ".join(sorted(tags_nl)))
        langs_en.append("; ".join(sorted(tags_en)))

    df["tags NL"] = langs_nl
    df["tags EN"] = langs_en
    return df[["Artist Name", "Artwork", "Location", "tags NL", "tags EN"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    parser.add_argument("--model_path", default="labse_logreg_model.pkl")
    parser.add_argument("--binarizer_path", default="labse_label_binarizer.pkl")
    parser.add_argument("--en_terms_path", default="SUBJECT_all_terms_ENGLISH.csv")
    parser.add_argument("--nl_terms_path", default="SUBJECT_all_terms_DUTCH.csv")
    parser.add_argument("--aat_dict_path", default="rkd_aat_term_mapping.csv")

    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_file)
        df = step1_predict(df, args.model_path, args.binarizer_path)
        df = step2_embedder_fallback(df, args.en_terms_path, args.nl_terms_path)
        df = step3_ner_tags(df)
        df = step5_aat_expansion(df, args.aat_dict_path)
        df = merge_and_split_tags(df, args.en_terms_path, args.nl_terms_path)
        df.to_csv(args.output_file, index=False)
        logging.info(f"✅ Pipeline complete! Output saved to {args.output_file}")
    except Exception as e:
        logging.error(f"❌ Pipeline failed: {e}")


if __name__ == "__main__":
    main()
