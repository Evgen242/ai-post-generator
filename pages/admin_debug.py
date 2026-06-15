import streamlit as st
import subprocess

st.set_page_config(page_title="Отладка", page_icon="")
st.title("Отладка удаления")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user or st.session_state.user.get('username') != 'admin':
    st.warning("Доступ только для администратора")
    st.stop()

# Получаем список пользователей
import db
conn = db.get_connection()
cur = conn.cursor()
cur.execute("SELECT id, username FROM users WHERE username != 'admin' ORDER BY id")
users = cur.fetchall()
cur.close()
conn.close()

for user in users:
    st.write(f"ID: {user[0]}, Логин: {user[1]}")
    if st.button(f"Удалить {user[1]} (ID {user[0]})", key=f"del_{user[0]}"):
        result = subprocess.run(
            ["/usr/local/bin/delete_user.sh", str(user[0])],
            capture_output=True,
            text=True
        )
        st.write("Результат:")
        st.write(f"  Код: {result.returncode}")
        st.write(f"  Вывод: {result.stdout}")
        st.write(f"  Ошибка: {result.stderr}")
        if result.returncode == 0:
            st.success("УДАЛЕНО!")
        else:
            st.error("ОШИБКА!")
