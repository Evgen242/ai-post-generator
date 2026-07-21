import streamlit as st
from db import get_connection
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Мои посты",
    page_icon="📜",
    layout="wide"
)

st.title("📜 История моих постов")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("⚠️ Пожалуйста, войдите в систему")
    st.stop()

user_id = st.session_state.user["id"]

# Получаем посты через прямое SQL соединение
conn = get_connection()
cur = conn.cursor()
cur.execute(
    "SELECT id, topic, post, created_at FROM posts WHERE user_id = %s ORDER BY created_at DESC",
    (user_id,)
)
posts_data = cur.fetchall()
conn.close()

if not posts_data:
    st.info("📭 У вас пока нет созданных постов")
else:
    st.write(f"Всего постов: **{len(posts_data)}**")
    
    # Преобразуем в список словарей
    posts = []
    for row in posts_data:
        posts.append({
            "id": row[0],
            "topic": row[1],
            "post": row[2],
            "created_at": row[3]
        })
    
    # Показываем в виде карточек
    for i, post in enumerate(posts):
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{post['topic']}**")
                st.caption(f"📅 {post['created_at'].strftime('%d.%m.%Y %H:%M') if post['created_at'] else 'Неизвестно'}")
            with col2:
                if st.button(f"📖 Просмотр", key=f"view_{post['id']}"):
                    st.session_state.selected_post = post
            
            st.markdown("---")
    
    # Показываем выбранный пост
    if st.session_state.get("selected_post"):
        post = st.session_state.selected_post
        st.markdown("### 📝 Полный текст поста")
        st.markdown(f"**Тема:** {post['topic']}")
        st.markdown(f"**Дата:** {post['created_at'].strftime('%d.%m.%Y %H:%M') if post['created_at'] else 'Неизвестно'}")
        st.markdown("---")
        st.markdown(post['post'])
        
        if st.button("❌ Закрыть", use_container_width=True):
            st.session_state.selected_post = None
            st.rerun()
