"""
Модуль работы с PostgreSQL
"""
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import hashlib
import secrets
import json

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.17.0.1'),
    'database': os.getenv('DB_NAME', 'post_generator_db'),
    'user': os.getenv('DB_USER', 'post_generator'),
    'password': os.getenv('DB_PASSWORD', 'post_generator_123')
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(200) UNIQUE,
            password VARCHAR(255) NOT NULL,
            salt VARCHAR(64) NOT NULL,
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
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            notification_enabled BOOLEAN DEFAULT TRUE,
            language VARCHAR(10) DEFAULT 'ru',
            PRIMARY KEY (user_id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_avatars (
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            avatar_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id)
        )
    """)
    
    conn.commit()
    conn.close()

def hash_password(password):
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt, hash_obj.hex()

def verify_password(password, salt, stored_hash):
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hash_obj.hex() == stored_hash

# === ОСНОВНЫЕ ФУНКЦИИ ===

def register_user(username, password, email=None, telegram_id=None, ip=None, fingerprint=None, language='ru'):
    conn = get_connection()
    cur = conn.cursor()
    try:
        salt, password_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (username, email, password, salt, telegram_id, reg_ip, fingerprint, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, password_hash, salt, telegram_id, ip, fingerprint, language))
        user_id = cur.fetchone()[0]
        cur.execute("INSERT INTO user_settings (user_id, language) VALUES (%s, %s)", (user_id, language))
        cur.execute("INSERT INTO user_avatars (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        conn.commit()
        return user_id, "Регистрация успешна!"
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "username" in str(e):
            return None, "Пользователь с таким логином уже существует"
        elif "email" in str(e):
            return None, "Пользователь с таким email уже существует"
        elif "telegram_id" in str(e):
            return None, "Этот Telegram ID уже зарегистрирован"
        return None, f"Ошибка регистрации: {e}"
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    conn.close()
    if not user:
        return None
    if verify_password(password, user['salt'], user['password']):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))
        conn.commit()
        conn.close()
        return dict(user)
    return None

def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_credits(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT credits FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 0

def use_credit(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET credits = credits - 1 WHERE id = %s AND credits > 0 RETURNING credits",
        (user_id,)
    )
    result = cur.fetchone()
    conn.commit()
    conn.close()
    return result[0] if result else None

def add_credits(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET credits = credits + %s WHERE id = %s RETURNING credits",
        (amount, user_id)
    )
    new_credits = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_credits

def update_user_credits(user_id, amount):
    return add_credits(user_id, amount)

def save_post(user_id, topic, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (user_id, topic, post) VALUES (%s, %s, %s) RETURNING id",
        (user_id, topic, content)
    )
    post_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return post_id

def create_post(user_id, topic, content):
    return save_post(user_id, topic, content)

def get_user_posts(user_id, limit=10):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit)
    )
    posts = cur.fetchall()
    conn.close()
    return [dict(post) for post in posts]

def get_user_language(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 'ru'

def update_user_language(user_id, language):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET language = %s WHERE id = %s",
        (language, user_id)
    )
    cur.execute(
        "UPDATE user_settings SET language = %s WHERE user_id = %s",
        (language, user_id)
    )
    conn.commit()
    conn.close()

def check_reg_limit(ip, fingerprint, max_per_day=5):
    """Check registration limit"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM reg_attempts 
        WHERE (ip = %s OR fingerprint = %s) 
        AND created_at > NOW() - INTERVAL '1 day'
    """, (ip, fingerprint))
    count = cur.fetchone()[0]
    conn.close()
    if count >= max_per_day:
        return False, "Превышен лимит попыток регистрации (максимум 5 в день)"
    return True, "OK"

def log_reg_attempt(ip, fingerprint):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reg_attempts (ip, fingerprint) VALUES (%s, %s)",
        (ip, fingerprint)
    )
    conn.commit()
    conn.close()

def check_reg_attempt(ip, fingerprint):
    return check_reg_limit(ip, fingerprint)

def get_user_settings(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
    settings = cur.fetchone()
    conn.close()
    return dict(settings) if settings else None

def update_user_settings(user_id, **kwargs):
    conn = get_connection()
    cur = conn.cursor()
    for key, value in kwargs.items():
        cur.execute(
            f"UPDATE user_settings SET {key} = %s WHERE user_id = %s",
            (value, user_id)
        )
    conn.commit()
    conn.close()

def get_avatar(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT avatar_data FROM user_avatars WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def save_avatar(user_id, avatar_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_avatars (user_id, avatar_data, updated_at) 
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO UPDATE 
        SET avatar_data = EXCLUDED.avatar_data, updated_at = CURRENT_TIMESTAMP
    """, (user_id, avatar_data))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, username, email, credits, plan, language, created_at, last_login FROM users ORDER BY id")
    users = cur.fetchall()
    conn.close()
    return [dict(user) for user in users]

def get_user_by_telegram(telegram_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

# Initialize database
init_db()
