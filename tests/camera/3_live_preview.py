"""摄像头实时预览，按 q 退出"""
import cv2

CAMERA_ID = 1  # 0=笔记本内置摄像头, 1=海康威视

cap = cv2.VideoCapture(CAMERA_ID)
print(f'Camera {CAMERA_ID} 实时预览中... 按 q 退出')

while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow(f'Camera {CAMERA_ID}', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print('已退出')
