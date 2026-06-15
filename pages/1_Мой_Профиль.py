import streamlit as st
import auth
import db

st.set_page_config(page_title="Профиль пользователя", page_icon="👤")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.warning("Пожалуйста, войдите в аккаунт")
    st.stop()

# Убираем заголовок "Мой профиль", оставляем только аватар и информацию

# --- Аватар ---
col_avatar, col_info = st.columns([1, 2])

with col_avatar:
    st.subheader("Фото профиля")
    
    # Загружаем текущий аватар
    current_avatar = db.get_avatar(st.session_state.user['id'])
    
    if current_avatar:
        st.image(current_avatar, width=150)
    else:
        st.image("https://img.icons8.com/ios-filled/100/user.png", width=150)
    
    # Загрузка нового фото
    uploaded_file = st.file_uploader(
        "Загрузить фото", 
        type=["png", "jpg", "jpeg"],
        help="Поддерживаются форматы: PNG, JPG, JPEG"
    )
    
    if uploaded_file:
        try:
            import io
            import base64
            from PIL import Image
            
            # Открываем изображение
            image = Image.open(uploaded_file)
            
            # Изменяем размер до 300x300
            image.thumbnail((300, 300))
            
            # Конвертируем в base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            avatar_data = f"data:image/png;base64,{img_base64}"
            
            # Сохраняем
            db.save_avatar(st.session_state.user['id'], avatar_data)
            st.success("✅ Фото профиля обновлено!")
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")
    
    if current_avatar and st.button("🗑️ Удалить фото"):
        db.save_avatar(st.session_state.user['id'], None)
        st.success("Фото удалено")
        st.rerun()

with col_info:
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("💰 Кредиты", st.session_state.user.get('credits', 10))
        st.metric("👤 Логин", st.session_state.user.get('username', '—'))
    
    with col2:
        st.metric("🎯 План", st.session_state.user.get('plan', 'free').upper())

# --- Блок пополнения баланса ---
st.markdown("---")
st.subheader("💳 Пополнить баланс")
st.markdown("""
| Кредиты | Цена |
|:---|:---|
| **50 кредитов** | 50 ₽ |
| **100 кредитов** | 90 ₽ |
| **500 кредитов** | 400 ₽ |

💬 **Оплата:** [Напишите в Telegram](https://t.me/ваш_логин)
""")
