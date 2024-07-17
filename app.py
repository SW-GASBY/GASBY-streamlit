import streamlit as st
import boto3
import time
import uuid
import subprocess
import json
import tempfile

# AWS S3 클라이언트 설정
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_DEFAULT_REGION = ''

s3_client = boto3.client('s3',
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_DEFAULT_REGION
                      )

source_bucket_name = 'gasby-req'
target_bucket_name = 'gasby-result'

def get_video_duration(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(file.read())
        tmp_file.flush()
        tmp_file_path = tmp_file.name
    
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', tmp_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    duration = result.stdout.decode().strip()
    if result.returncode != 0:
        st.error(f'ffprobe error: {result.stderr.decode()}')
        return None

    return float(duration)

def upload_video_to_s3(file, folder_name, file_name):
    # 폴더와 파일 이름을 조합한 객체 키 생성
    s3_key = f"{folder_name}/{file_name}"
    file.seek(0)
    s3_client.upload_fileobj(file, source_bucket_name, s3_key)
    st.success(f'영상이 {folder_name} 폴더에 업로드 되었습니다.')

def upload_json_to_s3(json_data, folder_name, file_name):
    # 폴더와 파일 이름을 조합한 객체 키 생성
    s3_key = f"{folder_name}/{file_name}"
    s3_client.put_object(Bucket=source_bucket_name, Key=s3_key, Body=json.dumps(json_data))
    st.success(f'JSON 파일이 {folder_name} 폴더에 업로드 되었습니다.')

def check_video_in_s3(file_name):
    try:
        s3_client.head_object(Bucket=target_bucket_name, Key=file_name)
        return True
    except:
        return False

def download_video_from_s3(file_name):
    s3_client.download_file(target_bucket_name, file_name, file_name)
    return file_name

def list_videos_in_bucket():
    response = s3_client.list_objects_v2(Bucket=target_bucket_name)
    videos = response.get('Contents', [])
    return [video['Key'] for video in videos]

# Streamlit 앱
st.title("S3 비디오 관리")

# 토글 버튼
mode = st.sidebar.selectbox("모드를 선택하세요", ["영상 업로드 및 보기", "모든 영상 보기"])

if mode == "영상 업로드 및 보기":
    st.header("영상 업로드 및 보기")

    st.subheader("팀 색상 선택")
    color_options = ["Black", "Blue", "Green", "Purple", "Red", "White", "Yellow", "Orange", "Unlabeled"]
    team_a_color = st.selectbox("A팀 색상을 선택하세요", color_options)
    team_b_color = st.selectbox("B팀 색상을 선택하세요", color_options)
    
    # 비디오 업로드 섹션
    uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4"])

    if uploaded_file is not None:

        # 업로드된 파일의 형식 확인
        file_extension = uploaded_file.name.split('.')[-1]
        if file_extension not in ["mp4"]:
            st.error("지원되지 않는 형식입니다. mp4형식의 파일을 업로드하세요.")
        else:
            # UUID 생성
            unique_id = str(uuid.uuid4())
            folder_name = unique_id
            file_name = f"{unique_id}.mp4"
            json_file_name = f"{unique_id}.json"
            
            # 파일을 다시 시작 위치로 돌려야 ffprobe가 읽을 수 있습니다.
            # uploaded_file.seek(0)
            videoDuration = get_video_duration(uploaded_file)
            
            json_data = {
                "team_a_color": team_a_color,
                "team_b_color": team_b_color,
                "video duration": videoDuration
            }
            upload_video_to_s3(uploaded_file, folder_name, file_name)
            upload_json_to_s3(json_data, folder_name, json_file_name)

            st.info('비디오 처리가 완료될 때까지 기다려주세요...')

            # UUID로 타겟 버킷에서 체크
            while not check_video_in_s3(file_name):
                time.sleep(5)  # 5초마다 확인

            st.success('비디오 처리가 완료되었습니다. 다운로드를 시작합니다.')
            video_path = download_video_from_s3(file_name)

            # 비디오 표시
            st.video(video_path)
        

elif mode == "모든 영상 보기":
    st.header("모든 영상 보기")

    # 버킷에서 모든 비디오 리스트 가져오기
    videos = list_videos_in_bucket()

    if videos:
        for video in videos:
            st.video(f"https://{target_bucket_name}.s3.amazonaws.com/{video}")
    else:
        st.warning("버킷에 비디오가 없습니다.")
