#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能展示文本节点 - 格式化文本输出

功能：
1. 智能处理多行文本输入，支持列表输入
2. 自动将输入文本转换为ComfyUI前端可显示的格式
3. 处理复杂嵌套文本结构，确保正确显示
4. 支持文本内容的格式化和清理
5. 更新工作流中的文本显示组件

特点：
- 自动处理换行符，将多行文本转换为嵌套数组结构
- 过滤空行，保持显示内容的整洁
- 支持列表输入和复杂数据结构
- 与ComfyUI前端ShowText组件完美兼容
"""

class XishenSmartDisplayNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    FUNCTION = "notify"
    CATEGORY = "🍡Comfyui-xishen"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (True,)

    def notify(self, text, unique_id=None, extra_pnginfo=None):
        # 处理多行文本，生成ShowText前端期望的嵌套数组结构 [[line1], [line2], ...]
        processed_text = []
        
        # 由于INPUT_IS_LIST=True，ComfyUI会自动将输入包装成数组
        if isinstance(text, list):
            # 遍历数组中的每个元素
            for item in text:
                # 如果元素是字符串且包含换行符
                if isinstance(item, str) and '\n' in item:
                    # 按换行符分割字符串，过滤空行
                    lines = [line.strip() for line in item.split('\n') if line.strip()]
                    # 转换为ShowText前端期望的嵌套数组结构 [[line1], [line2], ...]
                    processed_text.extend([[line] for line in lines])
                # 如果元素是字符串但不包含换行符
                elif isinstance(item, str):
                    processed_text.append([item])
                # 如果元素已经是数组（嵌套结构）
                elif isinstance(item, list):
                    # 确保每个子元素也是数组
                    for subitem in item:
                        if isinstance(subitem, str):
                            processed_text.append([subitem])
                        else:
                            processed_text.append(subitem)
        # 如果text不是数组（理论上不会发生，因为INPUT_IS_LIST=True）
        elif isinstance(text, str):
            if '\n' in text:
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                processed_text.extend([[line] for line in lines])
            else:
                processed_text.append([text])
        
        # 更新workflow中的widgets_values
        if unique_id is not None and extra_pnginfo is not None:
            if not isinstance(extra_pnginfo, list):
                print("Error: extra_pnginfo is not a list")
            elif (
                not isinstance(extra_pnginfo[0], dict)
                or "workflow" not in extra_pnginfo[0]
            ):
                print("Error: extra_pnginfo[0] is not a dict or missing 'workflow' key")
            else:
                workflow = extra_pnginfo[0]["workflow"]
                node = next(
                    (x for x in workflow["nodes"] if str(x["id"]) == str(unique_id[0])),
                    None,
                )
                if node:
                    node["widgets_values"] = [processed_text]

        return {"ui": {"text": processed_text}, "result": (processed_text,)}

# 注册节点
NODE_CLASS_MAPPINGS = {
    "XishenSmartDisplayNode": XishenSmartDisplayNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenSmartDisplayNode": "智能展示文本-xishen",
}
