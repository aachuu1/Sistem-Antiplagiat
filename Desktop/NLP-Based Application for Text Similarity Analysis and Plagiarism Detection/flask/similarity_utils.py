import logging
import unicodedata
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

def normalize_text(text):
    """
    Normalizează textul: lowercase, eliminare diacritice și semne de punctuație.
    """
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode("utf-8")
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower().strip()

def compute_similarity(sentences1, sentences2, min_similarity=0.2, one_to_one=False):
    """
    Calculează similaritatea între două liste de propoziții.
    Returnează un dicționar cu scorurile similitudinii și scorul general.

    Args:
        sentences1: Prima listă de propoziții
        sentences2: A doua listă de propoziții
        min_similarity: Pragul minim pentru a considera două propoziții similare (default: 0.2)
        one_to_one: Dacă True, nu asociază aceeași propoziție din sentences2 de mai multe ori
    """
    if not isinstance(sentences1, list) or not isinstance(sentences2, list):
        raise ValueError("Ambele argumente trebuie să fie liste de propoziții.")

    if not sentences1 or not sentences2:
        logger.warning("Una dintre liste este goală. Returnez scor de similaritate zero.")
        return {"similarities": [], "overall_score": 0.0}

    valid_sentences1 = [s for s in sentences1 if len(s.strip()) > 0]
    valid_sentences2 = [s for s in sentences2 if len(s.strip()) > 0]

    if not valid_sentences1 or not valid_sentences2:
        logger.warning("Una dintre liste conține doar propoziții goale.")
        return {"similarities": [], "overall_score": 0.0}

    logger.debug(f"Comparăm {len(valid_sentences1)} cu {len(valid_sentences2)} propoziții")
    logger.debug(f"Exemplu propoziție 1: {valid_sentences1[0][:100]}...")
    logger.debug(f"Exemplu propoziție 2: {valid_sentences2[0][:100]}...")

    try:
        # Normalizează propozițiile
        norm_sentences1 = [normalize_text(s) for s in valid_sentences1]
        norm_sentences2 = [normalize_text(s) for s in valid_sentences2]

        all_sentences = norm_sentences1 + norm_sentences2

        vectorizer = TfidfVectorizer(min_df=1, stop_words=None,
                                     ngram_range=(1, 2),
                                     max_features=5000,
                                     token_pattern=r'\b\w+\b')

        tfidf_matrix = vectorizer.fit_transform(all_sentences)
        logger.debug(f"Dimensiunea matricei TF-IDF: {tfidf_matrix.shape}")

        tfidf1 = tfidf_matrix[:len(norm_sentences1)]
        tfidf2 = tfidf_matrix[len(norm_sentences1):]

        sim_matrix = cosine_similarity(tfidf1, tfidf2)

        similarities = []
        used_indices = set()

        for i, row in enumerate(sim_matrix):
            max_idx = np.argmax(row)
            max_sim = row[max_idx]

            if max_sim >= min_similarity:
                if one_to_one and max_idx in used_indices:
                    continue
                used_indices.add(max_idx)

                similarities.append({
                    "sentence1": valid_sentences1[i],
                    "sentence2": valid_sentences2[max_idx],
                    "similarity_score": float(max_sim)
                })

        logger.debug(f"Număr de perechi de propoziții similare găsite: {len(similarities)}")

        overall_score = (sum(item["similarity_score"] for item in similarities) / len(similarities)) if similarities else 0.0
        logger.debug(f"Scor general de similaritate: {overall_score}")

        return {
            "similarities": sorted(similarities, key=lambda x: x["similarity_score"], reverse=True),
            "overall_score": overall_score
        }

    except Exception as e:
        logger.error(f"Eroare în calculul similarității: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"similarities": [], "overall_score": 0.0}
