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
