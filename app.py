import cv2
import numpy as np
import mediapipe as mp
from flask import Flask, render_template, request, jsonify, send_from_directory
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# MediaPipe 초기화
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

# 화이트 밸런스 자동 보정 함수
def adjust_white_balance(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    avg_a = np.mean(lab[:, :, 1])
    avg_b = np.mean(lab[:, :, 2])
    for i in range(3):
        image[:, :, i] = image[:, :, i] - (avg_a if i == 1 else avg_b)
    return image

@app.route('/picture/<filename>')
def get_picture(filename):
    return send_from_directory("picture", filename)

# 얼굴 영역 추출
def get_face_color(image):
    face_landmarks = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if face_landmarks.multi_face_landmarks:
        print(f"얼굴 인식 성공, 얼굴 수: {len(face_landmarks.multi_face_landmarks)}")
        for face_landmark in face_landmarks.multi_face_landmarks:
            points = []
            for landmark in face_landmark.landmark:
                x = int(landmark.x * image.shape[1])
                y = int(landmark.y * image.shape[0])
                points.append((x, y))

            # 얼굴 영역 좌표 추출
            min_x = min([p[0] for p in points])
            max_x = max([p[0] for p in points])
            min_y = min([p[1] for p in points])
            max_y = max([p[1] for p in points])

            # 얼굴의 중심을 기준으로 일정 비율로 영역을 자르기
            width = max_x - min_x
            height = max_y - min_y
            center_x = min_x + width // 2
            center_y = min_y + height // 2

            # 일정 비율로 얼굴 영역 자르기 (여기서는 1.5배 크기 영역을 선택)
            new_width = int(width * 1.5)
            new_height = int(height * 1.5)

            # 얼굴 중심을 기준으로 자르기
            new_min_x = max(center_x - new_width // 2, 0)
            new_max_x = min(center_x + new_width // 2, image.shape[1])
            new_min_y = max(center_y - new_height // 2, 0)
            new_max_y = min(center_y + new_height // 2, image.shape[0])

            face_region = image[new_min_y:new_max_y, new_min_x:new_max_x]

            # 화이트 밸런스를 맞추고, HSV로 변환
            face_region = adjust_white_balance(face_region)
            hsv_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)

            # 얼굴 색상 평균 추출
            avg_hue = np.mean(hsv_face[:, :, 0])
            avg_saturation = np.mean(hsv_face[:, :, 1])
            avg_value = np.mean(hsv_face[:, :, 2])

            print(f"Avg Hue: {avg_hue}, Avg Saturation: {avg_saturation}, Avg Value: {avg_value}")

            # 계절 분류 및 웜/쿨, 라이트/뮤트 속성 추가
            if avg_hue >= 0 and avg_hue < 95:
                tone = "웜"  # 봄, 가을
            else:
                tone = "쿨"  # 여름, 겨울

                # 웜 톤 (봄, 가을)
            if tone == "웜":
                if avg_value < 150:  # 봄 (따뜻하고 밝은 색)
                    season = "봄"
                    if avg_saturation > 85:
                            shade = "웜 라이트"  # 밝고 선명한 색
                    else:
                        shade = "웜 브라이트"  # 채도가 낮은 웜톤
                else:  # 가을 (따뜻하고 깊은 색)
                    season = "가을"
                    if avg_saturation > 85:
                            shade = "웜 뮤트"  # 탁하고 깊은 색
                    else:
                        shade = "웜 딥"  # 채도가 낮은 깊은 웜톤

                # 쿨 톤 (여름, 겨울)
            else:  # 쿨 톤
                if avg_value < 170:  # 여름 (차가운 밝은 색)
                    season = "여름"
                    if avg_saturation > 85:
                        shade = "쿨 라이트"  # 부드럽고 차가운 색
                    else:
                        shade = "쿨 뮤트"  # 전체적으로 차가운 색
                else:  # 겨울 (차가운 강렬한 색)
                    season = "겨울"
                    if avg_saturation > 85:
                        shade = "쿨 브라이트"  # 밝고 선명한 차가운 색
                    else:
                        shade = "쿨 다크"  # 채도가 낮은 겨울 톤

            return f"{season} {shade}"

    print("얼굴 인식 실패")
    return "얼굴 분석 실패"


# base64 이미지를 OpenCV 이미지로 변환
def base64_to_cv2(base64_str):
    img_data = base64.b64decode(base64_str.split(',')[1])
    img = Image.open(BytesIO(img_data))
    img = np.array(img)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start():
    return render_template('start.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        image_data = data['image']
        # base64 이미지를 OpenCV 이미지로 변환
        image = base64_to_cv2(image_data)

        # 얼굴 색상 추출 및 분석
        result = get_face_color(image)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
