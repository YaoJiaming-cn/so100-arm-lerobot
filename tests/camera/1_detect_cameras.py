"""检测所有摄像头的分辨率支持情况"""
import cv2

RESOLUTIONS = [
    ("1080P", 1920, 1080),
    ("720P",  1280, 720),
    ("默认",  None, None),
]

for idx in range(5):
    ok = False
    for name, w_target, h_target in RESOLUTIONS:
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            break
        ok = True

        if w_target and h_target:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w_target)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h_target)

        ret, frame = cap.read()
        if ret:
            w, h = frame.shape[1], frame.shape[0]
            tag = "OK" if (w_target is None) or (w == w_target and h == h_target) else f"实际 {w}x{h}"
            print(f'Camera {idx}: {name} -> {w}x{h} {tag}')
        else:
            print(f'Camera {idx}: {name} -> 无法读取')

        cap.release()

    if not ok:
        break
    print()

print('检测完毕')
