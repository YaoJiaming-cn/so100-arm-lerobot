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
  --dataset.repo_id=yaojiaming/so100_pick_place_v2 `
  --dataset.num_episodes=5 `
  --dataset.single_task="Pick and place" `
  --dataset.push_to_hub=false `
  --dataset.episode_time_s=30 `
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
  --dataset.repo_id=yaojiaming/so100_pick_place_v2 `
  --dataset.num_episodes=60 `
  --dataset.single_task="Pick and place" `
  --dataset.push_to_hub=false `
  --dataset.episode_time_s=30 `
  --dataset.reset_time_s=10
```

| 参数 | 含义 |
|------|------|
| `dataset.fps=30` | 录制帧率，30 比默认 60 省一半带宽 |
| `num_episodes` | 录制条数（试跑 5，正式 60） |
| `episode_time_s=30` | 每条最长 30 秒兜底，做完立刻按 → 提前结束 |
| `reset_time_s=10` | 条间 10 秒，把机械臂移回起始位 |
| `push_to_hub=false` | 先存本地，录完没问题再手动上传 |

**录制中按键：**
- **→** 右箭头：提前终止当前 episode，进入下一个
- **←** 左箭头：取消当前 episode，重新录本条
- **ESC**：停止录制，编码视频
- **不要按 Ctrl+C！** 录完后 reset 阶段机械臂不动、视频编码需几十秒，等语音说 "Stop recording"

**录制中断后续录**（如中途按 ESC 退出，已录数据不丢失）：

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
  --dataset.repo_id=yaojiaming/so100_pick_place_v2 `
  --dataset.num_episodes=60 `
  --dataset.single_task="Pick and place" `
  --dataset.push_to_hub=false `
  --dataset.episode_time_s=30 `
  --dataset.reset_time_s=10 `
  --resume=true
```

`--resume=true` 自动跳过已录完的条，从断点继续。

**录完后手动上传 HF**（开代理，只在自动上传失败时用）：
```powershell
huggingface-cli upload --repo-type=dataset yaojiaming/so100_pick_place_v2 D:\projects\so100-arm-lerobot\datasets\so100_pick_place_v2 .
```

**准备工作：**
- 桌上放好红色积木块，标记起始位置和目标位置
- 确保主动臂（Leader）不出现在摄像头画面中
- 每条都按相同流程：起始位→靠近物体→夹住→抬起→移到目标→放下→松开→回到起始位→按 →
- 建议每 10 条停下来休息一下，保持动作一致性

### 3. 训练

#### V1（50 条，旺仔牛奶糖，loss 0.27）

```powershell
lerobot-train `
  --dataset.repo_id=yaojiaming/so100_pick_place `
  --dataset.root=D:\projects\so100-arm-lerobot\datasets\so100_pick_place `
  --dataset.streaming=false `
  --policy.type=act `
  --output_dir=outputs/train/pick_place_act `
  --job_name=pick_place_act_v1 `
  --policy.device=cuda `
  --policy.push_to_hub=false `
  --batch_size=4 `
  --steps=20000
```

#### V2（66 条，红色积木块，当前）

首次训练（从头开始）：
```powershell
lerobot-train `
  --dataset.repo_id=yaojiaming/so100_pick_place_v2 `
  --dataset.root=D:\projects\so100-arm-lerobot\datasets\so100_pick_place_v2 `
  --dataset.streaming=false `
  --policy.type=act `
  --output_dir=outputs/train/pick_place_act_v2 `
  --job_name=pick_place_act_v2 `
  --policy.device=cuda `
  --policy.push_to_hub=false `
  --batch_size=4 `
  --steps=30000
```

续训（从 20K checkpoint 继续到 30K）：
```powershell
lerobot-train `
  --config_path=outputs/train/pick_place_act_v2/checkpoints/020000/pretrained_model/train_config.json `
  --dataset.repo_id=yaojiaming/so100_pick_place_v2 `
  --dataset.root=D:\projects\so100-arm-lerobot\datasets\so100_pick_place_v2 `
  --dataset.streaming=false `
  --policy.type=act `
  --output_dir=outputs/train/pick_place_act_v2 `
  --job_name=pick_place_act_v2 `
  --policy.device=cuda `
  --policy.push_to_hub=false `
  --batch_size=4 `
  --steps=30000 `
  --resume=true
```

续训到 100K（从 40K checkpoint 继续）：
```powershell
lerobot-train `
  --config_path=outputs/train/pick_place_act_v2/checkpoints/040000/pretrained_model/train_config.json `
  --dataset.repo_id=yaojiaming/so100_pick_place_v2 `
  --dataset.root=D:\projects\so100-arm-lerobot\datasets\so100_pick_place_v2 `
  --dataset.streaming=false `
  --policy.type=act `
  --output_dir=outputs/train/pick_place_act_v2 `
  --job_name=pick_place_act_v2 `
  --policy.device=cuda `
  --policy.push_to_hub=false `
  --batch_size=4 `
  --steps=100000 `
  --resume=true
```

| 参数 | 含义 |
|------|------|
| `policy.type=act` | Action Chunking Transformer，80M 参数，入门首选 |
| `batch_size=4` | RTX 3060 6GB 保守值，不 OOM 可调 8 |
| `steps=20000 / 30000` | V1 2 万步（50 条），V2 3 万步（66 条，防止欠拟合） |
| `dataset.streaming=false` | 数据集在本地，无需流式读取 |
| `output_dir` | 训练产物（模型权重）保存目录 |

### 4. 真机推理

#### V2（当前，红色积木块，40K 步 / loss 0.11）

```powershell
python scripts/inference.py
```

> `MODEL_PATH` 已指向 `outputs/train/pick_place_act_v2/checkpoints/040000/pretrained_model`
> 推理脚本已改用 **LeRobot 官方 processor 管道**（`PolicyProcessorPipeline`）处理归一化/反归一化，不再手写数据处理

#### V1（旺仔牛奶糖，20K 步 / loss 0.27）

改 `scripts/inference.py` 里 `MODEL_PATH` 为：
```
MODEL_PATH = "outputs/train/pick_place_act/checkpoints/020000/pretrained_model"
```

---

推理前确认：
- 从动臂 COM10 已插电（12V 电源）
- 两个摄像头均已连接（腕部=索引1，俯拍=索引2）
- 机械臂周围无障碍物，夹爪初始位置张开放好
- 机械臂前方放好要抓取的物体

**脚本做了什么：**
1. 加载训练好的 ACT 模型权重
2. 加载归一化统计量（mean/std），做输入归一化 + 输出反归一化
3. 连接从动臂和双摄像头
4. 模型根据摄像头画面实时预测动作
5. 从动臂自主执行抓取（**不需要人操作主动臂**）
6. 每条推理 30 秒，共 2 条
7. 自动保存 CSV 日志（每帧的关节状态 + 预测动作）+ 每秒截图到 `outputs/eval/<时间戳>/`

**按键：**
- **Ctrl+C**：停止推理

| 参数 | 含义 |
|------|------|
| `NUM_EPISODES=2` | 推理条数 |
| `EPISODE_TIME_SEC=30` | 每条最多 30 秒 |
| `MODEL_PATH` | 模型权重路径（脚本里改） |
| `SAVE_FRAME_INTERVAL=30` | 每 30 帧（1 秒）保存一张截图 |

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
