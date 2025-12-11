import random
import os
import json

class XishenThemePromptNode:
    @classmethod
    def INPUT_TYPES(s):
        # 在Python端直接加载JSON文件，提供完整的选项列表以解决验证错误
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(current_dir, "..", "web", "extensions", "xishen_theme_prompts.json")
        
        primary_categories = ["Loading..."]
        secondary_categories = ["Please select main..."]
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if data:
                primary_categories = list(data.keys())
                # 返回所有二级分类的并集，确保任何选择都能通过验证
                all_secondary_categories = []
                for categories in data.values():
                    all_secondary_categories.extend(categories)
                # 去重
                secondary_categories = list(set(all_secondary_categories))
                # 如果没有二级分类，使用默认值
                if not secondary_categories:
                    secondary_categories = ["None"]
        except Exception as e:
            print(f"❌ 加载分类数据失败: {e}")
        
        return {
            "required": {
                "primary_category": (primary_categories,),
                "secondary_category": (secondary_categories,),
                "control_option": (["设置生效", "选项随机", "全部随机"], {"default": "设置生效"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("category_name",)
    FUNCTION = "get_category_name"
    CATEGORY = "🍡Comfyui-xishen"

    def get_category_name(self, primary_category, secondary_category, control_option, seed):
        # 注意：这里我们再次读取文件，或者你可以将数据缓存到全局
        # 为了演示简单，这里假设数据通过前端传递，
        # 但为了安全和"随机"逻辑，最好还是后端再读一次
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(current_dir, "..", "web", "extensions", "xishen_theme_prompts.json")
        data = {}
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 加载分类数据失败: {e}")
            return ("")

        result = ""

        if control_option == "全部随机":
            all_items = [item for sublist in data.values() for item in sublist]
            result = random.choice(all_items) if all_items else ""
            
        elif control_option == "选项随机":
            if primary_category in data:
                result = random.choice(data[primary_category])
            else:
                result = "Category Error"
                
        else: # 设置生效
            # 如果是固定模式，直接输出前端传来的 secondary_category
            result = secondary_category

        print(f"🎯 主题提示词输出: {primary_category} -> {result}")
        return (result,)

NODE_CLASS_MAPPINGS = {
    "XishenThemePromptNode": XishenThemePromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenThemePromptNode": "主题提示词-xishen",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']