"""检测电脑上所有可用的摄像头"""
import cv2

for idx in range(5):
    cap = cv2.VideoCapture(idx)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            w, h = frame.shape[1], frame.shape[0]
            print(f'Camera {idx}: {w}x{h} - OK')
        else:
            print(f'Camera {idx}: 打开成功但无法读取画面')
        cap.release()
    else:
        break

print('检测完毕')
