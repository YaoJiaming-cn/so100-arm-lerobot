# 复现日志

## 2026-08-17
- **阶段性结项**：复现闭环全部跑通（环境搭建 → 组装标定 → 遥操作录制 → 训练 → 真机推理）
- **重新测试结论**：前两天把红色物块摆到合适初始位姿后，基本能稳定完成 Pick-and-place
  - 之前"抖动 + 抓不到"的根因确认为 ACT 模型的 OOD 局限（初始位姿超出训练分布），而非训练或推理代码问题
  - 推理脚本已改用官方 processor 管道，数据处理与训练一致，代码本身无误
- **项目收尾**：完善 README / reproduction-plan 文档，结项
  - 演示视频：`video/` 加入 .gitignore，上传 Bilibili 后在 README 放链接
  - 模型权重：建议推 HF 模型仓库 `yaojiaming/so100_pick_place_act_v2`
- **下一步方向**：换 VLA 模型（SmolVLA）、租云 GPU、扩充数据、装双系统跑官方 lerobot-eval

## 2026-08-04
- **V2 数据集录制完成**：66 条 Pick and place（红色积木块），双摄像头 640×480@30fps，26934 帧
  - 录制中反复崩溃（`ValueError: add_frame before add_episode`），是 LeRobot 内部 bug，与 ← 键（取消当前条）相关
  - `--resume=true` 续录：崩溃不丢数据，断点续录；但 resume 有 bug 导致超出 num_episodes（设定 60 条实际录了 66 条）
  - 数据集：`datasets/so100_pick_place_v2/`（从 HF 缓存拷贝），已上传 HF `yaojiaming/so100_pick_place_v2`
- **V2 训练**：ACT，batch_size=4，分三段
  - 0→20K: loss 7.43→0.17，符号链接崩溃
  - 20K→30K: `--resume=true`（需 `--config_path`），loss 0.17→0.13
  - 30K→40K: loss 0.13→0.11，仍在缓慢下降
  - 40K loss 0.11 换算真实 L1 误差: lift ~6°, pan ~2°，仍未达到实用精度
- **推理脚本重构**：改用 LeRobot 官方 `PolicyProcessorPipeline` 处理归一化/反归一化，不再手写
  - 调试：`from_pretrained` 需要 `config_filename` 参数；postprocessor 需要 dict 包装；image 需先转 float32 tensor 再喂 pipeline
  - 路径更新至 40K checkpoint
- **数据深度分析**：
  - 训练数据中 10% 的 lift 动作在 -100°（最小值），模型被训练数据的极端分布影响
  - 推理时初始位姿超出训练数据范围（lift=-104° vs 训练 min=-99.8°），导致 OOD 预测
  - 归一化 L1 loss 0.11 换算真实角度仍有数度误差，66 条数据量可能不够
  - ACT n_action_steps=100 意味着每 3.3s 才重新查询一次模型，开环控制时间长
- **WSL 评估**：用户考虑装双系统解决推理代码问题，分析 WSL vs 双系统的硬件兼容性（USB/串口/摄像头需 usbipd）

## 2026-08-03
- **训练完成**：ACT 算法，20K 步，~1h34m，loss 7.165 → 0.27（下降 96%），模型 197MB
  - 保存路径：`outputs/train/pick_place_act/checkpoints/020000/pretrained_model/model.safetensors`
  - 训练日志：`outputs/train/pick_place_act/training.log`
  - Windows 符号链接创建失败（WinError 1314），不影响模型权重，需管理员权限或开启开发者模式
- 更新 `docs/commands.md`：训练命令补充 `--policy.push_to_hub=false`
- 术语表新增：模仿学习、Epoch、数据增强、数据集划分
- 学到：LeRobot 训练不区分 epoch，按 step 计；loss 收敛到 0.3 以下即可做真机推理；真机推理没有现成 CLI，需基于 `evaluate.py` 示例脚本定制

- **真机推理调试**：创建 `scripts/inference.py`，多轮迭代修复
  - **第 1 版**：尝试复用官方 `evaluate.py` → 失败，官方脚本需要 placo（C++ FK/IK 库），Windows 上装不了
  - 确认本项目训练数据存储的是**关节角度**（非 EE 空间坐标），无需 FK/IK/URDF，直接输出关节角度即可
  - **第 2 版**：去除 placo 依赖，纯关节空间推理 → 机械臂"动一下就卡住"
  - **根因**：`policy.select_action()` 返回归一化值（z-score ~0.01 量级），脚本直接把 0.01 当角度发给舵机
  - **第 3 版（当前）**：从 `policy_postprocessor_step_0_unnormalizer_processor.safetensors` 加载 mean/std，添加：
    1. 输入归一化：`(state_raw - mean) / std` + `(img/255 - mean) / std`
    2. 输出反归一化：`action_raw = action_normalized * std + mean`
    3. 动作裁剪：clamp 到 `[min, max]` 训练数据范围
  - 修复后机械臂开始运动，但 5 条均未完成任务（抓旺仔牛奶糖）
  - **第 4 版（当前）**：添加 CSV 日志 + 定期截图保存到 `outputs/eval/<timestamp>/`
  - 可能原因：物体太小、示教质量不够（每条前后闲置时间长）、训练数据只有 50 条/2 万步
  - 下次改进：换大物体、录 8-10 秒/条用 → 键提前结束、4-5 万步训练
  - 学到：LeRobot 的 MEAN_STD 归一化在 safetensors 中；ACT 的 `select_action()` 内部维护 100 步 action queue；推理时必须手动做输入归一化 + 输出反归一化；ACT `temporal_ensemble_coeff` 默认为 None（用 queue 而非时间平滑）

## 2026-07-31
- 第二个扩展坞到货，USB 布局确定：Type-C 扩展坞接两臂+移动硬盘，USB 扩展坞接两个摄像头+键盘
- 摄像头索引确认：0=笔记本自带，1=腕部，2=海康威视俯拍
- 带腕部摄像头遥操作测试通过
- 发现高分辨率摄像头导致遥操作周期性掉帧（60Hz→11Hz），低分辨率（320×240, 30fps）流畅，疑似 USB 扩展坞带宽瓶颈，待后续排查
- 海康威视摄像头一度指示灯不亮，排查后确认是之前遥操作占用导致，摄像头本身正常
- 创建 README.md 项目主页
- 更新 `docs/servo-mapping.md`：补充摄像头索引表、USB 布局
- **双摄像头遥操作调试**：多轮硬件布局测试，最终找到可用配置
  - 海康威视俯拍摄像头限制：最低 640×480，不支持 MJPG，不支持 320×240
  - 两个摄像头必须分到不同扩展坞，否则 Windows MSMF 驱动无法同时拉两路 640×480 流
  - 俯拍摄像头不能和主动臂数据线共用扩展坞（否则掉帧）
  - 最终可用布局：USB-A 扩展坞（从动臂 COM10 + 腕部摄像头 + 键盘），Type-C 扩展坞（主动臂 COM9 + 俯拍摄像头 + 移动硬盘）
  - 640×480 双摄像头下有一点点卡，但可接受
- **HuggingFace 配置**：创建 Write token，`huggingface-cli login` 登录成功，用户名 yaojiaming
- **录制命令就绪**：适配为双摄像头 + COM9/COM10 + 自动上传的 `lerobot-record` 命令写入 `docs/commands.md`，数据集 `yaojiaming/so100_pick_place`
- 学到：MSMF（Microsoft Media Foundation）是 Windows 底层视频采集框架，OpenCV 在 Windows 上通过它读写摄像头；双摄像头同时拉流时 MSMF 驱动可能扛不住；USB 拓扑对多摄像头场景至关重要；`huggingface-cli login` 已 deprecated，新命令是 `hf auth login`；Token 暴露后 HF 会自动扫描失效

## 2026-07-28
- 螺丝刀到货，从动臂组装完成，FD 调试工具逐个关节测试通过
- 两臂 LeRobot 标定完成，标定文件存入项目 `calibration/` 目录
- 设置环境变量 `HF_LEROBOT_CALIBRATION` 指向项目文件夹，避免标定文件散落在 C 盘
- 遥操作测试通过：49Hz 实时性，精度高、延迟低
- 创建 `docs/commands.md` 命令速查卡片，后续录数据/训练/推理命令逐步补充
- 记录串口号：COM9（主动臂）、COM10（从动臂）到 `docs/servo-mapping.md`
- 摄像头检测：海康威视 + 笔记本自带摄像头共 2 个，索引 0 和 1
- 遇到 TTL 通信偶发抖动（4 号舵机 Incorrect status packet），重跑一次即恢复正常
- USB 口不够（两臂×2 + 鼠标 + 键盘 + 摄像头 = 5 个口），扩展坞只有 4 个口，已下单第二个扩展坞
- 学到：标定的两个步骤（归零偏移量 + 运动范围），wrist_roll 因可无限旋转被跳过，标定数据同时写入舵机 EEPROM 和 JSON 文件，FK/IK 全在 CPU 计算（控制板只做 USB→TTL 电平转换），TTL 半双工由协议层决定但软件循环快到体感无延迟，SO-ARM 系列谱系（TheRobotStudio × HuggingFace 原创 → Seeed Studio 生产 → 社区传播），TTL 偶发通信错误可通过重试解决

## 2026-07-26
- 通过 `/init` 创建 CLAUDE.md：项目骨架、环境搭建命令、CLI 命令表、Leader→FK→EE→IK→Follower 数据管道架构、硬件舵机映射
- 创建 `.claude/settings.json`：配置 Stop hook，每次对话结束自动提醒检查 LOG.md / reproduction-plan.md / troubleshooting.md 是否需要更新
- 更新 reproduction-plan.md：环境搭建标记为完成（ffmpeg 7.1.1、lerobot 导入成功、CUDA 可用）
- 术语表新增：CLI、FK（正运动学）、IK（逆运动学）、URDF
- 研读 `lerobot/examples/so100_to_so100_EE/teleoperate.py`：理解 20 行核心循环和 FK→IK 管线
- 学到：CLAUDE.md 与 .claude/settings.json 的分工（说明书 vs 自动化规则）、hooks 机制（Stop/PreToolUse 等触发时机）、项目级 vs 用户级配置的覆盖关系、SO-100 与 SO-101 共享代码但机械结构有差异、examples vs src 的分工（使用示范 vs 库源码）

## 2026-07-25
- 海康威视 USB 摄像头测试通过（OpenCV 拍照 + 实时预览 + Windows 相机应用）
- 飞书知识库「同济子豪兄」78 个页面全部导出为本地 Markdown（含图片，共 1.1GB）
- 遇到 `feishu-docx export` 对个人知识库报 131005 → 绕过方案：将 wiki URL 转为 docx URL 导出（详见 `docs/troubleshooting.md`）
- 舵机中位校准并编号完成。发现子豪兄文档《舵机控制板接电源线》最后一幅图中 12V 和 5V 电源适配器标注反了：按标注接 12V 到从动臂时舵机红灯闪烁、软件无法识别，换回标注为 5V 的适配器后正常。已自行纠正。
- **待重做：** 中位校准时未先在调试页将舵机拖至中位（~2048）就点了"中位校准"，导致各舵机的中位偏移量记录不准确。需在组装前逐一重做：调试页拖滑块到 ~2048 → 编程页点中位校准 → 保存。
- 中位校准重做完成（所有舵机已正确校准至 ~2048 中位）。
- 主动臂（Leader Arm）组装完成，FD 调试工具逐个关节测试通过。
- 整理项目结构：`camera-test/` 迁移至 `tests/camera/`；新建 `docs/glossary.md`（术语表，~40 个条目）、`docs/servo-mapping.md`（舵机 ID 对照表）。
- 学到：全双工/半双工、USB 转串口、闭环控制与舵机锁力、主动臂减速比分级的原理、从动臂统一 1:345 的原因。
