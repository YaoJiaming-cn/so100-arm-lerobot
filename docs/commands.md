# 命令速查

> 本机配置：主动臂 COM9（黑色），从动臂 COM10（白色）
> 标定文件目录：`calibration/`（环境变量 `HF_LEROBOT_CALIBRATION` 已设置）
> USB 布局：Type-C 扩展坞 → 两臂数据线 + 移动硬盘；USB 扩展坞 → 两个摄像头 + 键盘

## 标定（首次组装后跑一次即可）

```bash
# 从动臂（白色）
lerobot-calibrate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm

# 主动臂（黑色）
lerobot-calibrate --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm
```

## 检测摄像头

```bash
lerobot-find-cameras opencv
```

## 摄像头索引确认（逐个拍一张照，看画面确认，不需要遥操作）

```bash
# 测试索引 0
python -c "import cv2; cap = cv2.VideoCapture(0, cv2.CAP_DSHOW); cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480); ret, frame = cap.read(); cv2.imshow('Camera 0 - press any key to close', frame); cv2.waitKey(0); cap.release(); cv2.destroyAllWindows()"

# 测试索引 1
python -c "import cv2; cap = cv2.VideoCapture(1, cv2.CAP_DSHOW); cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480); ret, frame = cap.read(); cv2.imshow('Camera 1 - press any key to close', frame); cv2.waitKey(0); cap.release(); cv2.destroyAllWindows()"

# 测试索引 2
python -c "import cv2; cap = cv2.VideoCapture(2, cv2.CAP_DSHOW); cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480); ret, frame = cap.read(); cv2.imshow('Camera 2 - press any key to close', frame); cv2.waitKey(0); cap.release(); cv2.destroyAllWindows()"
```

## 遥操作

```bash
# 不带摄像头（最流畅）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm

# 单摄像头 - 低分辨率调试版（排查卡顿用）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 320, height: 240, fps: 30}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true

# 单摄像头 - 标准版（rerun.io 可视化）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true

# 双摄像头（腕部 wrist + 俯拍 overhead）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true
```

停止：按 `Ctrl+C`

## 录制数据集

（待补充）

## 训练

（待补充）

## 真机推理

（待补充）
