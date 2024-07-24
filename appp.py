import streamlit as st
import time

# 텍스트를 표시할 리스트
texts = ["텍스트 1", "텍스트 2", "텍스트 3", "텍스트 4", "텍스트 5"]

# 앱의 제목
st.title("1초마다 텍스트 업데이트와 동영상 재생")

# 동영상 업로드
uploaded_file = st.file_uploader("동영상을 업로드하세요", type=["mp4", "mov", "avi", "mkv"])

# 버튼 생성
start_button = st.button("시작")

# 텍스트 업데이트를 위한 공간
text_placeholder = st.empty()


# 버튼이 눌리면 텍스트 업데이트 시작
if start_button:
    if uploaded_file is not None:
        st.video(uploaded_file)
    for text in texts:
        text_placeholder.text(text)
        time.sleep(1)
