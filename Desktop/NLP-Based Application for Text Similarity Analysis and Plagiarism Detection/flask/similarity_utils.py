import logging
import unicodedata
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

_vectorizer_cache = {}
_normalized_text_cache = {}

@lru_cache(maxsize=10000)
def normalize_text_cached(text):
    """Versiune cache-uită a normalizării textului pentru texte scurte"""
    if len(text) > 1000: 
        return normalize_text_direct(text)
    return normalize_text_direct(text)

def normalize_text_direct(text):
    """Normalizare optimizată fără cache pentru texte lungi"""
    if text.isascii():
        text = re.sub(r'[^\w\s]', '', text)
        return text.lower().strip()
    else:
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore').decode("utf-8")
        text = re.sub(r'[^\w\s]', '', text)
        return text.lower().strip()

def normalize_text(text):
    """Wrapper pentru normalizare cu cache inteligent"""
    if len(text) <= 1000:
        return normalize_text_cached(text)
    return normalize_text_direct(text)

def preprocess_sentences(sentences, min_length=20):
    """Preprocessing optimizat cu filtrare timpurie"""
    valid_sentences = []
    normalized = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < min_length:  
            continue
            
        norm = normalize_text(sentence)
        if len(norm.split()) < 3:
            continue
            
        valid_sentences.append(sentence)
        normalized.append(norm)
    
    return valid_sentences, normalized

def compute_similarity_optimized(sentences1, sentences2, min_similarity=0.2, max_comparisons=1000):
    """Versiune optimizată cu limitări inteligente"""
    if not isinstance(sentences1, list) or not isinstance(sentences2, list):
        raise ValueError("Ambele argumente trebuie să fie liste de propoziții.")

    if not sentences1 or not sentences2:
        logger.warning("Una dintre liste este goală.")
        return {"similarities": [], "overall_score": 0.0}

    valid_sentences1, norm_sentences1 = preprocess_sentences(sentences1)
    valid_sentences2, norm_sentences2 = preprocess_sentences(sentences2)

    if not valid_sentences1 or not valid_sentences2:
        logger.warning("Nu există propoziții valide după preprocessing.")
        return {"similarities": [], "overall_score": 0.0}

    logger.debug(f"După preprocessing: {len(valid_sentences1)} vs {len(valid_sentences2)} propoziții")

    if len(valid_sentences1) * len(valid_sentences2) > max_comparisons:
        valid_sentences1, norm_sentences1 = select_representative_sentences(
            valid_sentences1, norm_sentences1, max_comparisons // len(valid_sentences2)
        )
        valid_sentences2, norm_sentences2 = select_representative_sentences(
            valid_sentences2, norm_sentences2, max_comparisons // len(valid_sentences1)
        )
        logger.debug(f"Limitat la: {len(valid_sentences1)} vs {len(valid_sentences2)} propoziții")

    try:
        vectorizer = TfidfVectorizer(
            min_df=1,
            max_df=0.95, 
            stop_words='english',  
            ngram_range=(1, 4),
            max_features=3000,  
            token_pattern=r'\b\w{2,}\b',  
            strip_accents='ascii' 
        )

        all_sentences = norm_sentences1 + norm_sentences2
        tfidf_matrix = vectorizer.fit_transform(all_sentences)
        
        tfidf1 = tfidf_matrix[:len(norm_sentences1)]
        tfidf2 = tfidf_matrix[len(norm_sentences1):]

        if tfidf1.shape[0] < tfidf2.shape[0]:
            sim_matrix = cosine_similarity(tfidf1, tfidf2)
        else:
            sim_matrix = cosine_similarity(tfidf2, tfidf1).T

        similarities = extract_similarities_optimized(
            valid_sentences1, valid_sentences2, sim_matrix, min_similarity
        )

        logger.debug(f"Găsite {len(similarities)} similarități")

        if similarities:
            scores = [s["similarity_score"] for s in similarities]
            overall_score = float(np.mean(scores))
        else:
            overall_score = 0.0

        return {
            "similarities": similarities[:50],  
            "overall_score": overall_score
        }

    except Exception as e:
        logger.error(f"Eroare în calculul similarității: {e}")
        return {"similarities": [], "overall_score": 0.0}

def select_representative_sentences(sentences, normalized, max_count):
    """Selectează cele mai reprezentative propoziții pentru analiză"""
    if len(sentences) <= max_count:
        return sentences, normalized
    
    paired = list(zip(sentences, normalized))
    paired.sort(key=lambda x: len(x[1].split()), reverse=True)

    selected = paired[:max_count]
    return [s[0] for s in selected], [s[1] for s in selected]

def extract_similarities_optimized(sentences1, sentences2, sim_matrix, min_similarity):
    """Extragere optimizată a similarităților"""
    similarities = []

    max_indices = np.argmax(sim_matrix, axis=1)
    max_similarities = np.max(sim_matrix, axis=1)
    
    valid_mask = max_similarities >= min_similarity
    
    for i in np.where(valid_mask)[0]:
        max_idx = max_indices[i]
        max_sim = max_similarities[i]
        
        similarities.append({
            "sentence1": sentences1[i],
            "sentence2": sentences2[max_idx],
            "similarity_score": float(max_sim)
        })
    
    return sorted(similarities, key=lambda x: x["similarity_score"], reverse=True)

def compute_similarity(sentences1, sentences2, min_similarity=0.2, one_to_one=False):
    """Wrapper pentru compatibilitate cu API-ul existent"""
    return compute_similarity_optimized(sentences1, sentences2, min_similarity)

def clear_cache():
    """Curăță cache-urile pentru a elibera memoria"""
    global _vectorizer_cache, _normalized_text_cache
    _vectorizer_cache.clear()
    _normalized_text_cache.clear()
    normalize_text_cached.cache_clear()
    logger.info("Cache-uri curățate")

def get_cache_stats():
    """Returnează statistici despre utilizarea cache-ului"""
    return {
        "normalize_cache_info": normalize_text_cached.cache_info(),
        "vectorizer_cache_size": len(_vectorizer_cache),
        "normalized_text_cache_size": len(_normalized_text_cache)
    }