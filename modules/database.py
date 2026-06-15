"""
Модуль работы с PostgreSQL
"""
import psycopg2
import psycopg2.extras
from datetime import datetime
import hashlib

DB_CONFIG = {
    'host': 'localhost',
    'database': 'post_generator_db',
    'user': 'post_generator',
    'password': 'strong_password_here'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # Таблица пользователей с языком
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(200) UNIQUE,
            password VARCHAR(255) NOT NULL,
            telegram_id VARCHAR(100) UNIQUE,
            credits INTEGER DEFAULT 10,
            plan VARCHAR(50) DEFAULT 'free',
            language VARCHAR(10) DEFAULT 'ru',
            reg_ip VARCHAR(50),
            fingerprint VARCHAR(255),
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            topic TEXT NOT NULL,
            post TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reg_attempts (
            id SERIAL PRIMARY KEY,
            ip VARCHAR(50),
            fingerprint VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ База данных PostgreSQL готова")

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email=None, telegram_id=None, ip=None, fingerprint=None, language='ru'):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (username, email, password, telegram_id, reg_ip, fingerprint, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, hash_password(password), telegram_id, ip, fingerprint, language))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id, "Регистрация успешна"
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'username' in str(e):
            return None, "Пользователь с таким логином уже существует"
        elif 'email' in str(e):
            return None, "Email уже используется"
        return None, "Ошибка регистрации"
    finally:
        cur.close()
        conn.close()

def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, username, credits, plan, verified, language 
        FROM users 
        WHERE username=%s AND password=%s
    """, (username, hash_password(password)))
    user = cur.fetchone()
    if user:
        cur.execute("UPDATE users SET last_login=%s WHERE id=%s", (datetime.now(), user['id']))
        conn.commit()
    cur.close()
    conn.close()
    return user

def get_user_language(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE id=%s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else 'ru'

def update_user_language(user_id, language):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET language=%s WHERE id=%s", (language, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_credits(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT credits FROM users WHERE id=%s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else 0

def use_credit(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits - 1 WHERE id=%s AND credits > 0", (user_id,))
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return affected > 0

def add_credits(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits + %s WHERE id=%s", (amount, user_id))
    conn.commit()
    cur.close()
    conn.close()

def save_post(user_id, topic, post):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO posts (user_id, topic, post)
        VALUES (%s, %s, %s)
    """, (user_id, topic, post))
    conn.commit()
    cur.close()
    conn.close()

def get_user_posts(user_id, limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT topic, post, created_at 
        FROM posts 
        WHERE user_id=%s 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (user_id, limit))
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

def check_reg_limit(ip, fingerprint, max_per_day=3):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM reg_attempts 
        WHERE ip=%s AND created_at > NOW() - INTERVAL '24 hours'
    """, (ip,))
    ip_count = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM reg_attempts 
        WHERE fingerprint=%s AND created_at > NOW() - INTERVAL '24 hours'
    """, (fingerprint,))
    fp_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    if ip_count >= max_per_day or fp_count >= max_per_day:
        return False, f"Слишком много регистраций. Лимит: {max_per_day} в день"
    return True, "OK"

def log_reg_attempt(ip, fingerprint):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO reg_attempts (ip, fingerprint) VALUES (%s, %s)", (ip, fingerprint))
    conn.commit()
    cur.close()
    conn.close()
