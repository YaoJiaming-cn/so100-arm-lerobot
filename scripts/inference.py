#!/usr/bin/env python
"""真机推理：加载训练好的 ACT 模型，控制 SO-ARM101 从动臂自主执行 Pick and place。
每次推理自动保存 CSV 日志 + 定期截图到 outputs/eval/<timestamp>/ 目录。"""

import csv
import os
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch
from safetensors import safe_open
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.robots.so_follower import SO100Follower, SO100FollowerConfig
from lerobot.utils.utils import log_say

# ===== 配置 =====
NUM_EPISODES = 2
FPS = 30
EPISODE_TIME_SEC = 30
ROBOT_PORT = "COM10"
ROBOT_ID = "my_follower_arm"
CAMERA_WRIST_INDEX = 1
CAMERA_OVERHEAD_INDEX = 2
MODEL_PATH = "outputs/train/pick_place_act/checkpoints/020000/pretrained_model"
SAVE_FRAME_INTERVAL = 30  # 每 30 帧（1秒）保存一张截图

JOINT_NAMES = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]
SHORT_NAMES = ["pan", "lift", "elbow", "w_flex", "w_roll", "grip"]


def load_norm_stats(model_path, device="cpu"):
    """从 safetensors 加载归一化统计量。"""
    stats_path = model_path + "/policy_postprocessor_step_0_unnormalizer_processor.safetensors"
    stats = {}
    with safe_open(stats_path, framework="pt") as sf:
        for key in [
            "action.mean", "action.std", "action.min", "action.max",
            "observation.state.mean", "observation.state.std",
            "observation.images.wrist.mean", "observation.images.wrist.std",
            "observation.images.overhead.mean", "observation.images.overhead.std",
        ]:
            if key in sf.keys():
                stats[key] = sf.get_tensor(key).to(device)
    return stats


def main():
    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_dir = Path(f"outputs/eval/{timestamp}")
    eval_dir.mkdir(parents=True, exist_ok=True)
    print(f"评估数据保存到: {eval_dir}")

    # 加载策略
    policy = ACTPolicy.from_pretrained(MODEL_PATH)
    policy.reset()
    policy.eval()
    device = policy.config.device
    print(f"模型已加载，设备: {device}")

    # 加载归一化统计量
    norm = load_norm_stats(MODEL_PATH, device)
    print("归一化统计量已加载")
    # 打印各关节统计信息
    for i, name in enumerate(SHORT_NAMES):
        print(f"  {name}: mean={norm['action.mean'][i]:.1f}, std={norm['action.std'][i]:.1f}, "
              f"range=[{norm['action.min'][i]:.1f}, {norm['action.max'][i]:.1f}]")

    # 摄像头
    camera_config = {
        "wrist": OpenCVCameraConfig(index_or_path=CAMERA_WRIST_INDEX, width=640, height=480, fps=FPS),
        "overhead": OpenCVCameraConfig(index_or_path=CAMERA_OVERHEAD_INDEX, width=640, height=480, fps=FPS),
    }

    # 从动臂
    robot_config = SO100FollowerConfig(port=ROBOT_PORT, id=ROBOT_ID, cameras=camera_config, use_degrees=True)
    robot = SO100Follower(robot_config)

    # 连接机械臂
    robot.connect()
    if not robot.is_connected:
        raise RuntimeError("机械臂连接失败！检查 COM10 是否插电")

    print(f"开始真机推理，共 {NUM_EPISODES} 条，每条 {EPISODE_TIME_SEC} 秒")
    print("按 Ctrl+C 停止")

    for ep in range(NUM_EPISODES):
        log_say(f"推理第 {ep + 1}/{NUM_EPISODES} 条")
        policy.reset()

        # 为本条创建 CSV 日志
        csv_path = eval_dir / f"episode_{ep:02d}.csv"
        csv_file = open(csv_path, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_header = ["frame", "timestamp"] + [f"state_{n}" for n in SHORT_NAMES] + [f"action_{n}" for n in SHORT_NAMES]
        csv_writer.writerow(csv_header)

        episode_start = time.time()
        frame_count = 0

        try:
            while True:
                elapsed = time.time() - episode_start
                if elapsed >= EPISODE_TIME_SEC:
                    break

                loop_start = time.time()

                # 1. 采集观测
                obs = robot.get_observation()

                # 保存原始状态用于日志
                state_raw = np.array([obs[name] for name in JOINT_NAMES], dtype=np.float32)

                # 2. 组装模型输入（归一化）
                state = torch.tensor(state_raw, dtype=torch.float32, device=device)
                state_norm = (state - norm["observation.state.mean"]) / norm["observation.state.std"]

                # 图像: HWC uint8 → CHW float32 [0,1] → 归一化
                wrist_img = torch.from_numpy(obs["wrist"]).float().to(device) / 255.0
                wrist_img = wrist_img.permute(2, 0, 1)
                wrist_img = (wrist_img - norm["observation.images.wrist.mean"]) / norm["observation.images.wrist.std"]

                overhead_img = torch.from_numpy(obs["overhead"]).float().to(device) / 255.0
                overhead_img = overhead_img.permute(2, 0, 1)
                overhead_img = (overhead_img - norm["observation.images.overhead.mean"]) / norm["observation.images.overhead.std"]

                batch = {
                    "observation.state": state_norm.unsqueeze(0),
                    "observation.images.wrist": wrist_img.unsqueeze(0),
                    "observation.images.overhead": overhead_img.unsqueeze(0),
                }

                # 3. 模型推理
                with torch.no_grad():
                    action_tensor = policy.select_action(batch)

                # 4. 反归一化 + 裁剪 + 发送动作
                action_values = action_tensor.squeeze(0)
                action_values = action_values * norm["action.std"] + norm["action.mean"]
                action_values = torch.clamp(action_values, norm["action.min"], norm["action.max"])
                action_np = action_values.cpu().numpy()
                action_dict = {name: float(action_np[i]) for i, name in enumerate(JOINT_NAMES)}
                robot.send_action(action_dict)

                # 5. 记录 CSV 日志
                csv_writer.writerow(
                    [frame_count, f"{elapsed:.3f}"]
                    + [f"{state_raw[i]:.2f}" for i in range(6)]
                    + [f"{action_np[i]:.2f}" for i in range(6)]
                )

                # 6. 定期保存截图
                if frame_count % SAVE_FRAME_INTERVAL == 0:
                    for cam_name, cam_img in [("wrist", obs["wrist"]), ("overhead", obs["overhead"])]:
                        img_dir = eval_dir / f"episode_{ep:02d}" / cam_name
                        img_dir.mkdir(parents=True, exist_ok=True)
                        cv2.imwrite(str(img_dir / f"frame_{frame_count:05d}.jpg"), cam_img)

                frame_count += 1

                # 7. 控制帧率
                elapsed_step = time.time() - loop_start
                sleep_time = (1.0 / FPS) - elapsed_step
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n用户中断")
            csv_file.close()
            break

        csv_file.close()
        log_say(f"第 {ep + 1} 条完成 ({frame_count} 帧), CSV → {csv_path}")

        # 条间复位
        if ep < NUM_EPISODES - 1:
            print("请将机械臂移回起始位置（10 秒）...")
            time.sleep(10)

    robot.disconnect()
    print(f"推理结束，所有数据保存在: {eval_dir}")


if __name__ == "__main__":
    main()
