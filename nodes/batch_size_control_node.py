import torch

class BatchSizeControl:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tensor": ("IMAGE,LATENT,MASK", {}),
                "batch_size": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    NAME = "批量控制-xishen"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("batch_size",)
    FUNCTION = "run"
    CATEGORY = "🍡Comfyui-xishen"
    OUTPUT_NODE = True

    def run(self, tensor, batch_size, unique_id, prompt, extra_pnginfo):
        # 从工作流元数据中获取输入类型
        node_list = extra_pnginfo["workflow"]["nodes"]
        cur_node = next(n for n in node_list if str(n["id"]) == unique_id)
        link_id = cur_node["inputs"][0]["link"]
        link = next(l for l in extra_pnginfo["workflow"]["links"] if l[0] == link_id)
        in_node_id, in_socket_id = link[1], link[2]
        in_node = next(n for n in node_list if n["id"] == in_node_id)
        input_type = in_node["outputs"][in_socket_id]["type"]

        # 获取tensor的实际batch_size
        actual_batch_size = 1

        if input_type == "IMAGE":
            actual_batch_size = tensor.shape[0] if hasattr(tensor, "shape") and len(tensor.shape) > 0 else 1
        elif input_type == "LATENT" or (type(tensor) is dict and "samples" in tensor):
            samples = tensor["samples"]
            actual_batch_size = samples.shape[0] if hasattr(samples, "shape") and len(samples.shape) > 0 else 1
        elif input_type == "MASK":
            actual_batch_size = tensor.shape[0] if hasattr(tensor, "shape") and len(tensor.shape) > 0 else 1

        # 根据用户输入决定最终的batch_size
        final_batch_size = actual_batch_size
        if batch_size > 0:
            final_batch_size = min(batch_size, actual_batch_size)

        return {
            "result": (final_batch_size,)
        }

NODE_CLASS_MAPPINGS = {
    "BatchSizeControl": BatchSizeControl,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchSizeControl": "批量控制-xishen",
}
