import re
import hashlib
import streamlit as st
from db import (
    register_user as db_register,
    login_user as db_login,
    get_user_credits as db_get_credits,
    use_credit as db_use_credit,
    add_credits as db_add_credits,
    save_post as db_save_post,
    get_user_posts as db_get_posts,
    get_user_language as db_get_user_language,
    update_user_language as db_update_user_language,
    check_reg_limit,
    log_reg_attempt
)
import psycopg2
from db import get_connection
import os
import requests

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_client_ip():
    try:
        forwarded = st.context.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return st.context.headers.get("Remote-Addr", "unknown")
    except:
        return "unknown"

def get_user_fingerprint():
    try:
        headers = st.context.headers
        data = f"{headers.get('User-Agent', '')}_{headers.get('Accept-Language', '')}"
        return hashlib.sha256(data.encode()).hexdigest()
    except:
        return "unknown"

def check_is_bot(telegram_id):
    """Проверяет, является ли аккаунт ботом через Telegram API"""
    if not telegram_id:
        return False, "OK"
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    if not bot_token:
        return False, "OK"
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getChat"
        response = requests.post(url, json={"chat_id": telegram_id}, timeout=5)
        data = response.json()
        
        if data.get("ok"):
            is_bot = data.get("result", {}).get("is_bot", False)
            if is_bot:
                return True, "Боты не могут регистрироваться"
            return False, "OK"
        else:
            return False, "OK"
    except Exception:
        return False, "OK"

def register_user_with_bot_check(username, password, email, telegram_id, language='ru'):
    """Регистрация с проверкой на бота"""
    
    if telegram_id:
        is_bot, msg = check_is_bot(telegram_id)
        if is_bot:
            return None, "❌ Регистрация ботов запрещена"
    
    # Вызываем обычную регистрацию
    return register_user(username, password, email, telegram_id, language)

def register_user(username, password, email=None, telegram_id=None, language='ru'):
    if len(username) < 3:
        return None, "Логин должен быть минимум 3 символа"
    if len(password) < 4:
        return None, "Пароль должен быть минимум 4 символа"
    if email and not validate_email(email):
        return None, "Неверный формат email"
    
    ip = get_client_ip()
    fingerprint = get_user_fingerprint()
    
    is_ok, msg = check_reg_limit(ip, fingerprint)
    if not is_ok:
        return None, msg
    
    user_id, result_msg = db_register(username, password, email, telegram_id, ip, fingerprint, language)
    
    if user_id:
        log_reg_attempt(ip, fingerprint)
        return user_id, result_msg
    
    return None, result_msg

def check_telegram_id(telegram_id):
    """Проверка, не зарегистрирован ли уже этот Telegram ID"""
    if not telegram_id:
        return True, "OK"
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    
    if exists:
        return False, "Этот Telegram ID уже зарегистрирован"
    return True, "OK"

def login_user(username, password):
    return db_login(username, password)

def login_by_telegram(telegram_id):
    """Вход по Telegram ID"""
    if not telegram_id:
        return None
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, credits, plan, language FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        return {"id": user[0], "username": user[1], "credits": user[2], "plan": user[3], "language": user[4]}
    return None

def get_user_credits(user_id):
    return db_get_credits(user_id)

def use_credit(user_id):
    return db_use_credit(user_id)

def add_credits(user_id, amount):
    db_add_credits(user_id, amount)

def save_post(user_id, topic, post):
    db_save_post(user_id, topic, post)

def get_user_posts(user_id, limit=10):
    return db_get_posts(user_id, limit)

def get_user_language(user_id):
    return db_get_user_language(user_id)

def update_user_language(user_id, language):
    db_update_user_language(user_id, language)

def init_auth_interface():
    """Интерфейс авторизации для боковой панели"""
    
    if not st.session_state.get("user"):
        menu = st.radio("Меню", ["Вход", "Регистрация"])
        
        if menu == "Регистрация":
            st.subheader("📝 Регистрация")
            st.info("💡 Регистрация по Telegram ID защищает от создания нескольких аккаунтов")
            
            col1, col2 = st.columns(2)
            with col1:
                reg_type = st.radio("Способ регистрации", ["По логину", "По Telegram ID"])
            
            if reg_type == "По логину":
                username = st.text_input("Логин (мин. 3 символа)")
                email = st.text_input("Email (необязательно)")
                password = st.text_input("Пароль (мин. 4 символа)", type="password")
                confirm = st.text_input("Подтвердите пароль", type="password")
                telegram_id = None
            else:
                st.markdown("""
                🔑 **Как получить Telegram ID:**
                1. Напишите @userinfobot в Telegram
                2. Нажмите Start
                3. Скопируйте ваш ID (число)
                """)
                telegram_id = st.text_input("Ваш Telegram ID (число)", placeholder="123456789")
                username = st.text_input("Логин (мин. 3 символа)")
                password = st.text_input("Пароль (мин. 4 символа)", type="password")
                confirm = st.text_input("Подтвердите пароль", type="password")
                email = None
            
            st.markdown("---")
            st.markdown("### 🌐 Язык интерфейса")
            language = st.radio("", ["🇷🇺 Русский", "🇬🇧 English"], index=0, horizontal=True)
            lang_code = "ru" if language == "🇷🇺 Русский" else "en"
            
            if st.button("Зарегистрироваться", use_container_width=True):
                if password != confirm:
                    st.error("❌ Пароли не совпадают")
                elif len(username) < 3:
                    st.error("❌ Логин слишком короткий")
                elif len(password) < 4:
                    st.error("❌ Пароль слишком короткий")
                else:
                    # Проверяем Telegram ID
                    if telegram_id:
                        is_ok, msg = check_telegram_id(telegram_id)
                        if not is_ok:
                            st.error(f"❌ {msg}")
                            return
                    
                    user_id, msg = register_user_with_bot_check(username, password, email, telegram_id, lang_code)
                    if user_id:
                        st.success("✅ Регистрация успешна! Теперь войдите")
                    else:
                        st.error(f"❌ {msg}")
        
        else:  # Вход
            st.subheader("🔑 Вход")
            
            col1, col2 = st.columns(2)
            with col1:
                login_type = st.radio("Способ входа", ["По логину", "По Telegram ID"])
            
            if login_type == "По логину":
                username = st.text_input("Логин")
                password = st.text_input("Пароль", type="password")
                
                if st.button("Войти", use_container_width=True):
                    user = login_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("❌ Неверный логин или пароль")
            else:
                st.markdown("🔑 **Введите ваш Telegram ID**")
                st.caption("Получить ID можно у бота @userinfobot")
                telegram_id = st.text_input("Telegram ID", placeholder="123456789")
                
                if st.button("Войти по Telegram ID", use_container_width=True):
                    user = login_by_telegram(telegram_id)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("❌ Telegram ID не найден. Зарегистрируйтесь сначала")
    
    else:
        st.success(f"👋 Привет, {st.session_state.user['username']}!")
        
        # Показываем способ входа
        if st.session_state.user.get('telegram_id'):
            st.info(f"🔒 Вход по Telegram ID: да")
        
        st.metric("💰 Кредиты", st.session_state.user.get('credits', 10))
        
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.user = None
            st.rerun()

def init_auth_interface():
    """Интерфейс авторизации для боковой панели"""
    
    if not st.session_state.get("user"):
        menu = st.radio("Меню", ["Вход", "Регистрация"])
        
        # ... остальной код авторизации ...
        
    else:
        st.success(f"👋 Привет, {st.session_state.user['username']}!")
        
        # Показываем безлимит для администратора
        if st.session_state.user.get('username') == 'admin':
            st.info("👑 Администратор | Безлимитные кредиты")
            st.metric("💰 Кредиты", "∞")
        else:
            st.metric("💰 Кредиты", st.session_state.user.get('credits', 10))
        
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.user = None
            st.rerun()

def init_auth_interface():
    """Интерфейс авторизации для боковой панели"""
    
    if not st.session_state.get("user"):
        menu = st.radio("Меню", ["Вход", "Регистрация"])
        
        if menu == "Регистрация":
            st.subheader("📝 Регистрация")
            st.info("💡 Регистрация по Telegram ID защищает от создания нескольких аккаунтов")
            
            col1, col2 = st.columns(2)
            with col1:
                reg_type = st.radio("Способ регистрации", ["По логину", "По Telegram ID"])
            
            if reg_type == "По логину":
                username = st.text_input("Логин (мин. 3 символа)")
                email = st.text_input("Email (необязательно)")
                password = st.text_input("Пароль (мин. 4 символа)", type="password")
                confirm = st.text_input("Подтвердите пароль", type="password")
                telegram_id = None
            else:
                st.markdown("""
                🔑 **Как получить Telegram ID:**
                1. Напишите @userinfobot в Telegram
                2. Нажмите Start
                3. Скопируйте ваш ID (число)
                """)
                telegram_id = st.text_input("Ваш Telegram ID (число)", placeholder="123456789")
                username = st.text_input("Логин (мин. 3 символа)")
                password = st.text_input("Пароль (мин. 4 символа)", type="password")
                confirm = st.text_input("Подтвердите пароль", type="password")
                email = None
            
            st.markdown("---")
            st.markdown("### 🌐 Язык интерфейса")
            language = st.radio("", ["🇷🇺 Русский", "🇬🇧 English"], index=0, horizontal=True)
            lang_code = "ru" if language == "🇷🇺 Русский" else "en"
            
            if st.button("Зарегистрироваться", use_container_width=True):
                if password != confirm:
                    st.error("❌ Пароли не совпадают")
                elif len(username) < 3:
                    st.error("❌ Логин слишком короткий")
                elif len(password) < 4:
                    st.error("❌ Пароль слишком короткий")
                else:
                    # Проверяем Telegram ID
                    if telegram_id:
                        is_ok, msg = check_telegram_id(telegram_id)
                        if not is_ok:
                            st.error(f"❌ {msg}")
                            return
                    
                    user_id, msg = register_user_with_bot_check(username, password, email, telegram_id, lang_code)
                    if user_id:
                        st.success("✅ Регистрация успешна! Теперь войдите")
                    else:
                        st.error(f"❌ {msg}")
        
        else:  # Вход
            st.subheader("🔑 Вход")
            
            col1, col2 = st.columns(2)
            with col1:
                login_type = st.radio("Способ входа", ["По логину", "По Telegram ID"])
            
            if login_type == "По логину":
                username = st.text_input("Логин")
                password = st.text_input("Пароль", type="password")
                
                if st.button("Войти", use_container_width=True):
                    user = login_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("❌ Неверный логин или пароль")
            else:
                st.markdown("🔑 **Введите ваш Telegram ID**")
                st.caption("Получить ID можно у бота @userinfobot")
                telegram_id = st.text_input("Telegram ID", placeholder="123456789")
                
                if st.button("Войти по Telegram ID", use_container_width=True):
                    user = login_by_telegram(telegram_id)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("❌ Telegram ID не найден. Зарегистрируйтесь сначала")
    
    else:
        st.success(f"👋 Привет, {st.session_state.user['username']}!")
        
        # Показываем способ входа
        if st.session_state.user.get('telegram_id'):
            st.info(f"🔒 Вход по Telegram ID: да")
        
        st.metric("💰 Кредиты", st.session_state.user.get('credits', 10))
        
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.user = None
            st.rerun()

def check_telegram_id(telegram_id):
    """Проверка, не зарегистрирован ли уже этот Telegram ID"""
    if not telegram_id:
        return True, "OK"
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    
    if exists:
        return False, "Этот Telegram ID уже зарегистрирован"
    return True, "OK"

def login_by_telegram(telegram_id):
    """Вход по Telegram ID"""
    if not telegram_id:
        return None
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, credits, plan, language FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        return {"id": user[0], "username": user[1], "credits": user[2], "plan": user[3], "language": user[4]}
    return None
