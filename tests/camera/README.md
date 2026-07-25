# 海康威视摄像头测试 & LeRobot 环境验证

## 文件说明

| 文件 | 用途 | 运行方式 |
|------|------|----------|
| `1_detect_cameras.py` | 检测所有可用摄像头 | `python 1_detect_cameras.py` |
| `2_capture_photo.py` | 拍一张照片 | `python 2_capture_photo.py` |
| `3_live_preview.py` | 实时预览画面（按 q 退出） | `python 3_live_preview.py` |
| `4_verify_env.py` | 验证 LeRobot 环境 | `python 4_verify_env.py` |

## 使用步骤

1. 打开终端，激活虚拟环境：
   ```
   conda activate lerobot
   ```

2. 进入本目录：
   ```
   cd D:\projects\so100-arm-lerobot\camera-test
   ```

3. 运行上方表格里的任意脚本，例如：
   ```
   python 1_detect_cameras.py
   ```

## 摄像头编号

- **Camera 0** — 笔记本内置摄像头
- **Camera 1** — 海康威视 USB 摄像头

脚本里默认用 Camera 1（海康），如果要切回内置摄像头，改脚本里的 `CAMERA_ID = 0`。

## 常用命令

| 操作 | 命令 |
|------|------|
| 激活环境 | `conda activate lerobot` |
| 退出环境 | `conda deactivate` |
| 查看已安装的包 | `pip list` |
| 查看 conda 环境列表 | `conda env list` |
