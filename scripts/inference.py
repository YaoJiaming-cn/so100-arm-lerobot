#!/usr/bin/env python
"""真机推理：加载训练好的 ACT 模型，控制 SO-ARM101 从动臂自主执行 Pick and place。
使用 LeRobot 官方 processor 管道处理归一化/反归一化，不手写数据处理逻辑。
每次推理自动保存 CSV 日志 + 定期截图到 outputs/eval/<timestamp>/ 目录。"""

import csv
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.processor.pipeline import PolicyProcessorPipeline
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
MODEL_PATH = "outputs/train/pick_place_act_v2/checkpoints/040000/pretrained_model"
SAVE_FRAME_INTERVAL = 30

JOINT_NAMES = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]
SHORT_NAMES = ["pan", "lift", "elbow", "w_flex", "w_roll", "grip"]


def robot_obs_to_policy_input(obs):
    """将 robot.get_observation() 返回的原始 numpy 数据转为 preprocessor 期望的 tensor 格式。
    - state: (6,) float32 → (1, 6) float32 tensor
    - images: uint8 HWC → float32 BCHW [0,1] tensor
    """
    state = torch.from_numpy(
        np.array([obs[name] for name in JOINT_NAMES], dtype=np.float32)
    ).unsqueeze(0)

    def img_to_tensor(img):
        return torch.from_numpy(img).float().permute(2, 0, 1).unsqueeze(0) / 255.0

    return {
        "observation.state": state,
        "observation.images.wrist": img_to_tensor(obs["wrist"]),
        "observation.images.overhead": img_to_tensor(obs["overhead"]),
    }


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_dir = Path(f"outputs/eval/{timestamp}")
    eval_dir.mkdir(parents=True, exist_ok=True)
    print(f"评估数据保存到: {eval_dir}")

    # 加载策略
    policy = ACTPolicy.from_pretrained(MODEL_PATH)
    policy.reset()
    policy.eval()
    print(f"模型已加载，设备: {policy.config.device}")

    # 加载官方 preprocessor / postprocessor 管道
    preprocessor = PolicyProcessorPipeline.from_pretrained(MODEL_PATH, "policy_preprocessor.json")
    postprocessor = PolicyProcessorPipeline.from_pretrained(MODEL_PATH, "policy_postprocessor.json")
    print("官方 processor 管道已加载")

    # 摄像头
    camera_config = {
        "wrist": OpenCVCameraConfig(index_or_path=CAMERA_WRIST_INDEX, width=640, height=480, fps=FPS),
        "overhead": OpenCVCameraConfig(index_or_path=CAMERA_OVERHEAD_INDEX, width=640, height=480, fps=FPS),
    }

    # 从动臂
    robot_config = SO100FollowerConfig(port=ROBOT_PORT, id=ROBOT_ID, cameras=camera_config, use_degrees=True)
    robot = SO100Follower(robot_config)
    robot.connect()
    if not robot.is_connected:
        raise RuntimeError("机械臂连接失败！检查 COM10 是否插电")

    print(f"开始真机推理，共 {NUM_EPISODES} 条，每条 {EPISODE_TIME_SEC} 秒")
    print("按 Ctrl+C 停止")

    for ep in range(NUM_EPISODES):
        log_say(f"推理第 {ep + 1}/{NUM_EPISODES} 条")
        policy.reset()

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

                # 1. 采集原始观测
                obs = robot.get_observation()
                state_raw = np.array([obs[name] for name in JOINT_NAMES], dtype=np.float32)

                # 2. 转为 tensor 格式 → 官方 preprocessor（归一化 + 转 device）
                policy_input = robot_obs_to_policy_input(obs)
                batch = preprocessor(policy_input)

                # 3. 模型推理
                with torch.no_grad():
                    action_tensor = policy.select_action(batch)

                # 4. 官方 postprocessor 反归一化（期望 dict 格式输入）
                action_dict = postprocessor({"action": action_tensor})
                action_np = action_dict["action"].squeeze(0).cpu().numpy()
                action_robot = {name: float(action_np[i]) for i, name in enumerate(JOINT_NAMES)}
                robot.send_action(action_robot)

                # 5. 记录 CSV
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

        if ep < NUM_EPISODES - 1:
            print("请将机械臂移回起始位置（10 秒）...")
            time.sleep(10)

    robot.disconnect()
    print(f"推理结束，所有数据保存在: {eval_dir}")


if __name__ == "__main__":
    main()
