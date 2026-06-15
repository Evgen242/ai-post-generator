"""
Административная панель
"""
import streamlit as st
from modules.database import get_all_users, add_credits_to_user

def show_admin_panel():
    """Отображение админ-панели"""
    st.title("🔧 Админ-панель")
    
    tab1, tab2 = st.tabs(["👥 Пользователи", "💰 Начисление кредитов"])
    
    with tab1:
        st.subheader("Все пользователи")
        users = get_all_users()
        if users:
            st.dataframe(users)
        else:
            st.info("Нет пользователей")
    
    with tab2:
        st.subheader("Начислить кредиты")
        user_id = st.number_input("ID пользователя", min_value=1, step=1)
        credits = st.number_input("Количество кредитов", min_value=1, step=10)
        
        if st.button("Начислить"):
            add_credits_to_user(user_id, credits)
            st.success(f"Начислено {credits} кредитов пользователю {user_id}")
