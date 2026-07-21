import streamlit as st
import auth
from modules.generator import generate_post
from modules.image_generator import generate_image
import db
import time

st.set_page_config(
    page_title="Telegram Post Generator",
    page_icon="📝",
    layout="wide"
)

def load_css():
    try:
        with open("static/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_css()

if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    auth.init_auth_interface()

if st.session_state.user:
    st.markdown("### ✍️ Создать новый пост")

    topic = st.text_input("Тема поста", placeholder="Например: как правильно отдыхать на море")

    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("Язык", ["Русский", "English", "Қазақша", "Українська"])
        lang_code = {"Русский": "ru", "English": "en", "Қазақша": "kk", "Українська": "uk"}[language]
    with col2:
        tone = st.selectbox("Тональность", ["Экспертная", "Дружеская", "Юмористическая"])

    col3, col4 = st.columns(2)
    with col3:
        length = st.selectbox("Длина", ["short", "medium", "long"],
                             format_func=lambda x: {"short": "Короткий", "medium": "Средний", "long": "Длинный"}[x])
    with col4:
        include_hashtags = st.checkbox("Добавить хештеги", value=True)

    st.markdown("---")
    st.markdown("### 🖼️ Генерация изображения")
    generate_image_flag = st.checkbox("Сгенерировать изображение", value=False)

    img_style = "Реалистичный"
    img_detail = "Средняя"
    extra_details = ""

    if generate_image_flag:
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            img_style = st.selectbox("Стиль", ["Реалистичный", "Мультяшный", "Аниме", "Акварель", "3D", "Киберпанк"])
        with col_img2:
            img_detail = st.select_slider("Детализация", options=["Быстрая", "Средняя", "Высокая", "Максимальная"])
        extra_details = st.text_input("Дополнительно (опционально)", placeholder="солнце, город, люди...")

    st.markdown("---")
    st.markdown("### ✅ Проверка фактов")
    factcheck_flag = st.checkbox("Автоматический фактчекинг", value=False)

    st.markdown("---")
    st.markdown("### 🧑‍💻 Человезация текста")
    humanize_flag = st.checkbox("Сделать текст более человеческим", value=False)

    st.markdown("---")

    # Простая кнопка без лишних параметров
    clicked = st.button("🚀 Сгенерировать")

    if clicked:
        credits = auth.get_user_credits(st.session_state.user['id'])
        needed = 1 + (2 if generate_image_flag else 0) + (1 if factcheck_flag else 0) + (1 if humanize_flag else 0)

        if credits < needed:
            st.error(f"❌ Недостаточно кредитов. Нужно: {needed}, доступно: {credits}")
        else:
            with st.spinner("⏳ Генерация поста..."):
                post = generate_post(topic, tone, length, lang_code, include_hashtags)
                time.sleep(0.5)

                if post and not post.startswith("❌"):
                    # Списываем кредиты
                    if not auth.use_credit(st.session_state.user['id']):
                        st.error("❌ Ошибка списания кредитов")
                        st.stop()

                    st.success("✅ Пост сгенерирован!")

                    # Показываем результат
                    st.markdown("### 📝 Результат")
                    st.markdown(post)

                    # Сохраняем в базу
                    db.save_post(st.session_state.user['id'], topic, post)

                    # Генерация изображения
                    image = None
                    if generate_image_flag:
                        with st.spinner("🎨 Генерация изображения..."):
                            image = generate_image(topic, img_style, img_detail, extra_details)
                            if image:
                                st.image(image, use_container_width=True)
                                st.success("✅ Изображение сгенерировано!")

                    # Обновляем кредиты
                    st.session_state.user['credits'] = auth.get_user_credits(st.session_state.user['id'])
                    st.metric("💰 Кредитов осталось", st.session_state.user['credits'])

                else:
                    st.error(f"❌ Ошибка генерации: {post}")
else:
    st.info("👈 Войдите или зарегистрируйтесь, чтобы начать")
