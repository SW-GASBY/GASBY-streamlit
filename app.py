import streamlit as st
import boto3
import time
import uuid
import subprocess
import json
import tempfile
import cv2

# AWS S3 클라이언트 설정
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_DEFAULT_REGION = ''

s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=AWS_DEFAULT_REGION)

source_bucket_name = 'gasby-req'
target_bucket_name = 'gasby-resp'

def get_video_duration(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(file.read())
        tmp_file.flush()
        tmp_file_path = tmp_file.name

    cap = cv2.VideoCapture(tmp_file_path)
    if not cap.isOpened():
        print("vid capture error")
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', tmp_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    duration = result.stdout.decode().strip()
    if result.returncode != 0:
        st.error(f'ffprobe error: {result.stderr.decode()}')
        return None

    return [float(duration), float(fps)]

def upload_video_to_s3(file, folder_name, file_name):
    s3_key = f"{folder_name}/{file_name}"
    file.seek(0)
    s3_client.upload_fileobj(file, source_bucket_name, s3_key)
    print(folder_name)

def upload_json_to_s3(json_data, folder_name, file_name):
    s3_key = f"{folder_name}/{file_name}"
    s3_client.put_object(Bucket=source_bucket_name, Key=s3_key, Body=json.dumps(json_data))

def check_comment_in_s3(file_name):
    try:
        s3_client.head_object(Bucket=target_bucket_name, Key=file_name)
        return True
    except:
        return False

def get_commentary_from_s3(file_name):
    comments_list = []
    comm = s3_client.get_object(Bucket=target_bucket_name, Key=file_name)
    body = comm['Body'].read()
    content = json.loads(body.decode('utf-8'))  # JSON 문자열을 파싱
    comments_list = [item['comment'] for item in content]  # 각 'comment'를 리스트에 추가
    return comments_list

# Streamlit 앱
st.title("AI Basketball Commentator")

st.header("Made by GASBY")

st.subheader("팀 색상 선택")
color_options = ["Black", "Blue", "Green", "Purple", "Red", "White", "Yellow", "Orange", "Unlabeled"]
team_a_color = st.selectbox("A팀 색상을 선택하세요", color_options)
team_b_color = st.selectbox("B팀 색상을 선택하세요", color_options)

st.subheader("언어 선택")
language_options = ["Korean", "English", "Spanish", "French", "German", "Chinese", "Japanese"]
language = st.selectbox("언어를 선택하세요", language_options)

# 비디오 업로드 섹션
uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4"])

start_button = st.button("시작")

st.markdown("""
    <style>
    .wide-textbox {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

textbox = st.empty()

if uploaded_file is not None and not start_button:
    file_extension = uploaded_file.name.split('.')[-1]
    if file_extension not in ["mp4"]:
        st.error("지원되지 않는 형식입니다. mp4형식의 파일을 업로드하세요.")
    else:
        unique_id = str(uuid.uuid4())
        folder_name = unique_id
        file_name = f"{unique_id}.mp4"
        json_file_name = f"{unique_id}.json"

        uploaded_file.seek(0)  # 비디오를 다시 읽기 위해 파일 포인터를 처음으로 되돌립니다.

        video_duration, fps = get_video_duration(uploaded_file)
            
        json_data = {
            "language": language,
            "team_a_color": team_a_color,
            "team_b_color": team_b_color,
            "video_duration": video_duration,
            "fps": fps
        }
            
        upload_video_to_s3(uploaded_file, folder_name, file_name)
        upload_json_to_s3(json_data, folder_name, json_file_name)
            
        with st.spinner('해설을 생성중입니다.'):
            while not check_comment_in_s3(f"{folder_name}.json"):
                time.sleep(5)  # 5초마다 확인
                if check_comment_in_s3(f"{folder_name}.json"):
                    break
                
        st.session_state.comm = get_commentary_from_s3(f"{folder_name}.json")
        
        print(st.session_state.comm)
        st.success('해설이 생성되었습니다!')


if start_button:
    if uploaded_file is not None:
        st.video(uploaded_file, autoplay=True)
        print(st.session_state.comm)
        for text in st.session_state.comm:
            textbox.markdown(f"<div class='wide-textbox'>{text}</div>", unsafe_allow_html=True)
            time.sleep(1)
