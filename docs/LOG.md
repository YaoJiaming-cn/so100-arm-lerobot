# 复现日志

## 2026-08-03
- **采集数据集 50 条完成**：`yaojiaming/so100_pick_place`，Pick and place 任务，双摄像头 640×480@30fps，每条 20 秒，间隔 10 秒
- 数据集上传至 HuggingFace：https://huggingface.co/datasets/yaojiaming/so100_pick_place（374MB，含 100 个 MP4 视频 + Parquet 数据）
- 自动上传（`--dataset.push_to_hub=true`）卡住，改用 `huggingface-cli upload --repo-type=dataset` 手动上传成功
- LFS 大文件上传到 67% 时卡住（单个 MP4 100-200MB），重跑上传命令可断点续传（已上传的文件自动跳过）
- 数据集从 C 盘移到 D 盘项目目录 `datasets/so100_pick_place/`
- **训练命令准备完成**：ACT 算法，batch_size=4（RTX 3060 6GB），20000 步，预计 1-2 小时
- 更新 `docs/commands.md`：录制命令分试跑/正式两步，新增训练命令、手动上传命令、参数说明表
- 学到：Windows ProcessPoolExecutor 在 `save_episode()` 视频编码阶段 spawn 子进程时会 crash（import torchvision 失败），不要按 Ctrl+C，耐心等主进程恢复；HuggingFace LFS 上传大文件容易超时，建议用小步迭代方式上传（先录 5 条测试 → 再录 50 条正式）；`huggingface-cli login` 已废弃，用 `hf auth login` 代替

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
