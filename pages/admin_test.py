import streamlit as st
import subprocess

st.set_page_config(page_title="Тест удаления", page_icon="")
st.title("Тест удаления")

if st.button("Запустить удаление пользователя ID 1"):
    result = subprocess.run(
        ["/usr/local/bin/delete_user.sh", "1"],
        capture_output=True,
        text=True
    )
    st.write("Код возврата:", result.returncode)
    st.write("stdout:", result.stdout)
    st.write("stderr:", result.stderr)
