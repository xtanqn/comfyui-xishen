#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
随机数与分辨率节点集合（后端）
random_number_node.py
"""

import random
import re
import torch
import comfy.model_management


class XishenRandomIntegerNode:
    def __init__(self):
        self.current_sequence_value = None
        self.last_min = None
        self.last_max = None
        self.last_reset_sequence = 0  # 跟踪上一次处理的reset_sequence值

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "min_value": ("INT", {"default": 1, "min": -10000, "max": 10000}),
                "max_value": ("INT", {"default": 50, "min": -10000, "max": 10000}),
                "mode": (["random", "sequence"], {"default": "sequence"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            # reset_sequence 作为 hidden 输入，仅由前端 JS 通过按钮触发时设置
            "hidden": {
                "reset_sequence": ("INT", {"default": 0}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("number_text", "number_int")
    FUNCTION = "generate_number"
    CATEGORY = "🍡Comfyui-xishen"

    def generate_number(self, min_value, max_value, mode, seed, reset_sequence=0):
        # 保证 min <= max
        if min_value > max_value:
            min_value, max_value = max_value, min_value

        # 随机模式
        if mode == "random":
            random.seed(seed)
            result = random.randint(min_value, max_value)
            return (str(result), result)

        # 序列模式
        # 转换reset_sequence为整数以确保类型正确
        reset_sequence = int(reset_sequence)
        
        # 如果reset_sequence为1或2且与上一次不同，重置为最小值
        # 这样1和2之间来回切换可以实现多次重置
        if reset_sequence in (1, 2) and reset_sequence != self.last_reset_sequence:
            self.current_sequence_value = min_value
            self.last_min = min_value
            self.last_max = max_value
            self.last_reset_sequence = reset_sequence  # 更新上一次的reset_sequence值
            return (str(self.current_sequence_value), self.current_sequence_value)
        
        # 只有当reset_sequence为1或2时才更新last_reset_sequence
        # 这样reset_sequence=0时不会清除之前的重置状态
        if reset_sequence in (1, 2):
            self.last_reset_sequence = reset_sequence

        # 如果 min/max 改变，自动重置
        if self.last_min != min_value or self.last_max != max_value:
            self.current_sequence_value = min_value
            self.last_min = min_value
            self.last_max = max_value
            return (str(self.current_sequence_value), self.current_sequence_value)

        # 第一次执行
        if self.current_sequence_value is None:
            self.current_sequence_value = min_value
            self.last_min = min_value
            self.last_max = max_value
            return (str(self.current_sequence_value), self.current_sequence_value)

        # 正常递增并循环
        self.current_sequence_value += 1
        if self.current_sequence_value > max_value:
            self.current_sequence_value = min_value

        return (str(self.current_sequence_value), self.current_sequence_value)


# 你的其他节点保持原样 —— 如果你原来文件较长请保留旧实现
class XishenCommonResolutionNode:
    def __init__(self):
        self.device = comfy.model_management.intermediate_device()

    @classmethod
    def INPUT_TYPES(cls):
        import math
        ratio_order = [
            "1:1",
            "4:3", "3:2", "16:10", "16:9", "21:9",
            "3:4", "2:3", "9:16", "9:21", "其他",
        ]
        # minimal placeholder to avoid syntax errors if you trimmed this file
        return {
            "required": {
                "aspect_ratio": (ratio_order, {"default": "16:9"}),
                "resolution": (["1024x1024"],),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
            }
        }

    RETURN_NAMES = ("Latent", "Width", "Height")
    RETURN_TYPES = ("LATENT", "INT", "INT")
    FUNCTION = "generate"
    CATEGORY = "🍡Comfyui-xishen"

    def generate(self, aspect_ratio, resolution, batch_size=1):
        dims = resolution.split(' ')[0]
        width, height = map(int, dims.split('x'))
        width = int((width // 16) * 16)
        height = int((height // 16) * 16)
        latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=self.device)
        return ({"samples": latent}, width, height)


class XishenRemoveEmptyLinesNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": ("STRING", {"default": "", "multiline": True})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "remove_empty_lines"
    CATEGORY = "🍡Comfyui-xishen"

    def remove_empty_lines(self, text):
        parts = re.findall(r"(.*?)(\r\n|\n|\r|$)", text)
        kept = []
        for content, sep in parts:
            if content.strip() != "":
                kept.append(content + sep)
        return ("".join(kept),)


NODE_CLASS_MAPPINGS = {
    "XishenRandomIntegerNode": XishenRandomIntegerNode,
    "XishenCommonResolutionNode": XishenCommonResolutionNode,
    "XishenRemoveEmptyLinesNode": XishenRemoveEmptyLinesNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenRandomIntegerNode": "随机整数-xishen",
    "XishenCommonResolutionNode": "常用分辨率-xishen",
    "XishenRemoveEmptyLinesNode": "去空行-xishen",
}
