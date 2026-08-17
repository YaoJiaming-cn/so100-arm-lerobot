# LingBot-VLA + LeRobot + SO-ARM101 复现流程

> 参考教程：[同济子豪兄 LeRobot 保姆级知识库](https://zihao-ai.feishu.cn/wiki/space/7589642043471924447)
> 视频参考：速通具身智能毕业论文！LeRobot+LingBot-VLA训推全流程
> 项目网站：https://technology.robbyant.com/lingbot-vla
> 技术报告：https://arxiv.org/pdf/2601.18692

---

## 总览

```
环境搭建 → 机械臂组装校准 → 摄像头连接 → 遥操作录制数据 →
→ VLA 预训练模型加载 → 后训练微调 → 仿真验证 → 开环验证 → 真机推理
```

---

## 一、环境搭建

1. 安装 Miniconda（已完成）
2. 创建虚拟环境
   ```
   conda create -y -n lerobot python=3.10
   conda activate lerobot
   ```
3. 安装 ffmpeg
   ```
   conda install ffmpeg=7.1.1 -c conda-forge -y
   ```
4. 安装 LeRobot + feetech 驱动
   ```
   cd lerobot
   pip install -e ".[feetech]"
   ```
5. 验证安装：`python` 下能 `import lerobot`、`import scservo_sdk`、`torch.cuda.is_available()` 返回 True

---

## 二、机械臂组装与校准

- SO-ARM101 机械臂硬件组装
- 连接 Dynamixel 舵机
- 获取串口号（Windows 设备管理器查看 COM 口）
- 运行校准脚本标定舵机零位

---

## 三、摄像头连接

- 连接 USB 摄像头
- 确认摄像头的摄像头索引（通常 0 或 1）
- 测试画面采集是否正常

---

## 四、遥操作录制示教数据集

- 使用游戏手柄/手机进行遥操作
- 录制多条示教轨迹（episode）
- 使用 LeRobotDataset v3 格式存储

---

## 五、VLA 模型后训练微调

- 选择预训练模型：LingBot-VLA
- 下载预训练权重（魔搭社区 / HuggingFace）
- 配置训练参数（数据集路径、episode 数、epoch、batch size 等）
- 执行 `lerobot-train` 进行微调

---

## 六、验证与推理

1. **仿真验证**：在仿真环境中验证微调后模型的策略
2. **开环验证**：用录制的数据集评估模型预测准确率
3. **真机推理**：加载微调模型，控制真实 SO-ARM101 机械臂

---

## 参考资源

| 资源 | 链接 |
|------|------|
| LingBot-VLA 开源代码 | https://github.com/Robbyant/lingbot-vla |
| 模型权重（魔搭） | https://www.modelscope.cn/collections/Robbyant/LingBot-VLA |
| 模型权重（HuggingFace） | https://huggingface.co/collections/robbyant/lingbot-vla |
| 技术报告 | https://arxiv.org/pdf/2601.18692 |
| 矽递 LeRobot 仓库 | https://github.com/Seeed-Projects/lerobot |
| 子豪兄知识库 | https://zihao-ai.feishu.cn/wiki/space/7589642043471924447 |

---

## 当前进度

| 步骤 | 状态 | 备注 |
|---|---|---|
| 环境搭建 | ✅ 已完成 | conda 环境、pip install -e ".[feetech]"、ffmpeg、CUDA 可用 |
| 舵机中位校准 | ✅ 已完成 | 12 个舵机全部校准至 ~2048 中位 |
| 主动臂组装 | ✅ 已完成 | FD 调试工具逐个关节测试通过 |
| 从动臂组装 | ✅ 已完成 | FD 调试工具逐个关节测试通过 |
| 摄像头 | ✅ 已测试 | 双摄像头确认：腕部（索引 1）+ 海康俯拍（索引 2） |
| LeRobot 标定 | ✅ 已完成 | 标定文件存项目 calibration/ 目录 |
| 遥操作 | ✅ 已测试 | 双摄像头 640×480 通过，略有卡顿但可接受 |
| HuggingFace 配置 | ✅ 已完成 | yaojiaming，Write token 已登录，录制后自动上传 |
| 采集数据集 | ✅ 已完成 | V2 共 66 条 Pick and place，双摄像头 640×480@30fps，26934 帧，已上传 HF |
| 训练模型 | ✅ 已完成 | ACT 算法，40K 步，loss 7.43→0.11，模型 206MB，保存于 `outputs/train/pick_place_act_v2/` |
| 真机推理 | ✅ 已完成 | 闭环跑通，物块置于合适初始位姿可稳定完成 Pick-and-place |

## 阶段性结论

已打通「环境搭建 → 组装标定 → 遥操作录制 → 训练 → 真机推理」完整闭环。真机推理效果依赖物块初始位姿落在训练分布内——置于合适位姿可稳定完成 Pick-and-place；初始位姿超出训练范围（OOD）时会出现抖动/抓取失败，这是 ACT 小模型 + 66 条数据的固有局限，而非训练或推理代码问题。

## 后续方向

- **换更强模型**：SmolVLA 等 VLA 模型，支持语言指令、泛化更强（需云 GPU）
- **云 GPU 训练**：本机 RTX 3060 6GB 显存有限，可租云 GPU 跑更大模型
- **扩充数据**：更多示教条数、覆盖更多场景与初始位姿，提升 OOD 鲁棒性
- **双系统 Linux**：装双系统以运行官方 `lerobot-eval`（Windows 上 placo FK/IK 库装不了）

