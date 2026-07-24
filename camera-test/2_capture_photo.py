"""用指定摄像头拍一张照片"""
import cv2

CAMERA_ID = 1  # 0=笔记本内置摄像头, 1=海康威视

cap = cv2.VideoCapture(CAMERA_ID)
ret, frame = cap.read()
if ret:
    cv2.imwrite('snapshot.jpg', frame)
    print(f'Camera {CAMERA_ID} 拍照成功 -> snapshot.jpg')
else:
    print(f'Camera {CAMERA_ID} 拍照失败')
cap.release()
