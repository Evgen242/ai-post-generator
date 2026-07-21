import streamlit as st
import auth
from modules.generator import generate_post
from modules.image_generator import generate_image
from modules.factcheck import factcheck_post, format_factcheck_result
from modules.humanize import humanize_text, detect_ai_artifacts
import db
import time

st.set_page_config(
    page_title="Telegram Post Generator",
    page_icon="",
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
    st.markdown("Создать новый пост")

    topic = st.text_input("Тема поста", placeholder="Например: как пользоваться iPhone")

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
    st.markdown("Генерация изображения")
    generate_image_flag = st.checkbox("Сгенерировать изображение (+2 кредита)", value=False)

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
    st.markdown("Проверка фактов")
    factcheck_flag = st.checkbox("Автоматический фактчекинг (+1 кредит)", value=False)
    factcheck_mode = "strict"
    if factcheck_flag:
        st.markdown("Режим проверки:")
        factcheck_mode = st.radio(
            "Выберите режим фактчекинга",
            ["strict", "predictions", "all"],
            format_func=lambda x: {
                "strict": "Строгий (только факты)",
                "predictions": "С прогнозами (проверять всё)",
                "all": "Полный (всё подряд)"
            }.get(x, x),
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown("Человезация текста")
    humanize_flag = st.checkbox("Сделать текст более человеческим (+1 кредит)", value=False)

    if humanize_flag:
        humanize_style = st.selectbox(
            "Стиль человезации",
            ["natural", "professional", "emotional"],
            format_func=lambda x: {
                "natural": "Естественный (разговорный)",
                "professional": "Профессиональный (экспертный)",
                "emotional": "Эмоциональный (живой)"
            }.get(x, x)
        )

    st.markdown("---")

    if st.button("Сгенерировать"):
        credits = auth.get_user_credits(st.session_state.user['id'])
        needed = 1 + (2 if generate_image_flag else 0) + (1 if factcheck_flag else 0) + (1 if humanize_flag else 0)

        if credits < needed:
            st.error(f"Нужно {needed} кредитов, доступно {credits}")
        elif not topic:
            st.error("Введите тему")
        else:
            with st.spinner("Пишем пост..."):
                try:
                    post = generate_post(topic, tone, length, lang_code, include_hashtags)
                    text_success = True
                except Exception as e:
                    st.error(f"Ошибка генерации текста: {e}")
                    post = None
                    text_success = False

            image = None
            image_success = False
            if generate_image_flag and text_success:
                with st.spinner("Рисуем изображение..."):
                    try:
                        image = generate_image(topic, img_style, img_detail, extra_details)
                        if image:
                            image_success = True
                        else:
                            st.warning("Не удалось сгенерировать изображение. Кредиты за изображение не списаны.")
                    except Exception as e:
                        st.warning(f"Ошибка генерации изображения: {e}. Кредиты за изображение не списаны.")

            artifacts = []
            humanized_post = post
            humanize_success = False
            if humanize_flag and text_success:
                with st.spinner("Очеловечиваем текст..."):
                    try:
                        artifacts = detect_ai_artifacts(post)
                        humanized_post = humanize_text(post, humanize_style)
                        humanize_success = True
                        time.sleep(0.5)
                    except Exception as e:
                        st.warning(f"Человезация временно недоступна: {e}")

            factcheck_result = None
            factcheck_success = False
            if factcheck_flag and text_success:
                with st.spinner("Проверяем факты..."):
                    try:
                        verified_facts = factcheck_post(humanized_post if humanize_success else post, mode=factcheck_mode)
                        factcheck_result = format_factcheck_result(verified_facts)
                        factcheck_success = True
                    except Exception as e:
                        st.warning(f"Фактчекинг временно недоступен: {e}")

            final_post = humanized_post if humanize_success else post
            if final_post and text_success:
                credits_to_deduct = 1
                if image_success:
                    credits_to_deduct += 2
                if factcheck_success:
                    credits_to_deduct += 1
                if humanize_success:
                    credits_to_deduct += 1

                for _ in range(credits_to_deduct):
                    auth.use_credit(st.session_state.user['id'])
                db.save_post(st.session_state.user['id'], topic, final_post)
                st.session_state.user['credits'] = auth.get_user_credits(st.session_state.user['id'])

                st.success(f"Готово! Списано {credits_to_deduct} кредитов")

                if image_success and image:
                    st.image(image)

                if humanize_success and artifacts:
                    st.info(f"Удалены AI-артефакты: {', '.join(artifacts[:5])}")

                st.markdown(f'<div class="result-card">{final_post}</div>', unsafe_allow_html=True)
                st.code(final_post, language="markdown")

                if factcheck_result:
                    st.markdown(factcheck_result)

                st.caption(f"Осталось кредитов: {st.session_state.user['credits']}")
            else:
                st.error("Ошибка генерации поста. Кредиты не списаны.")
else:
    st.info("Войдите или зарегистрируйтесь\n\n📱 На телефоне: нажмите на значок  «>>» в левом верхнем углу")
    with st.expander("Как это работает"):
        st.markdown("""
        - Генерация постов за 10 секунд
        - Генерация изображений
        - Автоматический фактчекинг с источниками
        - Человезация текста — убираем AI-артефакты
        - 10 бесплатных кредитов
        - 5 языка
        """)
