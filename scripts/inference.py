#!/usr/bin/env python
"""真机推理脚本：加载训练好的 ACT 模型，控制 SO-ARM101 从动臂自主执行 Pick and place 任务。

基于 lerobot/examples/so100_to_so100_EE/evaluate.py 定制。
"""

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.configs.types import FeatureType, PolicyFeature
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.pipeline_features import aggregate_pipeline_dataset_features, create_initial_features
from lerobot.datasets.utils import combine_feature_dicts
from lerobot.model.kinematics import RobotKinematics
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from lerobot.processor import (
    RobotAction,
    RobotObservation,
    RobotProcessorPipeline,
    make_default_teleop_action_processor,
)
from lerobot.processor.converters import (
    observation_to_transition,
    robot_action_observation_to_transition,
    transition_to_observation,
    transition_to_robot_action,
)
from lerobot.robots.so_follower import SO100Follower, SO100FollowerConfig
from lerobot.robots.so_follower.robot_kinematic_processor import (
    ForwardKinematicsJointsToEE,
    InverseKinematicsEEToJoints,
)
from lerobot.scripts.lerobot_record import record_loop
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.utils import log_say
from lerobot.utils.visualization_utils import init_rerun

# ===== 配置参数（按需修改）=====
NUM_EPISODES = 5
FPS = 30
EPISODE_TIME_SEC = 30  # 每条推理时长（秒）
TASK_DESCRIPTION = "Pick and place"
ROBOT_PORT = "COM10"  # 从动臂串口
ROBOT_ID = "my_follower_arm"
CAMERA_WRIST_INDEX = 1
CAMERA_OVERHEAD_INDEX = 2
MODEL_PATH = "outputs/train/pick_place_act/checkpoints/020000/pretrained_model"
URDF_PATH = "lerobot/SO101/so101_new_calib.urdf"
EVAL_DATASET_REPO_ID = "yaojiaming/so100_pick_place_eval"


def main():
    # 摄像头配置（双摄像头）
    camera_config = {
        "wrist": OpenCVCameraConfig(index_or_path=CAMERA_WRIST_INDEX, width=640, height=480, fps=FPS),
        "overhead": OpenCVCameraConfig(index_or_path=CAMERA_OVERHEAD_INDEX, width=640, height=480, fps=FPS),
    }

    # 从动臂配置
    robot_config = SO100FollowerConfig(
        port=ROBOT_PORT,
        id=ROBOT_ID,
        cameras=camera_config,
        use_degrees=True,
    )
    robot = SO100Follower(robot_config)

    # 加载训练好的策略
    policy = ACTPolicy.from_pretrained(MODEL_PATH)

    # 运动学求解器
    kinematics_solver = RobotKinematics(
        urdf_path=URDF_PATH,
        target_frame_name="gripper_frame_link",
        joint_names=list(robot.bus.motors.keys()),
    )

    # EE 动作 → 关节动作
    robot_ee_to_joints_processor = RobotProcessorPipeline[tuple[RobotAction, RobotObservation], RobotAction](
        steps=[
            InverseKinematicsEEToJoints(
                kinematics=kinematics_solver,
                motor_names=list(robot.bus.motors.keys()),
                initial_guess_current_joints=True,
            ),
        ],
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )

    # 关节观测 → EE 观测
    robot_joints_to_ee_pose_processor = RobotProcessorPipeline[RobotObservation, RobotObservation](
        steps=[
            ForwardKinematicsJointsToEE(
                kinematics=kinematics_solver, motor_names=list(robot.bus.motors.keys())
            )
        ],
        to_transition=observation_to_transition,
        to_output=transition_to_observation,
    )

    # 创建评估数据集（记录推理过程的视频和数据）
    dataset = LeRobotDataset.create(
        repo_id=EVAL_DATASET_REPO_ID,
        fps=FPS,
        features=combine_feature_dicts(
            aggregate_pipeline_dataset_features(
                pipeline=robot_joints_to_ee_pose_processor,
                initial_features=create_initial_features(observation=robot.observation_features),
                use_videos=True,
            ),
            aggregate_pipeline_dataset_features(
                pipeline=make_default_teleop_action_processor(),
                initial_features=create_initial_features(
                    action={
                        f"ee.{k}": PolicyFeature(type=FeatureType.ACTION, shape=(1,))
                        for k in ["x", "y", "z", "wx", "wy", "wz", "gripper_pos"]
                    }
                ),
                use_videos=True,
            ),
        ),
        robot_type=robot.name,
        use_videos=True,
        image_writer_threads=4,
    )

    # 策略前后处理器
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy,
        pretrained_path=MODEL_PATH,
        dataset_stats=dataset.meta.stats,
        preprocessor_overrides={"device_processor": {"device": str(policy.config.device)}},
    )

    # 连接机械臂
    robot.connect()

    # 初始化键盘监听器和可视化
    listener, events = init_keyboard_listener()
    init_rerun(session_name="so100_inference")

    try:
        if not robot.is_connected:
            raise ValueError("Robot is not connected!")

        print("开始真机推理...")
        for episode_idx in range(NUM_EPISODES):
            log_say(f"推理第 {episode_idx + 1}/{NUM_EPISODES} 条")

            record_loop(
                robot=robot,
                events=events,
                fps=FPS,
                policy=policy,
                preprocessor=preprocessor,
                postprocessor=postprocessor,
                dataset=dataset,
                control_time_s=EPISODE_TIME_SEC,
                single_task=TASK_DESCRIPTION,
                display_data=True,
                teleop_action_processor=make_default_teleop_action_processor(),
                robot_action_processor=robot_ee_to_joints_processor,
                robot_observation_processor=robot_joints_to_ee_pose_processor,
            )

            # Reset 阶段
            if not events["stop_recording"] and (
                (episode_idx < NUM_EPISODES - 1) or events["rerecord_episode"]
            ):
                log_say("请将机械臂移回起始位置")
                record_loop(
                    robot=robot,
                    events=events,
                    fps=FPS,
                    control_time_s=10,  # 10 秒 reset 时间
                    single_task=TASK_DESCRIPTION,
                    display_data=True,
                    teleop_action_processor=make_default_teleop_action_processor(),
                    robot_action_processor=robot_ee_to_joints_processor,
                    robot_observation_processor=robot_joints_to_ee_pose_processor,
                )

            if events["rerecord_episode"]:
                log_say("重新推理本条")
                events["rerecord_episode"] = False
                events["exit_early"] = False
                dataset.clear_episode_buffer()
                continue

            dataset.save_episode()

    finally:
        log_say("推理结束")
        robot.disconnect()
        listener.stop()
        dataset.finalize()
        print(f"评估数据集已保存到本地，可手动上传 HF：")
        print(f"  huggingface-cli upload --repo-type=dataset {EVAL_DATASET_REPO_ID} {dataset.root} .")


if __name__ == "__main__":
    main()
