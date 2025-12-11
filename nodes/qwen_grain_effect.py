import torch
import numpy as np
from PIL import Image
from nodes import MAX_RESOLUTION

# 定义节点类，用于给图像添加电影颗粒效果
class Qwen_Image_Grain_Effect:
    """
    为图像添加电影颗粒效果，模拟胶片摄影的颗粒质感
    """
    # 定义节点分类
    CATEGORY = "🍡Comfyui-xishen"
    # 定义节点名称
    NAME = "🍉Image-颗粒质感"
    # 定义节点描述
    DESCRIPTION = "为图像添加电影颗粒效果，模拟胶片摄影的颗粒质感"

    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数
        """
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图像
                "颗粒尺寸": ("FLOAT", {
                    "default": 0.6,       # 默认值
                    "min": 0.25,          # 最小值
                    "max": 2.0,           # 最大值
                    "step": 0.05,         # 调节步长
                    "display": "slider"   # 滑块显示
                }),
                "颗粒强度": ("FLOAT", {
                    "default": 0.5,       # 默认值
                    "min": 0.0,           # 最小值
                    "max": 10.0,          # 最大值
                    "step": 0.05,         # 调节步长
                    "display": "slider"   # 滑块显示
                }),
                "颗粒饱和度": ("FLOAT", {
                    "default": 0.7,       # 默认值
                    "min": 0.0,           # 最小值
                    "max": 2.0,           # 最大值
                    "step": 0.05,         # 调节步长
                    "display": "slider"   # 滑块显示
                }),
                "暗部颗粒": ("FLOAT", {
                    "default": 0.0,       # 默认值
                    "min": 0.0,           # 最小值
                    "max": 0.5,           # 最大值
                    "step": 0.01,         # 调节步长
                    "display": "slider"   # 滑块显示
                }),
                "seed": ("INT", {
                    "default": 0,          # 默认值
                    "min": 0,              # 最小值
                    "step": 1,             # 调节步长
                }),
            },
        }

    # 定义输出类型
    RETURN_TYPES = ("IMAGE",)
    # 定义输出名称
    RETURN_NAMES = ("IMAGE",)
    # 定义节点执行的函数
    FUNCTION = "add_grain_effect"

    def add_grain_effect(self, image, 颗粒尺寸, 颗粒强度, 颗粒饱和度, 暗部颗粒, seed):
        """
        为图像添加电影颗粒效果
        
        参数:
            image: 输入图像张量
            颗粒尺寸: 颗粒的大小，0.25-2，数值越大颗粒越粗
            颗粒强度: 颗粒的明显程度，0-10，数值越高颗粒感越强
            颗粒饱和度: 颗粒的色彩饱和度，0-2，数值越高色彩越鲜艳
            暗部颗粒: 暗部区域的颗粒控制，0-0.5，值为0时不做额外调整
            seed: 随机种子
        
        返回:
            处理后的图像张量
        """
        # 设置随机种子，确保颗粒效果可复现
        np.random.seed(seed)
        torch.manual_seed(seed)
        
        # 将图像转换为numpy数组处理
        # 原始图像形状: (batch_size, height, width, channels)
        batch_size, height, width, channels = image.shape
        
        # 初始化输出列表
        result_images = []
        
        # 遍历每个图像进行处理
        for b in range(batch_size):
            # 获取单个图像
            img = image[b].numpy()
            
            # 调整图像范围到[0, 1]
            img = np.clip(img, 0, 1)
            
            # 计算颗粒大小（基于图像尺寸和颗粒尺寸参数）
            grain_size = max(1, int(颗粒尺寸 * 2))
            
            # 创建随机噪声（颗粒）
            # 生成基础噪声
            noise = np.random.rand(height, width, channels)
            
            # 根据颗粒尺寸调整噪声
            if grain_size > 1:
                # 对噪声进行下采样和上采样，模拟不同大小的颗粒
                from scipy.ndimage import zoom
                noise = zoom(noise, (grain_size, grain_size, 1), order=0)
                noise = zoom(noise, (1/grain_size, 1/grain_size, 1), order=0)
            
            # 调整噪声到合适的范围
            noise = (noise - 0.5) * 2  # 调整到[-1, 1]范围
            
            # 计算暗部增强因子
            # 对于暗部区域（像素值低的区域），增强颗粒效果
            # 首先计算图像的亮度分量
            luminance = np.dot(img[..., :3], [0.299, 0.587, 0.114])
            # 计算暗部因子，亮度越低，因子越大
            dark_factor = 1.0 + (1.0 - luminance) * 暗部颗粒 * 2.0
            
            # 将暗部因子扩展到3通道
            dark_factor = np.repeat(dark_factor[:, :, np.newaxis], channels, axis=2)
            
            # 应用暗部因子到噪声
            noise = noise * dark_factor
            
            # 调整颗粒饱和度
            # 如果饱和度为0，将噪声转换为灰度
            if 颗粒饱和度 == 0:
                noise_gray = np.dot(noise[..., :3], [0.299, 0.587, 0.114])
                noise = np.repeat(noise_gray[:, :, np.newaxis], channels, axis=2)
            # 如果饱和度不为0，调整噪声的色彩饱和度
            elif 颗粒饱和度 != 1:
                # 计算噪声的灰度版本
                noise_gray = np.dot(noise[..., :3], [0.299, 0.587, 0.114])
                noise_gray = np.repeat(noise_gray[:, :, np.newaxis], channels, axis=2)
                # 插值调整饱和度
                noise = noise_gray + 颗粒饱和度 * (noise - noise_gray)
            
            # 应用颗粒强度
            noise = noise * (颗粒强度 / 10.0)
            
            # 将噪声添加到原始图像
            result = img + noise
            
            # 确保结果在[0, 1]范围内
            result = np.clip(result, 0, 1)
            
            # 将处理后的图像添加到结果列表
            result_images.append(result)
        
        # 将结果转换回张量
        result_tensor = torch.from_numpy(np.stack(result_images)).float()
        
        return (result_tensor,)

# 节点映射，用于在ComfyUI中注册节点
NODE_CLASS_MAPPINGS = {
    "🍉Image-颗粒质感": Qwen_Image_Grain_Effect,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "🍉Image-颗粒质感": "🍉Image-颗粒质感-xishen",
}