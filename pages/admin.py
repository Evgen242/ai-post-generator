import streamlit as st
import db
from datetime import datetime

st.set_page_config(
    page_title="Админ-панель",
    page_icon="⚙️",
    layout="wide"
)

st.title("Админ-панель")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Пожалуйста, войдите в систему")
    st.stop()

if st.session_state.user.get("username") != "admin":
    st.error("У вас нет прав администратора")
    st.stop()

st.markdown("### Общая статистика")

try:
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]

    cur.execute("SELECT SUM(credits) FROM users")
    total_credits = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM posts")
    posts_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM posts WHERE created_at > NOW() - INTERVAL '7 days'")
    posts_7d = cur.fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Пользователи", users_count)
    col2.metric("Кредиты в системе", f"{total_credits:,}".replace(',', ' '))
    col3.metric("Всего постов", posts_count)
    col4.metric("Посты за 7 дней", posts_7d)

    st.markdown("---")
    st.markdown("### Список пользователей")

    search = st.text_input("Поиск по логину", placeholder="Введите логин...")

    if search:
        cur.execute("SELECT id, username, credits, created_at FROM users WHERE username ILIKE %s ORDER BY id", (f"%{search}%",))
    else:
        cur.execute("SELECT id, username, credits, created_at FROM users ORDER BY id")

    users = cur.fetchall()

    for user in users:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**[ID {user[0]}] {user[1]}**")
                st.caption(f"Регистрация: {user[3].strftime('%Y-%m-%d %H:%M') if user[3] else 'Неизвестно'}")
            with col2:
                st.metric("Кредиты", user[2])
            with col3:
                if user[1] != "admin":
                    if st.button(f"Начислить", key=f"add_{user[0]}"):
                        st.session_state.add_user_id = user[0]
                        st.session_state.add_user_name = user[1]
            with col4:
                if user[1] != "admin":
                    if st.button(f"Удалить", key=f"del_{user[0]}"):
                        conn2 = db.get_connection()
                        cur_del = conn2.cursor()
                        cur_del.execute("DELETE FROM users WHERE id = %s", (user[0],))
                        conn2.commit()
                        conn2.close()
                        st.success(f"Пользователь {user[1]} удален")
                        st.rerun()
            st.markdown("---")

    conn.close()

except Exception as e:
    st.error(f"Ошибка: {e}")

if st.session_state.get("add_user_id"):
    st.markdown("### Начисление кредитов")
    st.info(f"Пользователь: {st.session_state.add_user_name} (ID: {st.session_state.add_user_id})")
    
    amount = st.number_input("Количество кредитов", min_value=1, max_value=1000, value=10)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Добавить кредиты", use_container_width=True):
            try:
                conn2 = db.get_connection()
                cur_add = conn2.cursor()
                cur_add.execute("UPDATE users SET credits = credits + %s WHERE id = %s", (amount, st.session_state.add_user_id))
                conn2.commit()
                conn2.close()
                st.success(f"Добавлено {amount} кредитов пользователю {st.session_state.add_user_name}")
                st.session_state.add_user_id = None
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")
    with col2:
        if st.button("Отмена", use_container_width=True):
            st.session_state.add_user_id = None
            st.rerun()

st.markdown("---")
st.markdown("### Очистка данных")

if st.button("Удалить все посты", use_container_width=True):
    st.warning("Внимание! Это действие необратимо.")
    if st.button("ПОДТВЕРДИТЬ УДАЛЕНИЕ", use_container_width=True):
        try:
            conn2 = db.get_connection()
            cur_del = conn2.cursor()
            cur_del.execute("DELETE FROM posts")
            conn2.commit()
            conn2.close()
            st.success("Все посты удалены")
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка: {e}")
