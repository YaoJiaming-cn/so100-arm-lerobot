"""验证 LeRobot 环境是否安装完整"""
import lerobot
import scservo_sdk
import torch

print(f'lerobot 版本: {lerobot.__version__}')
print(f'PyTorch 版本: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
print('环境验证通过')
