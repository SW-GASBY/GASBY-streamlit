import streamlit as st
from pytube import YouTube
import tempfile
import os
import requests

# Streamlit 페이지 설정
st.set_page_config(
    page_title="YouTube Video Downloader and Uploader",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("YouTube Video Downloader and Uploader")

# 유튜브 링크 입력
youtube_url = st.text_input("Enter YouTube video URL")

# API URL 입력
api_url = st.text_input("Enter API URL")

if youtube_url and api_url:
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        
        if stream:
            st.write(f"Title: {yt.title}")
            st.write(f"Author: {yt.author}")
            st.write(f"Views: {yt.views}")
            
            # 임시 파일 저장소 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                stream.download(output_path=os.path.dirname(temp_file.name), filename=os.path.basename(temp_file.name))
                temp_file_path = temp_file.name
            
            st.success(f"Video downloaded successfully: {temp_file_path}")
            
            # 동영상 표시
            st.video(temp_file_path)
            
            # API 호출 버튼
            if st.button('Upload Video to API'):
                with open(temp_file_path, 'rb') as f:
                    files = {'file': (os.path.basename(temp_file_path), f, 'video/mp4')}
                    response = requests.post(api_url, files=files)
                
                if response.status_code == 200:
                    st.success('Video uploaded successfully!')
                    st.json(response.json())
                else:
                    st.error(f"Failed to upload video. Status code: {response.status_code}")
                    st.write(response.text)

            # 삭제를 위해 파일 경로 저장
            st.session_state['temp_file_path'] = temp_file_path
        
        else:
            st.error("No suitable video stream found.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

# 파일 삭제 처리
if 'temp_file_path' in st.session_state:
    if st.button('Delete Video'):
        os.remove(st.session_state['temp_file_path'])
        del st.session_state['temp_file_path']
        st.success('Video deleted successfully!')
