import psycopg2
from psycopg2 import pool

# SQL pentru crearea tabelelor
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

# Crearea unui pool de conexiuni la baza de date
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min, max connections
    dbname="plagiarism_checker",
    user="postgres",
    password="sefumeu09",
    host="localhost",
    port="5432"
)

def get_db_connection():
    """Obţine o conexiune din pool"""
    return connection_pool.getconn()

def close_db_connection(conn):
    """Returnează conexiunea în pool"""
    connection_pool.putconn(conn)

def init_db():
    """Iniţializează baza de date (crează tabelele)"""
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

def create_test_user():
    """Creează un utilizator de test (dacă nu există deja)"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Şterge utilizatorul de test dacă există
        cur.execute("DELETE FROM users WHERE username = 'test_user'")
        conn.commit()

        # Verifică dacă utilizatorul există deja
        cur.execute("SELECT id FROM users WHERE username = 'test_user'")
        user = cur.fetchone()
        if user is None:
            # Adaugă utilizatorul de test dacă nu există
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                ('test_user', 'test@example.com', 'dummy_password_hash')
            )
            user_id = cur.fetchone()[0]
            conn.commit()
        else:
            user_id = user[0]
        return user_id
    except Exception as e:
        print(f"Eroare la crearea utilizatorului test: {e}")
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
    except Exception as e:
        print(f"Eroare la salvarea documentului: {e}")
        conn.rollback()
    finally:
        cur.close()
        close_db_connection(conn)

def get_document_content():
    """Obţine titlurile și conținutul documentelor din baza de date"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title, content FROM documents")
        documents = [{"title": row[0], "content": row[1]} for row in cur.fetchall()]
        return documents
    except Exception as e:
        print(f"Eroare la obţinerea documentelor: {e}")
        return []
    finally:
        cur.close()
        close_db_connection(conn)

if __name__ == "__main__":
    init_db()
