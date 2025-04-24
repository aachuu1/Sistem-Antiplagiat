import psycopg2

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

def init_db():
    conn = psycopg2.connect(
        dbname="plagiarism_checker",
        user="postgres",
        password="sefumeu09",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute(SQL)
    conn.commit()
    cur.close()
    conn.close()
    print("Tabele create cu succes!")

def create_test_user():
    try:
        conn = psycopg2.connect(
            dbname="plagiarism_checker",
            user="postgres",
            password="sefumeu09",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE username = 'test_user'")
        conn.commit()
        cur.execute("SELECT id FROM users WHERE username = 'test_user'")
        user = cur.fetchone()
        if user is None:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                ('test_user', 'test@example.com', 'dummy_password_hash')
            )
            user_id = cur.fetchone()[0]
            conn.commit()
        else:
            user_id = user[0]

        cur.close()
        conn.close()
        return user_id
    except Exception as e:
        print(f"Eroare: {e}")
        return None


def save_to_db(title, content, user_id):
    conn = psycopg2.connect(
        dbname="plagiarism_checker",
        user="postgres",
        password="sefumeu09",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (user_id, title, content) VALUES (%s, %s, %s)",
        (user_id, title, content)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_document_content():
    conn = psycopg2.connect(
        dbname="plagiarism_checker",
        user="postgres",
        password="sefumeu09",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("SELECT title, content FROM documents")
    documents = [{"title": row[0], "content": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return documents

if __name__ == "__main__":
    init_db()