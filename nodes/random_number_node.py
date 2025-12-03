import random

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
    CATEGORY = "utils/xishen"

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
NODE_CLASS_MAPPINGS = {
    "XishenRandomIntegerNode": XishenRandomIntegerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenRandomIntegerNode": "Random/Sequence Integer to Text (Xishen)",
}