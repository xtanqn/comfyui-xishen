import torch
import numpy as np
from PIL import Image, ImageFilter
import torch.nn.functional as F

# 定义泛光效果节点类
class ImageBloomEffect:
    """
    🍭Image-泛光效果节点
    核心作用：给图像添加辉光效果，让图像中的高光区域产生柔和的扩散发光，增强画面的光感、梦幻感或真实感
    """
    
    # 设置节点分类，使用统一的项目分类
    CATEGORY = "🍡Comfyui-xishen"
    
    # 定义输入参数
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 待处理的原始图像（必填）
                "亮度下限": ("FLOAT", {
                    "default": 0.5,  # 默认值
                    "min": 0.0,       # 最小值
                    "max": 1.0,       # 最大值
                    "step": 0.1,      # 调节步长改为0.1
                    "display": "slider"  # 滑块显示
                }),
                "亮度上限": ("FLOAT", {
                    "default": 1.0,   # 默认值
                    "min": 0.0,       # 最小值
                    "max": 1.0,       # 最大值
                    "step": 0.1,      # 调节步长改为0.1
                    "display": "slider"  # 滑块显示
                }),
                "模糊类型": (["高斯模糊", "矩形", "光束"], {
                    "default": "高斯模糊"  # 默认模糊类型
                }),
                "扩散范围": ("INT", {
                    "default": 15,     # 默认值
                    "min": 0,          # 最小值
                    "max": 50,         # 最大值
                    "step": 1,         # 调节步长
                    "display": "slider"  # 滑块显示
                }),
                "高光亮度": ("FLOAT", {
                    "default": 1.0,    # 默认值
                    "min": 0.1,        # 最小值
                    "max": 50.0,       # 最大值
                    "step": 0.1,       # 调节步长
                    "display": "slider"  # 滑块显示
                }),
                "混合方式": (["屏幕混合", "相加", "相乘", "覆盖", "soft_light", "hard_light"], {
                    "default": "屏幕混合"  # 默认混合模式
                }),
                "强度衰减": ("FLOAT", {
                    "default": 0.5,    # 默认值
                    "min": 0.0,        # 最小值
                    "max": 1.0,        # 最大值
                    "step": 0.1,       # 调节步长
                    "display": "slider"  # 滑块显示
                }),
                "分辨率上限": ("INT", {
                    "default": 2048,   # 默认值
                    "min": 256,        # 最小值
                    "max": 2048,       # 最大值（修改为2048）
                    "step": 256        # 调节步长，移除滑块效果
                }),
            },
            "optional": {
                "mask": ("MASK",),  # 遮罩图像（可选）
            }
        }
    
    # 定义输出类型
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "MASK")
    RETURN_NAMES = ("modified_image", "highlights_image", "image", "mask")
    FUNCTION = "apply_bloom_effect"
    
    def apply_bloom_effect(self, image, 亮度下限=0.5, 亮度上限=1.0, 模糊类型="高斯模糊", 
                          扩散范围=15, 高光亮度=1.0, 混合方式="屏幕混合", 
                          强度衰减=0.5, 分辨率上限=2048, mask=None):
        """
        应用泛光效果的核心方法
        
        参数：
        - image: 待处理的原始图像
        - 亮度下限: 高光区域的亮度下限
        - 亮度上限: 高光区域的亮度上限
        - 模糊类型: 辉光的模糊类型
        - 扩散范围: 辉光的扩散范围
        - 高光亮度: 高光区域的基础亮度
        - 混合方式: 辉光与原图的混合方式
        - 强度衰减: 辉光的强度衰减
        - 分辨率上限: 模糊处理的分辨率上限
        - mask: 遮罩图像（可选）
        
        返回：
        - modified_image: 应用Bloom效果后的最终图像
        - highlights_image: 提取出的图像高光区域
        - image: 原始图像的直通输出
        - mask: 原始遮罩的直通输出
        """
        # 处理图像张量，确保在CPU上操作
        if image.device.type == "cuda":
            image = image.cpu()
        
        # 转换图像格式：从[0,1]范围的张量转换为PIL图像
        image_np = image.numpy().squeeze(0)  # 移除批次维度
        image_pil = Image.fromarray((image_np * 255).astype(np.uint8))
        
        # 提取图像的亮度通道（用于确定高光区域）
        image_gray = image_pil.convert("L")
        image_gray_np = np.array(image_gray) / 255.0
        
        # 根据亮度上下限提取高光区域
        # 创建高光掩码：亮度在[亮度下限, 亮度上限]之间的像素
        highlights_mask = np.zeros_like(image_gray_np)
        highlights_mask[image_gray_np >= 亮度下限] = 1.0
        
        # 对高光掩码进行渐变处理，使边缘更柔和
        if 亮度上限 > 亮度下限:
            highlights_mask[np.logical_and(image_gray_np >= 亮度下限, image_gray_np < 亮度上限)] = \
                (image_gray_np[np.logical_and(image_gray_np >= 亮度下限, image_gray_np < 亮度上限)] - 亮度下限) / (亮度上限 - 亮度下限)
        
        # 将高光掩码应用到原始图像，提取高光区域
        highlights_np = image_np * highlights_mask[..., np.newaxis]
        
        # 处理遮罩（如果提供）
        if mask is not None:
            if mask.device.type == "cuda":
                mask = mask.cpu()
            mask_np = mask.numpy().squeeze(0)  # 移除批次维度
            # 将遮罩应用到高光区域
            highlights_np = highlights_np * mask_np[..., np.newaxis]
        
        # 转换高光区域为PIL图像，用于后续模糊处理
        highlights_pil = Image.fromarray((highlights_np * 255).astype(np.uint8))
        
        # 根据分辨率上限调整图像大小，优化性能
        width, height = highlights_pil.size
        if width > 分辨率上限 or height > 分辨率上限:
            scale_factor = 分辨率上限 / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            highlights_pil = highlights_pil.resize((new_width, new_height), Image.LANCZOS)
        
        # 根据选择的模糊类型进行模糊处理
        if 模糊类型 == "高斯模糊":
            blurred_highlights = highlights_pil.filter(ImageFilter.GaussianBlur(radius=扩散范围))
        elif 模糊类型 == "矩形":
            blurred_highlights = highlights_pil.filter(ImageFilter.BoxBlur(radius=扩散范围))
        elif 模糊类型 == "光束":
            # 光束模糊效果（通过多次高斯模糊模拟）
            blurred_highlights = highlights_pil
            for i in range(3):
                blurred_highlights = blurred_highlights.filter(ImageFilter.GaussianBlur(radius=扩散范围 / (i + 1)))
        
        # 恢复原始大小（如果之前调整过）
        if width > 分辨率上限 or height > 分辨率上限:
            blurred_highlights = blurred_highlights.resize((width, height), Image.LANCZOS)
        
        # 转换模糊后的高光为numpy数组
        blurred_highlights_np = np.array(blurred_highlights) / 255.0
        
        # 调整高光亮度
        blurred_highlights_np = blurred_highlights_np * 高光亮度
        
        # 应用强度衰减
        blurred_highlights_np = blurred_highlights_np * 强度衰减
        
        # 将模糊后的高光与原始图像混合
        # 转换原始图像为numpy数组，确保格式一致
        original_image_np = np.array(image_pil) / 255.0
        
        # 根据选择的混合方式进行混合
        if 混合方式 == "屏幕混合":
            # 屏幕混合：1 - (1 - 原图) * (1 - 辉光)
            modified_image_np = 1.0 - (1.0 - original_image_np) * (1.0 - blurred_highlights_np)
        elif 混合方式 == "相加":
            # 相加混合：原图 + 辉光
            modified_image_np = original_image_np + blurred_highlights_np
        elif 混合方式 == "相乘":
            # 相乘混合：原图 * 辉光
            modified_image_np = original_image_np * (1.0 + blurred_highlights_np)
        elif 混合方式 == "覆盖":
            # 覆盖混合：根据原图亮度调整混合方式
            modified_image_np = np.where(original_image_np <= 0.5, 2 * original_image_np * blurred_highlights_np, 1.0 - 2 * (1.0 - original_image_np) * (1.0 - blurred_highlights_np))
        elif 混合方式 == "soft_light":
            # 柔光混合：类似柔光效果
            modified_image_np = np.where(blurred_highlights_np <= 0.5, original_image_np - (1.0 - 2.0 * blurred_highlights_np) * original_image_np * (1.0 - original_image_np), original_image_np + (2.0 * blurred_highlights_np - 1.0) * (np.sqrt(original_image_np) - original_image_np))
        elif 混合方式 == "hard_light":
            # 强光混合：类似强光效果
            modified_image_np = np.where(blurred_highlights_np <= 0.5, 2 * original_image_np * blurred_highlights_np, 1.0 - 2 * (1.0 - original_image_np) * (1.0 - blurred_highlights_np))
        
        # 确保像素值在[0, 1]范围内
        modified_image_np = np.clip(modified_image_np, 0.0, 1.0)
        
        # 转换回张量格式
        modified_image = torch.from_numpy(modified_image_np).unsqueeze(0).float()
        highlights_image = torch.from_numpy(highlights_np).unsqueeze(0).float()
        
        # 返回处理结果和直通输出
        return (modified_image, highlights_image, image, mask if mask is not None else torch.tensor([]))

# 定义节点映射，用于节点注册
NODE_CLASS_MAPPINGS = {
    "🍭Image-泛光效果": ImageBloomEffect
}

# 定义节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "🍭Image-泛光效果": "🍭Image-泛光效果-xishen"
}