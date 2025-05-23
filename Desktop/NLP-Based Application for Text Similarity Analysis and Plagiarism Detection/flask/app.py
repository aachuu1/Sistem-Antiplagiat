from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import logging
import os
import requests
import hashlib
from test_postgres import save_to_db, create_user, get_document_content, authenticate_user, get_user_by_id
from similarity_utils import compute_similarity
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("Director curent:", os.getcwd())
print("Calea către templates:", os.path.join(os.getcwd(), "templates"))
print("Există directorul templates?", os.path.exists(os.path.join(os.getcwd(), "templates")))
print("Există fișierul index.html?", os.path.exists(os.path.join(os.getcwd(), "templates", "index.html")))

app = Flask(__name__)
CORS(app)  

# Configurare session
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

def login_required(f):
    """Decorator pentru rutele care necesită autentificare"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({"error": "Autentificare necesară"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    """Hashuiește parola folosind SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

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

# Rute pentru autentificare
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not email or not password:
        error_msg = "Toate câmpurile sunt obligatorii!"
        if request.is_json:
            return jsonify({"error": error_msg}), 400
        return render_template('register.html', error=error_msg)
    
    if len(password) < 6:
        error_msg = "Parola trebuie să aibă cel puțin 6 caractere!"
        if request.is_json:
            return jsonify({"error": error_msg}), 400
        return render_template('register.html', error=error_msg)
    
    try:
        user_id = create_user(username, email, hash_password(password))
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            logger.info(f"Utilizator nou înregistrat: {username} (ID: {user_id})")
            
            if request.is_json:
                return jsonify({"message": "Cont creat cu succes!", "user_id": user_id}), 201
            return redirect(url_for('index'))
        else:
            error_msg = "Username-ul sau email-ul există deja!"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template('register.html', error=error_msg)
    except Exception as e:
        logger.error(f"Eroare la înregistrare: {e}")
        error_msg = "Eroare la crearea contului!"
        if request.is_json:
            return jsonify({"error": error_msg}), 500
        return render_template('register.html', error=error_msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        error_msg = "Username și parola sunt obligatorii!"
        if request.is_json:
            return jsonify({"error": error_msg}), 400
        return render_template('login.html', error=error_msg)
    
    try:
        user_id = authenticate_user(username, hash_password(password))
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            logger.info(f"Utilizator autentificat: {username} (ID: {user_id})")
            
            if request.is_json:
                return jsonify({"message": "Autentificare reușită!", "user_id": user_id}), 200
            return redirect(url_for('index'))
        else:
            error_msg = "Username sau parolă incorectă!"
            if request.is_json:
                return jsonify({"error": error_msg}), 401
            return render_template('login.html', error=error_msg)
    except Exception as e:
        logger.error(f"Eroare la autentificare: {e}")
        error_msg = "Eroare la autentificare!"
        if request.is_json:
            return jsonify({"error": error_msg}), 500
        return render_template('login.html', error=error_msg)

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"Utilizator delogat: {username}")
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    user_info = get_user_by_id(session['user_id'])
    if not user_info:
        session.clear()
        return redirect(url_for('login'))
    return render_template('profile.html', user=user_info)

# Rute existente cu autentificare
@app.route('/upload', methods=['POST'])
@login_required
def upload_multiple_files():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "Nu au fost trimise fișiere!"}), 400

    user_id = session['user_id']
    saved = []
    for file in files:
        if not file or not file.filename:
            continue
        try:
            content = file.read().decode(request.form.get('encoding', 'utf-8'), errors='ignore')
            
            logger.debug(f"Conținut fișier '{file.filename}': {content[:100]}..." if content else "Conținut gol")
            
            save_to_db(file.filename, content, user_id)
            saved.append(file.filename)
        except Exception as e:
            logger.error(f"Eroare la {file.filename}: {e}")
    
    logger.info(f"Utilizatorul {session['username']} a încărcat {len(saved)} fișiere")
    return jsonify({"message": "Fișiere încărcate", "saved_files": saved}), 201

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_document():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"error": "Nu a fost încărcat niciun fișier!"}), 400

    user_id = session['user_id']
    
    try:
        content = file.read().decode(request.form.get('encoding', 'utf-8'), errors='ignore')
        logger.debug(f"Analizez fișierul: {file.filename}, lungime: {len(content)} caractere pentru utilizatorul {session['username']}")
    except Exception as e:
        logger.error(f"Eroare la citirea fișierului: {e}")
        return jsonify({"error": "Fișier text invalid!"}), 415

    if not content or len(content.strip()) == 0:
        return jsonify({"error": "Fișierul este gol!"}), 400

    sentences = [s.strip() for s in content.split('.') if s.strip()]
    logger.debug(f"Număr de propoziții în document: {len(sentences)}")

    key_phrases = sorted([s for s in sentences if len(s.split()) > 10], 
                        key=lambda x: len(x.split()), 
                        reverse=True)[:3]
    
    logger.debug(f"Fraze-cheie extrase: {len(key_phrases)}")
    for i, phrase in enumerate(key_phrases):
        logger.debug(f"Frază {i+1}: {phrase[:100]}...")

    if not key_phrases:
        key_phrases = [s for s in sentences if len(s.split()) > 5][:3]
        logger.debug(f"Folosesc fraze mai scurte: {len(key_phrases)}")

    external_snippets = []
    for phrase in key_phrases:
        search_phrase = ' '.join(phrase.split()[:10])
        snippets = google_search(search_phrase)
        external_snippets.extend(snippets)

    logger.debug(f"Total snippets externe: {len(external_snippets)}")

    external_sents = []
    for snippet in external_snippets:
        for sent in snippet.split('.'):
            sent = sent.strip()
            if len(sent.split()) > 3:
                external_sents.append(sent)
    
    logger.debug(f"Total propoziții externe: {len(external_sents)}")
    
    your_sents = [s.strip() for s in content.replace('\n',' ').split('.') if s.strip()]
    
    if not external_sents:
        logger.warning("Nu s-au găsit rezultate externe pentru analiză.")
        ext_sim = {"similarities": [], "overall_score": 0.0}
    else:
        ext_sim = compute_similarity(your_sents, external_sents, min_similarity=0.2)

    # Obține doar documentele utilizatorului curent
    existing_docs = get_document_content(user_id)
    logger.debug(f"Documente existente pentru utilizator: {len(existing_docs)}")
    
    internal_results = []
    overall_internal = 0.0
    
    for doc in existing_docs:
        if doc['title'] == file.filename:
            logger.debug(f"Ignorăm comparația cu același document: {doc['title']}")
            continue
            
        logger.debug(f"Comparăm cu documentul: {doc['title']}")
        doc_sents = [s.strip() for s in doc['content'].replace('\n',' ').split('.') if s.strip()]
        
        if not doc_sents:
            logger.warning(f"Documentul {doc['title']} nu conține propoziții valide.")
            continue
            
        try:
            sim = compute_similarity(doc_sents, your_sents, min_similarity=0.2)
            
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
    
    logger.info(f"Analiză finalizată pentru {session['username']}: {result['overall_external_similarity']} (extern), {result['overall_internal_similarity']} (intern)")
    
    return jsonify(result), 200

@app.route('/test_google', methods=['GET'])
@login_required
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

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)