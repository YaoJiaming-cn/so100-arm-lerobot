# 命令速查

> 本机配置：主动臂 COM9（黑色），从动臂 COM10（白色）
> 标定文件目录：`calibration/`（环境变量 `HF_LEROBOT_CALIBRATION` 已设置）

## 标定（首次组装后跑一次即可）

```bash
# 从动臂（白色）
lerobot-calibrate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm

# 主动臂（黑色）
lerobot-calibrate --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm
```

## 遥操作

```bash
# 不带摄像头
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm

# 带摄像头画面（rerun.io 可视化）
lerobot-teleoperate --robot.type=so101_follower --robot.port=COM10 --robot.id=my_follower_arm --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 60, fourcc: "MJPG"}}" --teleop.type=so101_leader --teleop.port=COM9 --teleop.id=my_leader_arm --display_data=true
```

停止：按 `Ctrl+C`

## 检测摄像头

```bash
lerobot-find-cameras opencv
```

## 录制数据集

（待补充）

## 训练

（待补充）

## 真机推理

（待补充）
