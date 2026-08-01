# 命令速查

> 本机配置：主动臂 COM9（黑色），从动臂 COM10（白色）
> 标定文件目录：`calibration/`（环境变量 `HF_LEROBOT_CALIBRATION` 已设置）
> USB 布局：USB-A 扩展坞 → 从动臂 + 腕部摄像头 + 键盘；Type-C 扩展坞 → 主动臂 + 俯拍摄像头 + 移动硬盘
>
> **摄像头兼容性**：腕部（索引 1）支持 320×240～1280×720 + MJPG；俯拍海康（索引 2）最低 640×480，不支持 MJPG 和 320×240。两个摄像头必须分到不同扩展坞。**俯拍不能和主动臂数据线同坞。**

## HuggingFace 登录（首次配置，只需一次）

```bash
huggingface-cli login
# 输入 Write 权限的 Access Token（https://huggingface.co/settings/tokens）
# Token 保存在 C:\Users\a1867\.cache\huggingface\token，忘记可去 HF 网站重建
```

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

# 双摄像头 - 低分辨率调试版（排查卡顿用，俯拍最低 640×480，不支持 MJPG）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 320, height: 240, fps: 30}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true

# 双摄像头 - 标准版（腕部 MJPG + 俯拍无 MJPG，俯拍不支持 MJPG）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true

# 双摄像头 - 两个都不用 MJPG（MSMF 驱动兼容性测试）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true
```

停止：按 `Ctrl+C`

## 录制数据集

```bash
# 双摄像头录制，自动上传 HuggingFace
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=COM10 \
    --robot.id=my_follower_arm \
    --robot.cameras="{ wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, overhead: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=COM9 \
    --teleop.id=my_leader_arm \
    --display_data=true \
    --dataset.repo_id=yaojiaming/so100_pick_place \
    --dataset.num_episodes=10 \
    --dataset.single_task="Pick and place" \
    --dataset.push_to_hub=true \
    --dataset.episode_time_s=10 \
    --dataset.reset_time_s=2
```

参数说明：
- `repo_id`：`yaojiaming/so100_pick_place`，数据本地保存在 `~/.cache/huggingface/lerobot/`
- `num_episodes`：录制 10 条，第一次先试试手感
- `single_task`："Pick and place"（抓取并放置），最经典的入门任务
- `episode_time_s`：每条 10 秒
- `reset_time_s`：两条之间间隔 2 秒，用于把机械臂归位
- `push_to_hub=true`：录完自动上传 HuggingFace

录制中按键：
- **→** 右箭头：提前终止当前 episode，进入下一个
- **←** 左箭头：取消当前 episode，重新录
- **ESC**：停止录制，保存数据

## 训练

```bash
# ACT 算法训练（推荐入门，~80M 参数，RTX 3060 6GB 可跑）
lerobot-train \
    --dataset.repo_id=yaojiaming/so100_pick_place \
    --dataset.root=~/.cache/huggingface/lerobot/yaojiaming/so100_pick_place \
    --dataset.revision=v0.1.0 \
    --dataset.streaming=false \
    --policy.type=act \
    --output_dir=outputs/train/pick_place_act \
    --job_name=pick_place_act_v1 \
    --policy.device=cuda \
    --wandb.enable=false \
    --policy.push_to_hub=false \
    --steps=20000 \
    --batch_size=4
```

参数说明：
- `dataset.repo_id`：数据集名称，与录制时一致
- `dataset.root`：数据集本地路径，录完数据后确认实际路径
- `dataset.revision`：数据集版本，上传 HF 时指定
- `dataset.streaming=false`：数据集在本地，无需流式读取
- `policy.type`：`act`（Action Chunking Transformer），最推荐入门
- `output_dir`：训练产物保存目录
- `job_name`：任务名，区分不同训练实验
- `policy.device=cuda`：使用 GPU 训练
- `batch_size=4`：RTX 3060 6GB 显存保守设置，如果没 OOM 可调到 8
- `steps=20000`：简单抓取任务 2 万步足够
- `wandb.enable=false`：先不启用 wandb 可视化，需要的话装 `pip install wandb` 后改为 true

## 真机推理

（待补充）
