from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_similarity(sentences1, sentences2):
    if not isinstance(sentences1, list) or not isinstance(sentences2, list):
        raise ValueError("Ambele argumente trebuie să fie liste de propoziții.")
        
    if not sentences1 or not sentences2:
        raise ValueError("Listele de propoziții nu trebuie să fie goale.")
    
    if all(len(s.strip()) == 0 for s in sentences1) or all(len(s.strip()) == 0 for s in sentences2):
        logger.warning("Una dintre liste conține doar propoziții goale.")
        return {"similarities": [], "overall_score": 0.0}
    
    sentences1 = [s for s in sentences1 if len(s.strip()) > 5]
    sentences2 = [s for s in sentences2 if len(s.strip()) > 5]
    
    if not sentences1 or not sentences2:
        logger.warning("După filtrare, una dintre liste a rămas goală.")
        return {"similarities": [], "overall_score": 0.0}
        
    try:
        if len(sentences1) > 100:
            logger.info(f"Limitând documentul 1 de la {len(sentences1)} la 100 propoziții")
            sentences1 = sentences1[:100]
        if len(sentences2) > 100:
            logger.info(f"Limitând documentul 2 de la {len(sentences2)} la 100 propoziții")
            sentences2 = sentences2[:100]
        
        all_sentences = sentences1 + sentences2
        vectorizer = TfidfVectorizer(min_df=1, stop_words=None)
        tfidf_matrix = vectorizer.fit_transform(all_sentences)
        
        doc1_vectors = tfidf_matrix[:len(sentences1)]
        doc2_vectors = tfidf_matrix[len(sentences1):]
        
        similarities = []
        similarity_threshold = 0.6
        similarity_matrix = cosine_similarity(doc1_vectors, doc2_vectors)
        
        total_match_score = 0
        matched_sentences_doc1 = set()
        
        for i in range(len(sentences1)):
            best_match_score = 0
            best_match_idx = -1
            
            for j in range(len(sentences2)):
                score = similarity_matrix[i, j]
                if score > similarity_threshold:
                    len_ratio = min(len(sentences1[i]), len(sentences2[j])) / max(len(sentences1[i]), len(sentences2[j]))
                    if len_ratio > 0.5 and score > best_match_score:
                        best_match_score = score
                        best_match_idx = j
            
            if best_match_idx >= 0:
                matched_sentences_doc1.add(i)
                similarities.append({
                    "sentence_doc1": sentences1[i],
                    "sentence_doc2": sentences2[best_match_idx],
                    "similarity": round(float(best_match_score), 3)
                })
                total_match_score += best_match_score
        
        overall_similarity_score = 0.0
        if len(sentences1) > 0:
            if len(matched_sentences_doc1) > 0:
                match_percentage = len(matched_sentences_doc1) / len(sentences1)
                avg_match_score = total_match_score / len(matched_sentences_doc1)
                overall_similarity_score = match_percentage * avg_match_score
            overall_similarity_score = round(overall_similarity_score * 100, 1)
        
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        if len(similarities) > 20:
            similarities = similarities[:20]
            
        return {
            "similarities": similarities,
            "overall_score": overall_similarity_score
        }
        
    except Exception as e:
        logger.error(f"Eroare în compute_similarity: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"similarities": [], "overall_score": 0.0}
