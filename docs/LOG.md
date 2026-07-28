# 复现日志

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
