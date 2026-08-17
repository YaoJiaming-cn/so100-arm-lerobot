# SO-ARM101 + LeRobot + LingBot-VLA 复现项目

低成本开源机械臂的 VLA 模型微调与真机部署。基于 SO-ARM101 开源机械臂、HuggingFace LeRobot 框架和 LingBot-VLA 视觉-语言-动作模型的端到端复现项目。目标是从硬件组装、遥操作示教、模型后训练微调到真机推理，打通具身智能的全流程。

## 参考资源

| 资源 | 链接 |
|---|---|
| LingBot-VLA 技术报告 | [arxiv.org/pdf/2601.18692](https://arxiv.org/pdf/2601.18692) |
| LingBot-VLA 开源代码 | [github.com/Robbyant/lingbot-vla](https://github.com/Robbyant/lingbot-vla) |
| 模型权重（魔搭） | [modelscope.cn/collections/Robbyant/LingBot-VLA](https://www.modelscope.cn/collections/Robbyant/LingBot-VLA) |
| 本项目训练模型权重 | [huggingface.co/yaojiaming/so100_pick_place_act_v2](https://huggingface.co/yaojiaming/so100_pick_place_act_v2) |
| LeRobot（矽递 fork） | [github.com/Seeed-Projects/lerobot](https://github.com/Seeed-Projects/lerobot) |
| 同济子豪兄知识库 | [zihao-ai.feishu.cn](https://zihao-ai.feishu.cn/wiki/space/7589642043471924447) |

## 复现流程

```
环境搭建 → 机械臂组装校准 → 摄像头连接 → 遥操作录制数据
→ VLA 预训练模型加载 → 后训练微调 → 仿真验证 → 真机推理
```

## 环境搭建

```bash
git clone --recurse-submodules <this-repo>
conda create -y -n lerobot python=3.10
conda activate lerobot
conda install ffmpeg=7.1.1 -c conda-forge -y
cd lerobot
pip install -e ".[feetech]"
```

## 项目结构

```
├── lerobot/              # LeRobot 子模块（矽递 fork v0.4.4）
├── calibration/          # 机械臂标定文件
├── datasets/             # 录制的数据集（本地备份）
├── outputs/              # 训练产物（模型权重、日志）
├── docs/
│   ├── commands.md       # 命令速查卡片
│   ├── servo-mapping.md  # 舵机对照表 + 串口号
│   ├── glossary.md       # 术语词典
│   ├── troubleshooting.md # 踩坑记录
│   └── LOG.md            # 每日工作日志
├── tests/camera/         # 摄像头测试脚本
├── tools/                # 飞特 FD 舵机调试工具
├── zihao-reference/      # 子豪兄知识库导出的参考教程
└── reproduction-plan.md  # 复现路线图与当前进度
```

## 当前进度

| 步骤 | 状态 |
|---|---|
| 环境搭建 | ✅ 已完成 |
| 舵机中位校准 | ✅ 已完成 |
| 主动臂组装 | ✅ 已完成 |
| 从动臂组装 | ✅ 已完成 |
| 摄像头 | ✅ 已测试 |
| LeRobot 标定 | ✅ 已完成 |
| 遥操作 | ✅ 已测试 |
| 采集数据集 | ✅ 已完成 | [yaojiaming/so100_pick_place_v2](https://huggingface.co/datasets/yaojiaming/so100_pick_place_v2)（66 条，双摄像头 640×480@30fps，26934 帧） |
| 训练模型 | ✅ 已完成 | ACT, 40K 步, loss 0.11, 206MB → [HF 模型仓库](https://huggingface.co/yaojiaming/so100_pick_place_act_v2) |
| 真机推理 | ✅ 已完成 | 闭环跑通，物块置于合适初始位姿可稳定完成 Pick-and-place |

## 阶段性结论

已打通「环境搭建 → 组装标定 → 遥操作录制 → 训练 → 真机推理」完整闭环。真机推理效果依赖物块初始位姿落在训练分布内——置于合适位姿可稳定完成 Pick-and-place；初始位姿超出训练范围（OOD）时会出现抖动/抓取失败，这是 ACT 小模型 + 66 条数据的固有局限，而非训练或推理代码问题。

## 下一步方向

- 换更强的 VLA 模型（如 SmolVLA，支持语言指令、泛化更强）
- 租云 GPU 训练（本机 RTX 3060 6GB 显存有限）
- 扩充示教数据、覆盖更多场景与初始位姿

## 演示视频

- [Lerobot + SO-ARM101 + ACT 复现全流程](https://www.bilibili.com/video/BV1oRbe6eEkv/)（Bilibili）

## 硬件配置

- **机械臂**：SO-ARM101（主动臂 + 从动臂）
- **舵机**：飞特 Feetech STS3215 串行总线舵机 ×12
- **摄像头**：海康威视 1080P USB 摄像头（俯拍）
- **操作系统**：Windows 11
- **GPU**：NVIDIA CUDA
