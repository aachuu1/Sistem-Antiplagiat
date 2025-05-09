from flask import Flask, request, jsonify
import logging
import os
import requests
from test_postgres import save_to_db, create_test_user, get_document_content
from similarity_utils import compute_similarity
from flask_cors import CORS
from dotenv import load_dotenv

# Încarcă variabilele de mediu din .env
load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

user_id = create_test_user()
logger.info(f"Aplicație inițializată cu user_id: {user_id}")

def google_search(query, num=5):
    """Trimite o interogare la Google Custom Search API și returnează snippet-urile."""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        logger.error("GOOGLE_API_KEY sau GOOGLE_CSE_ID nu sunt configurate!")
        return []
        
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': query,
        'num': num
    }
    
    logger.debug(f"Căutare Google pentru: '{query}'")
    
    try:
        resp = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"Eroare la apelarea Google Search API: {resp.status_code} - {resp.text}")
            return []
            
        data = resp.json()
        
        # Verifică dacă avem rezultate
        if 'items' not in data or not data['items']:
            logger.warning(f"Nu s-au găsit rezultate pentru căutarea: '{query}'")
            return []
            
        snippets = [item.get('snippet', '') for item in data.get('items', [])]
        logger.debug(f"Rezultate găsite: {len(snippets)}")
        
        if snippets:
            logger.debug(f"Exemplu snippet: {snippets[0]}")
            
        return snippets
    except Exception as e:
        logger.error(f"Excepție la apel Google Search: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

@app.route('/upload', methods=['POST'])
def upload_multiple_files():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "Nu au fost trimise fișiere!"}), 400

    saved = []
    for file in files:
        if not file or not file.filename:
            continue
        try:
            content = file.read().decode(request.form.get('encoding', 'utf-8'), errors='ignore')
            
            # Debug pentru conținutul fișierului
            logger.debug(f"Conținut fișier '{file.filename}': {content[:100]}..." if content else "Conținut gol")
            
            save_to_db(file.filename, content, user_id)
            saved.append(file.filename)
        except Exception as e:
            logger.error(f"Eroare la {file.filename}: {e}")
    return jsonify({"message": "Fișiere încărcate", "saved_files": saved}), 201

@app.route('/analyze', methods=['POST'])
def analyze_document():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"error": "Nu a fost încărcat niciun fișier!"}), 400

    # Citește conținutul fișierului
    try:
        content = file.read().decode(request.form.get('encoding', 'utf-8'), errors='ignore')
        logger.debug(f"Analizez fișierul: {file.filename}, lungime: {len(content)} caractere")
    except Exception as e:
        logger.error(f"Eroare la citirea fișierului: {e}")
        return jsonify({"error": "Fișier text invalid!"}), 415

    # Verifică dacă avem conținut valid
    if not content or len(content.strip()) == 0:
        return jsonify({"error": "Fișierul este gol!"}), 400

    # 1) Analiză externă
    # Extrage câteva fraze-cheie (primele 3 fraze mai lungi)
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    logger.debug(f"Număr de propoziții în document: {len(sentences)}")

    # Sortăm propozițiile după lungime și alegem primele 3 mai lungi de 10 cuvinte
    key_phrases = sorted([s for s in sentences if len(s.split()) > 10], 
                        key=lambda x: len(x.split()), 
                        reverse=True)[:3]
    
    logger.debug(f"Fraze-cheie extrase: {len(key_phrases)}")
    for i, phrase in enumerate(key_phrases):
        logger.debug(f"Frază {i+1}: {phrase[:100]}...")

    # Dacă nu avem fraze lungi, folosim primele 3 propoziții mai lungi de 5 cuvinte
    if not key_phrases:
        key_phrases = [s for s in sentences if len(s.split()) > 5][:3]
        logger.debug(f"Folosesc fraze mai scurte: {len(key_phrases)}")

    # Căutare externă
    external_snippets = []
    for phrase in key_phrases:
        # Limitează lungimea frazei pentru căutare
        search_phrase = ' '.join(phrase.split()[:10])
        snippets = google_search(search_phrase)
        external_snippets.extend(snippets)

    logger.debug(f"Total snippets externe: {len(external_snippets)}")

    # Transformă snippet-urile în propoziții individuale
    external_sents = []
    for snippet in external_snippets:
        for sent in snippet.split('.'):
            sent = sent.strip()
            if len(sent.split()) > 3:
                external_sents.append(sent)
    
    logger.debug(f"Total propoziții externe: {len(external_sents)}")
    
    # Compară documentul tău cu cele externe
    your_sents = [s.strip() for s in content.replace('\n',' ').split('.') if s.strip()]
    
    # Verifică dacă listele nu sunt goale înainte de a le procesa
    if not external_sents:
        logger.warning("Nu s-au găsit rezultate externe pentru analiză.")
        ext_sim = {"similarities": [], "overall_score": 0.0}
    else:
        ext_sim = compute_similarity(your_sents, external_sents, min_similarity=0.2)

    # 2) Analiză internă (documente din baza de date)
    existing_docs = get_document_content()
    logger.debug(f"Documente existente în baza de date: {len(existing_docs)}")
    
    internal_results = []
    overall_internal = 0.0
    
    for doc in existing_docs:
        # Verifică dacă documentul actual nu este același cu cel încărcat
        if doc['title'] == file.filename:
            logger.debug(f"Ignorăm comparația cu același document: {doc['title']}")
            continue
            
        logger.debug(f"Comparăm cu documentul: {doc['title']}")
        doc_sents = [s.strip() for s in doc['content'].replace('\n',' ').split('.') if s.strip()]
        
        # Verifică dacă ambele liste au conținut înainte de a calcula similaritatea
        if not doc_sents:
            logger.warning(f"Documentul {doc['title']} nu conține propoziții valide.")
            continue
            
        try:
            sim = compute_similarity(doc_sents, your_sents, min_similarity=0.2)
            
            # Adăugăm rezultatul chiar dacă nu avem similarități, pentru a afișa un rezultat complet
            internal_results.append({
                "compared_with": doc['title'],
                "similarities": sim['similarities'],
                "similarity_percentage": sim['overall_score']
            })
            
            overall_internal = max(overall_internal, sim['overall_score'])
            logger.debug(f"Similaritate cu {doc['title']}: {sim['overall_score']}")
        except ValueError as e:
            logger.error(f"Eroare la calculul similarității: {e}")
            continue
        except Exception as e:
            logger.error(f"Excepție neașteptată: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue

    # 3) Construcția răspunsului
    result = {
        "message": "Analiză finalizată!",
        "overall_internal_similarity": overall_internal,
        "internal_results": sorted(internal_results, key=lambda x: x['similarity_percentage'], reverse=True),
        "overall_external_similarity": ext_sim['overall_score'],
        "external_results": ext_sim['similarities'],
        "debug_info": {
            "document_sentences": len(your_sents),
            "external_sentences": len(external_sents),
            "internal_documents": len(existing_docs),
            "key_phrases_used": len(key_phrases)
        }
    }
    
    logger.debug(f"Rezultat final: {result['overall_external_similarity']} (extern), {result['overall_internal_similarity']} (intern)")
    
    return jsonify(result), 200

@app.route('/test_google', methods=['GET'])
def test_google():
    """Endpoint de test pentru API-ul Google Search"""
    query = request.args.get('q', 'inteligenta artificiala')
    
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return jsonify({
            "error": "API_KEY sau CSE_ID nedefinite",
            "GOOGLE_API_KEY_set": bool(GOOGLE_API_KEY),
            "GOOGLE_CSE_ID_set": bool(GOOGLE_CSE_ID)
        }), 400
    
    try:
        snippets = google_search(query)
        return jsonify({
            "query": query,
            "results_count": len(snippets),
            "snippets": snippets
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "query": query
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)