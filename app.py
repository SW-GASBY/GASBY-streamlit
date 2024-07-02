import streamlit as st
from pytube import YouTube
import tempfile
import os
import requests
import time
import uuid as uuid_lib
from datetime import datetime
import base64

# Streamlit 페이지 설정
st.set_page_config(
    page_title="Basketball Commentator",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("Basketball Commentator")

# 업로드 방식 선택
upload_option = st.radio(
    "Select an upload option",
    ('YouTube URL', 'Upload from Local')
)

# 고정된 API URL
api_url_post = "https://nj7ceu0i9c.execute-api.ap-northeast-2.amazonaws.com/deploy/request"

# UUID 저장용 변수
uuid = None

def check_status(uuid):
    status_placeholder = st.empty()
    result_placeholder = st.empty()
    
    while True:
        response = requests.get(f"{api_url_post}/{uuid}")
        
        if response.status_code == 200:
            result_placeholder.success('Video processing completed!')
            # 결과 비디오를 표시
            result_placeholder.video(response.content)
            break
        else:
            status_placeholder.info(f"Processing... (Status code: {response.status_code})")
        
        time.sleep(5)

# URL을 통한 동영상 업로드
if upload_option == 'YouTube URL':
    youtube_url = st.text_input("Enter YouTube video URL")
    if youtube_url:
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
                    # UUID 생성
                    unique_id = str(uuid_lib.uuid4())
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    user_id = f"{unique_id}_{timestamp}"
                    
                    with open(temp_file_path, 'rb') as f:
                        file_content = f.read()
                        file_content_base64 = base64.b64encode(file_content).decode('utf-8')
                        
                        payload = {
                            'file': file_content_base64,
                            'userId': user_id  
                        }

                        response = requests.post(api_url_post, json=payload)
                    
                    if response.status_code == 200:
                        st.success('Video uploaded successfully!')
                        result = response.json()
                        st.write(f"result: {result}")
                        uuid = result.get('uuid')
                        st.write(f"UUID: {uuid}")
                        check_status(uuid)  # 상태 확인 함수 호출
                    else:
                        st.error(f"Failed to upload video. Status code: {response.status_code}")
                        st.write(response.text)

                # 삭제를 위해 파일 경로 저장
                st.session_state['temp_file_path'] = temp_file_path
            
            else:
                st.error("No suitable video stream found.")
        
        except Exception as e:
            st.error(f"An error occurred: {e}")

# 로컬 파일 업로드
elif upload_option == 'Upload from Local':
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4"])
    if uploaded_file:
        temp_file_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Uploaded file successfully: {temp_file_path}")
        
        # 동영상 표시
        st.video(temp_file_path)
        
        # API 호출 버튼
        if st.button('Upload Video to API'):
            # UUID 생성
            unique_id = str(uuid_lib.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            user_id = f"{unique_id}_{timestamp}"
            
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')
                        
                payload = {
                    'file': file_content_base64,
                    'userId': user_id  
                }

                response = requests.post(api_url_post, json=payload)
            
            if response.status_code == 200:
                st.success('Video uploaded successfully!')
                result = response.json()
                st.write(f"result: {result}")
                uuid = result.get('uuid')
                st.write(f"UUID: {uuid}")
                check_status(uuid)  # 상태 확인 함수 호출
            else:
                st.error(f"Failed to upload video. Status code: {response.status_code}")
                st.write(response.text)



# 파일 삭제 처리
if 'temp_file_path' in st.session_state:
    if st.button('Delete Video'):
        os.remove(st.session_state['temp_file_path'])
        del st.session_state['temp_file_path']
        st.success('Video deleted successfully!')
