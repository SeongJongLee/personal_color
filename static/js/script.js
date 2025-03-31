const video = document.getElementById('video');
const canvas = document.createElement('canvas');
const context = canvas.getContext('2d');
const loadingPopup = document.getElementById('loading-popup');
const resultContainer = document.getElementById('result-container');
const colorResult = document.getElementById('color-result');
const colorPicker = document.getElementById('color-picker');
const resetBtn = document.getElementById('reset-btn');

navigator.mediaDevices.getUserMedia({ video: true })
    .then((stream) => {
        video.srcObject = stream;
    })
    .catch(err => console.error('카메라 접근 실패:', err));

function analyzeFace() {
    loadingPopup.style.display = 'flex';

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const image = canvas.toDataURL('image/jpeg');

    fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: image })
    })
    .then(response => response.json())
    .then(data => {
        loadingPopup.style.display = 'none';

        if (data.error) {
            alert(data.error);
        } else {
            colorResult.textContent = `추천된 퍼스널 컬러: ${data.predicted_color}`;
            resultContainer.style.display = 'block';
            colorPicker.style.display = 'inline';
            resetBtn.style.display = 'block';
        }
    })
    .catch(error => {
        loadingPopup.style.display = 'none';
        alert('분석 실패');
    });
}

document.getElementById('analyze-btn').addEventListener('click', analyzeFace);
