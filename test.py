import requests
import base64

url = 'https://nj7ceu0i9c.execute-api.ap-northeast-2.amazonaws.com/deploy/request'

# user 요청받아서 만들기
file_path = '/Users/jungheechan/Desktop/kakao.mp4'
userId = '1'

# 파일을 base64로 인코딩
with open(file_path, 'rb') as f:
    file_content = f.read()
    file_content_base64 = base64.b64encode(file_content).decode('utf-8')

# HTTP POST 요청 보내기
payload = {
    'file': file_content_base64,
    'userId': userId  
}

response = requests.post(url, json=payload)

# 응답 확인
print(response.status_code)
print(response.json())