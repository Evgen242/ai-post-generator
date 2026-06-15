import streamlit as st
import db

st.set_page_config(page_title="История постов", page_icon="📜")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.warning("Пожалуйста, войдите в аккаунт")
    st.stop()

st.title("📜 История постов")

history = db.get_user_posts(st.session_state.user['id'])

if history:
    for topic, post, date in history:
        with st.expander(f"📝 {topic[:50]} — {date.strftime('%Y-%m-%d %H:%M') if date else 'Дата неизвестна'}"):
            st.write(post)
else:
    st.info("У вас пока нет сгенерированных постов")
