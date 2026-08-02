# 命令速查

> **本机配置：** 主动臂 COM9（黑色），从动臂 COM10（白色）
> **摄像头：** 腕部 OpenCV Camera @1（640×480 30fps MJPG）| 俯拍 OpenCV Camera @2（640×480 30fps）
> **标定目录：** `calibration/`
> **USB 布局：** USB-A 扩展坞 → 从动臂 + 腕部摄像头 + 键盘；Type-C 扩展坞 → 主动臂 + 俯拍摄像头 + 移动硬盘

---

## 一次性操作（做过就不用再跑）

### HuggingFace 登录

```powershell
huggingface-cli login
```

### 标定

```powershell
# 从动臂（白色）
lerobot-calibrate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm

# 主动臂（黑色）
lerobot-calibrate --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm
```

---

## 日常操作

### 1. 遥操作（双摄像头）

```powershell
lerobot-teleoperate `
  --robot.type=so101_follower `
  --robot.port=COM10 `
  --robot.id=my_follower_arm `
  --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: 'MJPG'}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" `
  --teleop.type=so101_leader `
  --teleop.port=COM9 `
  --teleop.id=my_leader_arm `
  --display_data=true
```

停止：`Ctrl+C`

### 2. 录制数据集

**第一步：试跑 5 条**（确认流程没问题）

```powershell
lerobot-record `
  --robot.type=so101_follower `
  --robot.port=COM10 `
  --robot.id=my_follower_arm `
  --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: 'MJPG'}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" `
  --teleop.type=so101_leader `
  --teleop.port=COM9 `
  --teleop.id=my_leader_arm `
  --display_data=true `
  --dataset.fps=30 `
  --dataset.repo_id=yaojiaming/so100_pick_place_test `
  --dataset.num_episodes=5 `
  --dataset.single_task="Pick and place" `
  --dataset.push_to_hub=true `
  --dataset.episode_time_s=20 `
  --dataset.reset_time_s=10
```

**第二步：正式录制**（试跑没问题后跑这个）

```powershell
lerobot-record `
  --robot.type=so101_follower `
  --robot.port=COM10 `
  --robot.id=my_follower_arm `
  --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: 'MJPG'}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" `
  --teleop.type=so101_leader `
  --teleop.port=COM9 `
  --teleop.id=my_leader_arm `
  --display_data=true `
  --dataset.fps=30 `
  --dataset.repo_id=yaojiaming/so100_pick_place `
  --dataset.num_episodes=50 `
  --dataset.single_task="Pick and place" `
  --dataset.push_to_hub=true `
  --dataset.episode_time_s=20 `
  --dataset.reset_time_s=10
```

| 参数 | 含义 |
|------|------|
| `dataset.fps=30` | 录制帧率，30 比默认 60 省一半带宽 |
| `num_episodes` | 录制条数（试跑 5，正式 50） |
| `episode_time_s=20` | 每条 20 秒，一次完整的抓取+放置 |
| `reset_time_s=10` | 条间 10 秒，把机械臂移回起始位 |
| `push_to_hub=false` | 先存本地，录完没问题再手动上传（推荐） |

**录制中按键：**
- **→** 右箭头：提前终止当前 episode，进入下一个
- **←** 左箭头：取消当前 episode，重新录本条
- **ESC**：停止录制，编码视频
- **不要按 Ctrl+C！** 录完后 reset 阶段机械臂不动、视频编码需几十秒，等语音说 "Stop recording"

**录完后手动上传 HF**（开代理，只在自动上传失败时用）：
```powershell
huggingface-cli upload --repo-type=dataset yaojiaming/so100_pick_place D:\projects\so100-arm-lerobot\datasets\so100_pick_place .
```

**准备工作：**
- 桌面上放好要抓的小物体（积木、瓶盖、橡皮等）
- 标记起始位置和目标位置
- 确保主动臂（Leader）不出现在摄像头画面中
- 建议每 10 条停下来休息一下，保持动作一致性

### 3. 训练

```powershell
lerobot-train `
  --dataset.repo_id=yaojiaming/so100_pick_place `
  --dataset.root=D:\projects\so100-arm-lerobot\datasets\so100_pick_place `
  --dataset.streaming=false `
  --policy.type=act `
  --output_dir=outputs/train/pick_place_act `
  --job_name=pick_place_act_v1 `
  --policy.device=cuda `
  --batch_size=4 `
  --steps=20000
```

| 参数 | 含义 |
|------|------|
| `policy.type=act` | Action Chunking Transformer，80M 参数，入门首选 |
| `batch_size=4` | RTX 3060 6GB 保守值，不 OOM 可调 8 |
| `steps=20000` | 简单抓取任务 2 万步，约 1-2 小时 |
| `dataset.streaming=false` | 数据集在本地，无需流式读取 |
| `output_dir` | 训练产物（模型权重）保存目录 |

### 4. 真机推理

（待补充）

---

## 排查工具

```powershell
# 检测摄像头序号
lerobot-find-cameras opencv

# 检测串口号
lerobot-find-port

# 逐个打开摄像头确认画面（DShow 后端）
python -c "import cv2; cap = cv2.VideoCapture(1, cv2.CAP_DSHOW); cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480); ret, frame = cap.read(); cv2.imshow('Camera 1', frame); cv2.waitKey(0); cap.release(); cv2.destroyAllWindows()"
```
