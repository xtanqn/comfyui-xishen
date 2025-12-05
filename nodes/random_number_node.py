import random
import re
import torch
import comfy.model_management

class XishenRandomIntegerNode:
    def __init__(self):
        self.current_sequence_value = None
        self.last_min = None
        self.last_max = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "min_value": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "max_value": ("INT", {"default": 10, "min": -10000, "max": 10000}),
                "mode": (["random", "sequence"], {"default": "random"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("number_text", "number_int")
    FUNCTION = "generate_number"
    CATEGORY = "xishen"  # 修改为 xishen，这样在搜索时输入 "xishen" 就能找到节点

    def generate_number(self, min_value, max_value, mode, seed):
        if min_value > max_value:
            min_value, max_value = max_value, min_value
            
        if mode == "random":
            # 随机模式
            random.seed(seed)
            result = random.randint(min_value, max_value)
        else:  # sequence 模式
            # 顺序模式
            if (self.current_sequence_value is None or 
                min_value != self.last_min or 
                max_value != self.last_max):
                # 如果是第一次或范围改变了，重新初始化
                self.current_sequence_value = min_value
                self.last_min = min_value
                self.last_max = max_value
            else:
                # 递增，如果超过最大值则回到最小值
                self.current_sequence_value += 1
                if self.current_sequence_value > max_value:
                    self.current_sequence_value = min_value
            
            result = self.current_sequence_value
            
        return (str(result), result)

# 注册节点
class XishenCommonResolutionNode:
    def __init__(self):
        self.device = comfy.model_management.intermediate_device()

    @classmethod
    def INPUT_TYPES(cls):
        ratio_order = [
            "1:1",
            "4:3", "3:2", "16:10", "16:9", "21:9",
            "3:4", "2:3", "9:16", "9:21", "其他",
        ]

        ratio_map = {
            "1:1": [
                "1024x1024", "1280x1280", "1536x1536",
                "1080x1080", "600x600", "480x480", "240x240",
            ],
            "4:3": ["1152x864", "1472x1104", "1728x1296"],
            "3:4": [
                "864x1152", "1104x1472", "1296x1728",
                "1242x1660", "1080x1440", "750x1000",
            ],
            "3:2": ["1248x832", "1536x1024", "1872x1248"],
            "2:3": ["832x1248", "1024x1536", "1248x1872"],
            "16:10": ["1280x800", "1146x717"],
            "16:9": [
                "1280x720", "1536x864", "1920x1080", "2048x1152",
                "1080x608", "864x516",
            ],
            "9:16": ["720x1280", "1080x1920", "1152x2048"],
            "21:9": ["1344x576", "1680x720", "2016x864"],
            "9:21": ["576x1344", "720x1680", "864x2016"],
            "其他": [
                "1920x1184", "980x300", "900x383", "600x600",
                "1080x300", "1536x768", "1500x500",
            ],
        }

        web_marks = {
            # 1:1
            "1080x1080": "Instagram动态视频、Facebook轮播视频广告、LinkedIn移动端、小红书正方形视频；广告：Instagram轮播视频广告推荐",
            "600x600": "Facebook插播视频广告方形视频最小分辨率、Instagram常规方形视频最小推荐分辨率；微信公众号名片二维码推荐分辨率",
            "480x480": "快手头像标准分辨率",
            "240x240": "微信公众号头像、B站头像（官方最小尺寸）",
            # 16:9
            "1920x1080": "YouTube标准视频推荐；西瓜号/百家号/腾讯视频横屏视频常用；<br>2. 社交平台：微博超粉横版、快手横版推荐；<br>3. 其他：快手主页背景图",
            "1280x720": "B站横屏常用；西瓜号/优酷号横屏基础；<br>2. Facebook动态视频、LinkedIn视频、Twitter推文视频",
            "1080x608": "微信视频号横版封面推荐、快手横版封面推荐",
            "864x516": "快手视频封面标准",
            # 16:10
            "1280x800": "B站视频封面推荐",
            "1146x717": "B站标准视频封面（官方推荐最优尺寸）",
            # 9:16
            "1080x1920": "YouTube Shorts；B站竖屏常用；TikTok、Instagram Stories/Reels、Facebook Stories、小红书竖版、抖音竖版；封面：快手竖版封面建议",
            "720x1280": "抖音、快手等竖屏平台基础分辨率（低码率适配）",
            # 3:4
            "1242x1660": "小红书图文竖版封面（高清适配）",
            "1080x1440": "小红书视频竖版封面",
            "750x1000": "小红书主页封面",
            # 其他
            "1920x1184": "微信朋友圈封面（适配全屏无裁剪）",
            "980x300": "微博主页封面图",
            "900x383": "微信公众号推文封面（官方推荐）",
            "1080x300": "微信公众号内容引导图、B站竖版封面常用",
            "1536x768": "LinkedIn封面图（PC端最优适配）",
            "1500x500": "Twitter封面图（官方推荐高清尺寸）",
            # 保留原有标注
            "1024x1024": "[公众号]",
            "1280x1280": "[公众号]",
            "1536x1536": "[公众号]",
        }

        options = []
        for ratio in ratio_order:
            dims = ratio_map.get(ratio, [])
            def sort_key(d):
                w, h = map(int, d.split("x"))
                return (w if w >= h else h)
            dims = sorted(dims, key=sort_key)
            for d in dims:
                mark = web_marks.get(d, "")
                label = f"{d} ( {ratio} )" + (f" {mark}" if mark else "")
                options.append(label)

        return {"required": {
            "aspect_ratio": (ratio_order, {"default": "16:9"}),
            "resolution": (options, ),
            "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
        }}

    RETURN_NAMES = ("Latent", "Width", "Height")
    RETURN_TYPES = ("LATENT", "INT", "INT")
    FUNCTION = "generate"
    CATEGORY = "xishen"

    def generate(self, aspect_ratio, resolution, batch_size=1):
        dimensions = resolution.split(' ')[0]
        width, height = map(int, dimensions.split('x'))

        width = int((width // 16) * 16)
        height = int((height // 16) * 16)

        latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=self.device)

        return ({"samples": latent}, width, height)

class XishenCommonPromptNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "category": (["人物", "风景"], {"default": "人物"}),
                "prompt_key": (["a", "b"], {"default": "a"}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("number_text", "number_int")
    FUNCTION = "generate_prompt"
    CATEGORY = "xishen"

    def generate_prompt(self, category, prompt_key):
        mapping = {
            "人物": {"a": "a", "b": "b"},
            "风景": {"a": "a", "b": "b"},
        }
        text = mapping.get(category, {}).get(prompt_key, "")
        idx = 0 if prompt_key == "a" else 1
        return (text, idx)

class XishenRemoveEmptyLinesNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "remove_empty_lines"
    CATEGORY = "xishen"

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
    "XishenCommonPromptNode": XishenCommonPromptNode,
    "XishenRemoveEmptyLinesNode": XishenRemoveEmptyLinesNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenRandomIntegerNode": "随机整数-xishen",
    "XishenCommonResolutionNode": "常用分辨率-xishen",
    "XishenCommonPromptNode": "常用提示词-xishen",
    "XishenRemoveEmptyLinesNode": "去空行-xishen",
}
