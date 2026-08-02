# Troubleshooting

## feishu-docx 导出个人飞书知识库报 131005

**现象：**
```shell
feishu-docx export "https://zihao-ai.feishu.cn/wiki/<token>" --auth-mode oauth
```
```
API 请求失败: wiki.v2.space.get_node
  code: 131005
  msg: not found
```

**原因：**
`feishu-docx` 内部使用 `wiki.v2.space.get_node` API（不带 space_id 参数），该端点对个人知识库（OAuth 跨租户场景）返回 131005。

但 `wiki/v2/spaces/{space_id}/nodes/{node_token}` API（带 space_id）用同样的 OAuth token 是正常的。

**绕过方案：**
将 wiki URL 的 token 拼到 docx URL 里导出：

```shell
# 原 URL（失败）
feishu-docx export "https://zihao-ai.feishu.cn/wiki/JP2YdRzUGoLOsyxIHKwc1wcmnHh" --auth-mode oauth

# 改为 docx URL（成功）
feishu-docx export "https://zihao-ai.feishu.cn/docx/JP2YdRzUGoLOsyxIHKwc1wcmnHh" --auth-mode oauth
```

## PyTorch pip 默认安装 CPU 版本

`pip install torch` 从 PyPI 安装的是 CPU 版本。需要指定 CUDA 索引：

```shell
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

验证：
```python
import torch
print(torch.cuda.is_available())  # 应为 True
```

## opencv-python-headless 不支持 imshow

lerobot 依赖了 `opencv-python-headless`，它缺少 GUI 功能。替换为完整版：

```shell
conda install -n lerobot -c conda-forge opencv
```

## TTL 通信偶发错误：Incorrect status packet

**现象：**
```
ConnectionError: Failed to write 'Torque_Enable' on id_=4 with '1' after 1 tries.
[TxRxResult] Incorrect status packet!
```

**原因：**
TTL 半双工总线偶发通信丢包，舵机返回的数据校验不通过。

**解决方法：**
重跑一次命令即可。如果连续多次报同一个舵机 ID，检查该舵机的接线是否松动。

## USB 口不够

两臂 USB 线 ×2 + 摄像头 ×1 + 鼠标 + 键盘 = 至少 5 个 USB 口。普通笔记本 + 一个 4 口扩展坞可能不够。

**解决方法：**
多加一个扩展坞，或者用 USB Hub 集中接键鼠。注意机械臂的 USB 线建议直连电脑或供电充足的扩展坞，避免 USB 供电不足导致通信不稳定。

## COM10 端口打不开（Windows）

**现象：**
```
could not open port 'COM10': OSError(22, '函数不正确。')
```

**原因：**
Windows 对 COM10 及以上端口号有历史遗留 bug，需要用 `\\.\COM10` 格式。

**解决方法 1 — 加 `\\.\` 前缀：**
```powershell
lerobot-teleoperate --robot.port=\\.\COM10 ...
```

**解决方法 2 — 如果 `\\.\COM10` 也不行，确认 follower 的真实端口：**
1. 打开设备管理器 `devmgmt.msc`
2. 展开"端口 (COM 和 LPT)"
3. 拔掉 follower 的 USB 线，观察哪个 COM 口消失
4. 那个就是 follower 的真实端口

**注意：** `lerobot-find-port` 在 Windows 上有 bug——拔线后检测不到端口变化，OError 报 "No difference was found"。

## OpenCV 摄像头 MSMF 后端报错

**现象：**
```
WARN: cap.cpp:480 VIDEOIO(MSMF): backend is generally available but can't be used to capture by index
ConnectionError: Failed to open OpenCVCamera(1).
```
`lerobot-find-cameras opencv` 报大量 `obsensor_uvc_stream_channel.cpp` 错误。

**原因：**
OpenCV 的 MSMF 后端不支持按 index 打开摄像头（可能与 RealSense 深度相机冲突）。

**排查 — DShow 枚举摄像头：**
```powershell
python -c "
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        print(f'Camera {i}: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} OK')
        cap.release()
    else:
        print(f'Camera {i}: not available')
"
```

**排查 — 检查已连接摄像头：**
```powershell
Get-PnpDevice -Class Camera | Select-Object Status, FriendlyName
```

根据 DShow 枚举结果，使用 **DShow 可用的 index** 作为 `index_or_path`。如果所有 index 都不可用，可能需要：
- 检查摄像头驱动是否正确安装
- 在海康威视的官方工具（MVS）里确认摄像头能被系统识别
- 尝试用 `index_or_path` 传入摄像头名称字符串而非数字 index

## 录制结束后视频编码阶段 Windows 进程崩溃

**现象：**
录制完成后，终端显示 "Encoding episode videos. This may take a while..."，随后报大量错误：
```
RuntimeError: module 'torchvision' has no attribute 'disable_batch_tracing'
ImportError: DLL load failed while importing _C: 找不到指定的模块。
```
子进程反复崩溃重启，看起来像死循环。

**原因：**
`save_episode()` 使用 `ProcessPoolExecutor` 并行编码视频。Windows 上 `multiprocessing` 使用 `spawn` 模式（不是 Linux 的 `fork`），子进程会重新 import 所有模块。在这个项目中，重新 import torchvision 会触发一系列 DLL 加载问题，导致子进程 crash。

**解决方法：**
**不要按 Ctrl+C！** 主进程会检测到子进程失败并 fallback 到单进程编码，虽然慢但最终能完成。耐心等待，听到语音说 "Stop recording" 即表示全部完成。按 Ctrl+C 会留下不完整的数据集，下次启动会报 `FileExistsError`。

## HuggingFace 上传超时 / LFS 大文件卡住

**现象：**
- 录制时 `--dataset.push_to_hub=true` 自动上传卡住不动
- 手动 `huggingface-cli upload` 上传到 67% 时卡住（大 MP4 文件 >100MB）

**原因：**
50 条 episode × 2 个摄像头 = 100 个 MP4 视频，每个 20 秒，单文件 100-200MB，总量约 370MB。LFS 上传大文件时网络波动或代理不稳定容易超时。

**解决方法：**
1. 确保代理已开启（Clash `http://127.0.0.1:7890`）
2. 重新运行上传命令，已上传的文件会自动跳过（断点续传）
   ```powershell
   huggingface-cli upload --repo-type=dataset yaojiaming/so100_pick_place D:\projects\so100-arm-lerobot\datasets\so100_pick_place .
   ```
3. 如果反复失败，可先用 `--dataset.push_to_hub=false` 录到本地，录完再手动上传

## 录制中断后重跑报 FileExistsError

**现象：**
```
FileExistsError: Output directory ... already exists
```

**原因：**
上次录制被 Ctrl+C 中断，留下了不完整的数据集目录。LeRobot 检测到已有数据时不会自动覆盖。

**解决方法：**
删除不完整的数据集目录后重跑：
```powershell
rm -r -Force D:\projects\so100-arm-lerobot\datasets\so100_pick_place
```

注意：如果已经部分上传到 HF，删除本地数据不影响 HF 上的内容。重跑后重新上传即可覆盖。
