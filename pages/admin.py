import streamlit as st
import subprocess
import db
import pandas as pd
from datetime import datetime

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user or st.session_state.user.get('username') != 'admin':
    st.warning("Доступ только для администратора")
    st.stop()

st.set_page_config(page_title="Админ-панель", page_icon="")
st.title("Админ-панель")

# Функция удаления (работает)
def delete_user(user_id):
    result = subprocess.run(
        ["/usr/local/bin/delete_user.sh", str(user_id)],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

# Получение статистики
conn = db.get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM users")
total_users = cur.fetchone()[0]
cur.execute("SELECT SUM(credits) FROM users")
total_credits = cur.fetchone()[0] or 0
cur.execute("SELECT COUNT(*) FROM posts")
total_posts = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM posts WHERE created_at > NOW() - INTERVAL '7 days'")
posts_last_7d = cur.fetchone()[0]
cur.close()
conn.close()

# Метрики
st.subheader("Общая статистика")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Пользователи", total_users)
with col2:
    st.metric("Кредиты в системе", f"{total_credits:,}")
with col3:
    st.metric("Всего постов", total_posts)
with col4:
    st.metric("Посты за 7 дней", posts_last_7d)

st.markdown("---")

# Вкладки
tab1, tab2, tab3, tab4 = st.tabs(["Пользователи", "Начисление кредитов", "Статистика постов", "Очистка данных"])

# ==================== ВКЛАДКА 1: ПОЛЬЗОВАТЕЛИ ====================
with tab1:
    st.subheader("Список пользователей")
    
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, credits, created_at FROM users WHERE username != 'admin' ORDER BY id")
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    if users:
        search = st.text_input("Поиск по логину", placeholder="Введите логин...")
        
        filtered_users = users
        if search:
            filtered_users = [u for u in users if search.lower() in u[1].lower()]
        
        for user in filtered_users:
            with st.expander(f"[ID {user[0]}] {user[1]} — {user[2]} кредитов | Регистрация: {str(user[3])[:10] if user[3] else 'неизвестно'}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Текущие кредиты", user[2])
                    extra = st.number_input("Добавить кредитов", min_value=1, step=10, key=f"credits_{user[0]}")
                    if st.button(f"Начислить", key=f"add_{user[0]}"):
                        db.add_credits(user[0], extra)
                        st.success(f"Начислено {extra} кредитов")
                        st.rerun()
                
                with col2:
                    if st.button(f"Посты пользователя", key=f"posts_{user[0]}"):
                        conn_p = db.get_connection()
                        cur_p = conn_p.cursor()
                        cur_p.execute("SELECT topic, created_at FROM posts WHERE user_id=%s ORDER BY created_at DESC LIMIT 10", (user[0],))
                        posts = cur_p.fetchall()
                        cur_p.close()
                        conn_p.close()
                        if posts:
                            st.write(f"**Последние 10 постов пользователя {user[1]}:**")
                            for p in posts:
                                st.caption(f"📅 {p[1][:16]} | 📝 {p[0][:60]}...")
                        else:
                            st.info("Нет постов")
                
                with col3:
                    st.metric("ID пользователя", user[0])
                    if st.button(f"Удалить пользователя", key=f"del_{user[0]}"):
                        if delete_user(user[0]):
                            st.success(f"Пользователь {user[1]} удалён")
                            st.rerun()
                        else:
                            st.error("Ошибка удаления")
    else:
        st.info("Нет обычных пользователей")

# ==================== ВКЛАДКА 2: НАЧИСЛЕНИЕ КРЕДИТОВ ====================
with tab2:
    st.subheader("Начисление кредитов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**По ID пользователя**")
        user_id = st.number_input("ID пользователя", min_value=1, step=1)
        amount = st.number_input("Количество кредитов", min_value=1, step=10, value=50)
        if st.button("Начислить по ID"):
            db.add_credits(user_id, amount)
            st.success(f"Начислено {amount} кредитов пользователю ID {user_id}")
    
    with col2:
        st.markdown("**Выбрать из списка**")
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE username != 'admin' ORDER BY id")
        users_list = cur.fetchall()
        cur.close()
        conn.close()
        
        if users_list:
            selected_user = st.selectbox("Выберите пользователя", users_list, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
            selected_amount = st.number_input("Количество", min_value=1, step=10, value=50, key="selected_amount")
            if st.button("Начислить выбранному"):
                db.add_credits(selected_user[0], selected_amount)
                st.success(f"Начислено {selected_amount} кредитов пользователю {selected_user[1]}")
    
    st.markdown("---")
    st.subheader("Массовые операции")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bonus_amount = st.number_input("Бонус для всех пользователей", min_value=1, step=10, value=10)
        if st.button("Выдать бонус всем"):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET credits = credits + %s WHERE username != 'admin'", (bonus_amount,))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"Выдано {bonus_amount} кредитов {affected} пользователям")
    
    with col2:
        if st.button("Обнулить кредиты у всех (кроме admin)"):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET credits = 0 WHERE username != 'admin'")
            affected = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"Кредиты обнулены у {affected} пользователей")

# ==================== ВКЛАДКА 3: СТАТИСТИКА ПОСТОВ ====================
with tab3:
    st.subheader("Статистика постов за последние 7 дней")
    
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(created_at), COUNT(*) 
        FROM posts 
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)
    daily_posts = cur.fetchall()
    
    # Топ пользователей по постам
    cur.execute("""
        SELECT u.username, COUNT(p.id) as post_count 
        FROM users u 
        LEFT JOIN posts p ON u.id = p.user_id 
        WHERE u.username != 'admin'
        GROUP BY u.id 
        ORDER BY post_count DESC 
        LIMIT 5
    """)
    top_users = cur.fetchall()
    cur.close()
    conn.close()
    
    if daily_posts:
        df = pd.DataFrame(daily_posts, columns=["Дата", "Посты"])
        st.line_chart(df.set_index("Дата"))
    else:
        st.info("Нет данных за последние 7 дней")
    
    st.markdown("---")
    st.subheader("Топ пользователей по количеству постов")
    
    if top_users:
        for u in top_users:
            st.write(f"**{u[0]}** — {u[1]} постов")
    else:
        st.info("Нет данных")

# ==================== ВКЛАДКА 4: ОЧИСТКА ДАННЫХ ====================
with tab4:
    st.subheader("Очистка данных")
    st.warning("Внимание! Эти действия необратимы.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Удалить все посты"):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM posts")
            conn.commit()
            cur.close()
            conn.close()
            st.success("Все посты удалены")
            st.rerun()
    
    with col2:
        days = st.number_input("Удалить посты старше (дней)", min_value=1, value=30)
        if st.button(f"Удалить посты старше {days} дней"):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM posts WHERE created_at < NOW() - INTERVAL '%s days'", (days,))
            deleted = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            st.success(f"Удалено {deleted} старых постов")
            st.rerun()
    
    st.markdown("---")
    st.subheader("Сброс системы")
    st.error("Удаление ВСЕХ пользователей (кроме admin) и ВСЕХ постов")
    
    if st.button("Сбросить все данные"):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username != 'admin'")
        users_ids = cur.fetchall()
        cur.close()
        conn.close()
        
        for uid in users_ids:
            delete_user(uid[0])
        
        st.success("Система очищена")
        st.rerun()
