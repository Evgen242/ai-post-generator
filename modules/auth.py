"""
Модуль авторизации
"""
import streamlit as st
from modules.database import (
    register_user as db_register,
    login_user as db_login,
    get_user_by_id
)

def init_auth_interface():
    """Интерфейс авторизации в боковой панели"""
    
    if not st.session_state.user:
        menu = st.radio("Меню", ["Вход", "Регистрация"])
        
        if menu == "Регистрация":
            st.subheader("📝 Регистрация")
            username = st.text_input("Логин (мин. 3 символа)")
            email = st.text_input("Email (необязательно)")
            password = st.text_input("Пароль (мин. 4 символа)", type="password")
            confirm = st.text_input("Подтвердите пароль", type="password")
            
            # Выбор языка
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
                    user_id, msg = db_register(username, password, email, lang_code)
                    if user_id:
                        st.success("✅ Регистрация успешна! Теперь войдите")
                    else:
                        st.error(f"❌ {msg}")
        
        else:  # Вход
            st.subheader("🔑 Вход")
            username = st.text_input("Логин")
            password = st.text_input("Пароль", type="password")
            
            if st.button("Войти", use_container_width=True):
                user = db_login(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Неверный логин или пароль")
    
    else:
        # Отображаем информацию о пользователе
        st.success(f"👋 Привет, {st.session_state.user['username']}!")
        st.metric("💰 Кредиты", st.session_state.user.get('credits', 10))
        
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.user = None
            st.rerun()

def get_user_stats(user_id):
    """Получение статистики пользователя"""
    user = get_user_by_id(user_id)
    return {
        'total_posts': user.get('total_posts', 0) if user else 0,
        'credits': user.get('credits', 0) if user else 0
    }
