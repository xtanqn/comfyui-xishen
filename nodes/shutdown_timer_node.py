import os
import subprocess
import platform

class XishenShutdownTimerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_value": ("STRING", {"forceInput": True}),  # 输入接口，只能通过连线接收其他节点的输出
                "batch_number": ("STRING", {"default": "10", "multiline": False}),  # 批次（手动填写）
                "countdown_time": ("INT", {"default": 600, "min": 0, "max": 86400, "step": 1}),  # 倒计时时间（手动填写，秒）
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)  # 输出接口，返回状态信息
    FUNCTION = "check_and_shutdown"
    CATEGORY = "🍡Comfyui-xishen"

    def check_and_shutdown(self, input_value, batch_number, countdown_time):
        # 检查输入值是否等于批次数字
        shutdown_delay = countdown_time
        if input_value.strip() == batch_number.strip() and input_value.strip() != "":
            try:
                # 根据不同的操作系统执行定时关机命令
                if platform.system() == "Windows":
                    # Windows系统使用shutdown命令
                    # /s 表示关机，/t 表示延迟时间（秒）
                    cmd = f"shutdown /s /t {shutdown_delay}"
                    subprocess.run(cmd, shell=True, check=True)
                    status = f"✅ 定时关机任务已设置，将在 {shutdown_delay} 秒后关机"
                elif platform.system() == "Darwin":
                    # macOS系统使用shutdown命令
                    cmd = f"shutdown -h +{shutdown_delay // 60}"
                    subprocess.run(cmd, shell=True, check=True)
                    status = f"✅ 定时关机任务已设置，将在 {shutdown_delay} 秒后关机"
                elif platform.system() == "Linux":
                    # Linux系统使用shutdown命令
                    cmd = f"shutdown -h +{shutdown_delay // 60}"
                    subprocess.run(cmd, shell=True, check=True)
                    status = f"✅ 定时关机任务已设置，将在 {shutdown_delay} 秒后关机"
                else:
                    status = f"❌ 不支持的操作系统: {platform.system()}"
            except subprocess.CalledProcessError as e:
                status = f"❌ 执行关机命令失败: {e}"
            except Exception as e:
                status = f"❌ 发生错误: {e}"
        else:
            # 如果值不匹配或为空，不执行关机命令
            status = f"ℹ️ 当前运行为第 '{input_value}'批 未达到设定的 '{batch_number}' 批次，暂不不执行关机任务"
            
        return (status,)

NODE_CLASS_MAPPINGS = {
    "XishenShutdownTimerNode": XishenShutdownTimerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenShutdownTimerNode": "定时关机-xishen",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
