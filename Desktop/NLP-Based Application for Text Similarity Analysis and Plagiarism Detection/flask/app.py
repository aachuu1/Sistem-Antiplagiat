from flask import Flask, request, jsonify
import logging
from test_postgres import save_to_db, create_test_user, get_document_content
from similarity_utils import compute_similarity

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

user_id = create_test_user()
logger.info(f"Aplicație inițializată cu user_id: {user_id}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nu a fost încărcat niciun fișier!"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Fișierul nu are un nume!"}), 400
        
    try:
        content = file.read().decode('utf-8')
        logger.debug(f"Fișier încărcat: {file.filename}, mărime: {len(content)} caractere")
    except UnicodeDecodeError:
        return jsonify({"error": "Fișierul nu este un fișier text valid!"}), 400
    
    save_to_db(file.filename, content, user_id)
    return jsonify({"message": f'Conținutul fișierului a fost salvat cu succes: {file.filename}'})

@app.route('/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({"error": "Nu a fost încărcat niciun fișier!"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Fișierul nu are un nume!"}), 400
    
    try:
        content = file.read().decode('utf-8')
        logger.debug(f"Document pentru analiză: {file.filename}, mărime: {len(content)} caractere")
    except UnicodeDecodeError:
        return jsonify({"error": "Fișierul nu este un fișier text valid!"}), 400
    
    existing_docs = get_document_content()
    logger.debug(f"Număr de documente găsite în baza de date: {len(existing_docs)}")
    
    if not existing_docs:
        return jsonify({
            "message": "Nu există documente în baza de date pentru comparație!",
            "results": []
        })
    
    results = []
    overall_max_score = 0.0
    
    for doc in existing_docs:
        logger.debug(f"Comparare cu documentul: {doc['title']}, mărime: {len(doc['content'])} caractere")
        
        doc_content = doc['content'].replace('\n', ' ')
        new_content = content.replace('\n', ' ')
        
        doc_sentences = [s.strip() for s in doc_content.split('.') if s.strip()]
        new_doc_sentences = [s.strip() for s in new_content.split('.') if s.strip()]
        
        logger.debug(f"Număr de propoziții extrase - document existent: {len(doc_sentences)}")
        logger.debug(f"Număr de propoziții extrase - document nou: {len(new_doc_sentences)}")
        
        if len(doc_sentences) == 0 or len(new_doc_sentences) == 0:
            logger.warning(f"Document fără propoziții valide: {doc['title'] if len(doc_sentences) == 0 else 'document nou'}")
            continue
        
        try:
            similarity_result = compute_similarity(doc_sentences, new_doc_sentences)
            doc_similarities = similarity_result["similarities"]
            doc_overall_score = similarity_result["overall_score"]
            
            if doc_similarities:
                logger.info(f"Găsite {len(doc_similarities)} similarități cu documentul: {doc['title']} (Similaritate globală: {doc_overall_score}%)")
                results.append({
                    "compared_with": doc['title'],
                    "similarities": doc_similarities,
                    "similarity_percentage": doc_overall_score
                })
                
                if doc_overall_score > overall_max_score:
                    overall_max_score = doc_overall_score
            else:
                logger.info(f"Nu s-au găsit similarități cu documentul: {doc['title']}")
        except Exception as e:
            logger.error(f"Eroare la calcularea similarității cu documentul {doc['title']}: {str(e)}")
    
    results.sort(key=lambda x: x["similarity_percentage"], reverse=True)
    
    return jsonify({
        "message": "Document analizat cu succes!",
        "overall_similarity": overall_max_score,
        "results": results
    })

if __name__ == '__main__':
    app.run(debug=True)
