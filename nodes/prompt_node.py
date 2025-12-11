#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常用提示词节点 - 随机生成分类提示词

功能：
1. 提供预设的分类提示词系统，支持两级分类
2. 一级分类：女性、男性、风景、建筑、动漫
3. 二级分类：微距、长焦、广角、人文摄影等23种风格
4. 支持随机种子控制，可重复性生成相同提示词
5. 从外部JSON文件读取提示词库，方便维护和扩展

使用方法：
- 选择一级分类和二级分类
- 设置种子值（0为随机，非0为固定）
- 自动生成对应风格的随机提示词
"""

import json
import os
import random

class XishenCommonPromptNode:
    @classmethod
    def INPUT_TYPES(cls):
        # 定义一级分类和二级分类
        primary_categories = ["女性", "男性", "风景", "建筑", "动漫"]
        secondary_categories = ["微距", "长焦", "广角", "人文摄影", "夜景摄影", "国画", "油画", "水彩", "素描", "版画", "工笔画", "浮世绘", "莫奈印象派", "梵高后印象派", "赛博朋克", "蒸汽波", "暗黑系", "治愈系", "极简主义", "波普艺术", "哥特风", "洛丽塔", "复古风"]
        
        return {
            "required": {
                "primary_category": (primary_categories, {"default": "女性"}),
                "secondary_category": (secondary_categories, {"default": "微距"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_text",)
    FUNCTION = "generate_prompt"
    CATEGORY = "🍡Comfyui-xishen"

    def generate_prompt(self, primary_category, secondary_category, seed):
        # 构建JSON文件路径
        json_path = os.path.join(os.path.dirname(__file__), "..", "web", "extensions", "xishen_prompts.json")
        
        try:
            # 读取JSON文件
            with open(json_path, "r", encoding="utf-8") as f:
                prompts_data = json.load(f)
            
            # 验证一级分类是否存在
            if primary_category not in prompts_data:
                print(f"一级分类不存在！primary_category={primary_category}")
                return ("",)
            
            # 验证二级分类是否存在
            if secondary_category not in prompts_data[primary_category]:
                print(f"二级分类不存在！primary_category={primary_category}, secondary_category={secondary_category}")
                return ("",)
            
            # 获取该分类下的所有提示词
            prompts = prompts_data[primary_category][secondary_category]
            
            if not prompts:
                print(f"该分类下没有提示词！primary_category={primary_category}, secondary_category={secondary_category}")
                return ("",)
            
            # 使用种子初始化随机数生成器
            # 如果种子为0，则使用系统随机种子
            if seed == 0:
                selected_prompt = random.choice(prompts)
            else:
                rng = random.Random(seed)
                selected_prompt = rng.choice(prompts)
            
            # 增加调试信息
            print(f"当前primary_category: {primary_category}, secondary_category: {secondary_category}, selected_prompt: {selected_prompt[:50]}...")
            
            return (selected_prompt,)
            
        except Exception as e:
            print(f"读取或处理提示词时出错：{e}")
            return ("",)

NODE_CLASS_MAPPINGS = {
    "XishenCommonPromptNode": XishenCommonPromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenCommonPromptNode": "常用提示词-xishen",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']