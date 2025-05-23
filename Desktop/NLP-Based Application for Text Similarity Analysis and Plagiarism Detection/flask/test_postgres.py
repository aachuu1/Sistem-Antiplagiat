import psycopg2
from psycopg2 import pool
import logging

logger = logging.getLogger(__name__)

SQL = """
CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    username       TEXT   UNIQUE NOT NULL,
    email          TEXT   UNIQUE NOT NULL,
    password_hash  TEXT   NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title        TEXT       NOT NULL,
    content      TEXT       NOT NULL,
    uploaded_at  TIMESTAMP  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processed_sentences (
    id            SERIAL PRIMARY KEY,
    document_id   INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sentence_idx  INTEGER NOT NULL,
    sentence      TEXT    NOT NULL,
    UNIQUE(document_id, sentence_idx)
);

CREATE TABLE IF NOT EXISTS plagiarism_reports (
    id           SERIAL PRIMARY KEY,
    document_id  INTEGER   NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    score        REAL      NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suspicious_passages (
    id               SERIAL  PRIMARY KEY,
    report_id        INTEGER NOT NULL REFERENCES plagiarism_reports(id) ON DELETE CASCADE,
    sentence_id      INTEGER NOT NULL REFERENCES processed_sentences(id) ON DELETE CASCADE,
    similar_doc_id   INTEGER NOT NULL REFERENCES documents(id),
    similarity_score REAL    NOT NULL,
    snippet_source   TEXT    NOT NULL,
    snippet_target   TEXT    NOT NULL
);
"""

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    dbname="plagiarism_checker",
    user="postgres",
    password="sefumeu09",
    host="localhost",
    port="5432"
)

def get_db_connection():
    """Obține o conexiune din pool"""
    return connection_pool.getconn()

def close_db_connection(conn):
    """Returnează conexiunea în pool"""
    connection_pool.putconn(conn)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(SQL)
        conn.commit()
        print("Tabele create cu succes!")
    except Exception as e:
        print(f"Eroare la crearea tabelelor: {e}")
        conn.rollback()
    finally:
        cur.close()
        close_db_connection(conn)

def create_user(username, email, password_hash):
    """Creează un utilizator nou și returnează ID-ul acestuia"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, email, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Utilizator nou creat: {username} (ID: {user_id})")
        return user_id
    except psycopg2.IntegrityError as e:
        logger.warning(f"Utilizatorul {username} sau email-ul {email} există deja")
        conn.rollback()
        return None
    except Exception as e:
        logger.error(f"Eroare la crearea utilizatorului: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        close_db_connection(conn)

def authenticate_user(username, password_hash):
    """Autentifică utilizatorul și returnează ID-ul acestuia"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM users WHERE username = %s AND password_hash = %s",
            (username, password_hash)
        )
        result = cur.fetchone()
        if result:
            user_id = result[0]
            logger.info(f"Autentificare reușită pentru {username} (ID: {user_id})")
            return user_id
        else:
            logger.warning(f"Încercare de autentificare eșuată pentru {username}")
            return None
    except Exception as e:
        logger.error(f"Eroare la autentificare: {e}")
        return None
    finally:
        cur.close()
        close_db_connection(conn)

def get_user_by_id(user_id):
    """Obține informațiile utilizatorului după ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = %s",
            (user_id,)
        )
        result = cur.fetchone()
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "created_at": result[3]
            }
        return None
    except Exception as e:
        logger.error(f"Eroare la obținerea utilizatorului: {e}")
        return None
    finally:
        cur.close()
        close_db_connection(conn)

def get_user_by_username(username):
    """Obține informațiile utilizatorului după username"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username, email, created_at FROM users WHERE username = %s",
            (username,)
        )
        result = cur.fetchone()
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "created_at": result[3]
            }
        return None
    except Exception as e:
        logger.error(f"Eroare la obținerea utilizatorului: {e}")
        return None
    finally:
        cur.close()
        close_db_connection(conn)

def create_test_user():
    """Creează un utilizator de test (păstrat pentru compatibilitate)"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Verifică dacă utilizatorul de test există deja
        cur.execute("SELECT id FROM users WHERE username = 'test_user'")
        user = cur.fetchone()
        if user is None:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                ('test_user', 'test@example.com', 'dummy_password_hash')
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Utilizator de test creat cu ID: {user_id}")
        else:
            user_id = user[0]
            logger.info(f"Utilizator de test există deja cu ID: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Eroare la crearea utilizatorului test: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        close_db_connection(conn)

def save_to_db(title, content, user_id):
    """Salvează un document în baza de date"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO documents (user_id, title, content) VALUES (%s, %s, %s)",
            (user_id, title, content)
        )
        conn.commit()
        logger.info(f"Document salvat: {title} pentru utilizatorul {user_id}")
    except Exception as e:
        logger.error(f"Eroare la salvarea documentului: {e}")
        conn.rollback()
    finally:
        cur.close()
        close_db_connection(conn)

def get_document_content(user_id=None):
    """Obține conținutul documentelor (pentru un utilizator specific sau toate)"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if user_id:
            cur.execute("SELECT title, content FROM documents WHERE user_id = %s", (user_id,))
        else:
            cur.execute("SELECT title, content FROM documents")
        
        documents = [{"title": row[0], "content": row[1]} for row in cur.fetchall()]
        logger.debug(f"Obținute {len(documents)} documente" + (f" pentru utilizatorul {user_id}" if user_id else ""))
        return documents
    except Exception as e:
        logger.error(f"Eroare la obținerea documentelor: {e}")
        return []
    finally:
        cur.close()
        close_db_connection(conn)

def get_user_documents(user_id):
    """Obține toate documentele unui utilizator cu informații suplimentare"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, title, uploaded_at FROM documents WHERE user_id = %s ORDER BY uploaded_at DESC",
            (user_id,)
        )
        documents = []
        for row in cur.fetchall():
            documents.append({
                "id": row[0],
                "title": row[1],
                "uploaded_at": row[2]
            })
        return documents
    except Exception as e:
        logger.error(f"Eroare la obținerea documentelor utilizatorului: {e}")
        return []
    finally:
        cur.close()
        close_db_connection(conn)

def delete_document(document_id, user_id):
    """Șterge un document (doar dacă aparține utilizatorului)"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM documents WHERE id = %s AND user_id = %s",
            (document_id, user_id)
        )
        deleted_count = cur.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Document {document_id} șters de utilizatorul {user_id}")
            return True
        else:
            logger.warning(f"Nu s-a putut șterge documentul {document_id} pentru utilizatorul {user_id}")
            return False
    except Exception as e:
        logger.error(f"Eroare la ștergerea documentului: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        close_db_connection(conn)

if __name__ == "__main__":
    init_db()