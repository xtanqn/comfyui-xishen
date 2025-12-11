import os
import subprocess
import platform
import time
import threading
from datetime import datetime, timedelta

class XishenShutdownTimerAdvancedNode:
    # 类变量用于存储活动计时器
    active_timers = {}
    timer_lock = threading.Lock()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_value": ("STRING", {"forceInput": True}),  # 输入接口，只能通过连线接收其他节点的输出
                "batch_number": ("STRING", {"default": "10", "multiline": False}),  # 批次（手动填写）
                "action": (["shutdown", "restart", "sleep", "hibernate"], {"default": "shutdown"}),  # 系统操作类型
                "time_type": (["countdown", "specific_time"], {"default": "countdown"}),  # 时间设置类型
                "countdown_seconds": ("INT", {"default": 600, "min": 0, "max": 86400, "step": 1}),  # 倒计时时间（秒）
                "target_time": ("STRING", {"default": "23:00", "description": "格式: HH:MM"}),  # 目标时间
                "enable_timer": ("BOOLEAN", {"default": True, "label_on": "启用", "label_off": "禁用"}),  # 启用/禁用计时器
                "cancel_timer": ("BOOLEAN", {"default": False, "label_on": "取消", "label_off": "不取消"}),  # 取消计时器
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "timer_info")  # 输出接口，返回状态信息和计时器详情
    FUNCTION = "check_and_control"
    CATEGORY = "🍡Comfyui-xishen"

    def get_system_command(self, action, delay):
        """根据系统类型和操作类型返回相应的命令"""
        system = platform.system()
        
        if system == "Windows":
            if action == "shutdown":
                return ["shutdown", "/s", "/t", str(delay)]
            elif action == "restart":
                return ["shutdown", "/r", "/t", str(delay)]
            elif action == "sleep":
                # Windows的睡眠没有延迟参数，需要立即执行
                return ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
            elif action == "hibernate":
                # Windows的休眠没有延迟参数，需要立即执行
                return ["shutdown", "/h"]
        elif system == "Darwin":  # macOS
            # 确保延迟至少为1分钟
            minutes = max(1, delay // 60)
            if action == "shutdown":
                return ["sudo", "shutdown", "-h", f"+{minutes}"]
            elif action == "restart":
                return ["sudo", "shutdown", "-r", f"+{minutes}"]
            elif action == "sleep":
                # macOS的睡眠没有延迟参数，需要立即执行
                return ["pmset", "sleepnow"]
        elif system == "Linux":
            # 确保延迟至少为1分钟
            minutes = max(1, delay // 60)
            if action == "shutdown":
                return ["sudo", "shutdown", "-h", f"+{minutes}"]
            elif action == "restart":
                return ["sudo", "shutdown", "-r", f"+{minutes}"]
            elif action == "sleep":
                # Linux的睡眠没有延迟参数，需要立即执行
                return ["systemctl", "suspend"]
            elif action == "hibernate":
                # Linux的休眠没有延迟参数，需要立即执行
                return ["systemctl", "hibernate"]
        
        return None

    def calculate_wait_time(self, time_type, countdown_seconds, target_time):
        """计算等待时间"""
        if time_type == "countdown":
            return countdown_seconds
        else:
            try:
                # 解析目标时间
                target_hour, target_minute = map(int, target_time.split(":"))
                now = datetime.now()
                target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                
                # 如果目标时间已过，设置为明天
                if target <= now:
                    target += timedelta(days=1)
                
                return int((target - now).total_seconds())
            except ValueError:
                raise ValueError("目标时间格式错误，请使用HH:MM格式")

    def timer_thread(self, timer_id, action, wait_time, cmd):
        """计时器线程函数"""
        try:
            # 直接执行系统命令，不使用Python的time.sleep
            with self.timer_lock:
                if timer_id in self.active_timers:
                    del self.active_timers[timer_id]
                    subprocess.run(cmd, shell=True, check=True)
        except Exception as e:
            print(f"计时器线程错误: {str(e)}")
            with self.timer_lock:
                if timer_id in self.active_timers:
                    del self.active_timers[timer_id]

    def check_and_control(self, input_value, batch_number, action, time_type, countdown_seconds, target_time, enable_timer, cancel_timer):
        # 检查取消计时器选项
        if cancel_timer:
            # 取消系统级别的定时任务
            system = platform.system()
            try:
                if system == "Windows":
                    # Windows取消定时关机/重启命令
                    subprocess.run(["shutdown", "/a"], shell=True, check=False)
                elif system in ["Darwin", "Linux"]:
                    # macOS/Linux取消定时关机/重启命令
                    subprocess.run(["sudo", "shutdown", "-c"], shell=True, check=False)
            except Exception as e:
                print(f"取消系统任务时出错: {str(e)}")
                
            # 清除并停止Python层面的计时器
            with self.timer_lock:
                active_count = len(self.active_timers)
                # 遍历所有活动计时器
                for timer_id, timer_info in list(self.active_timers.items()):
                    # 尝试停止线程（如果有线程对象）
                    if "thread" in timer_info:
                        try:
                            # 注意：Python没有直接的线程停止方法，这里只是标记为取消
                            # 在线程函数中会检查timer_id是否仍然存在于active_timers中
                            print(f"取消计时器 {timer_id}")
                        except Exception as e:
                            print(f"停止计时器 {timer_id} 时出错: {str(e)}")
                # 清除所有计时器记录
                self.active_timers.clear()
            return (f"✅ 已取消所有 {active_count} 个活动计时器和系统级定时任务", "无活动计时器")

        # 检查是否启用计时器
        if not enable_timer:
            return ("ℹ️ 计时器已禁用", "无活动计时器")

        # 批次校验逻辑 - 仅在倒计时模式下需要
        if time_type == "countdown":
            if input_value.strip() != batch_number.strip() or input_value.strip() == "":
                return (f"ℹ️ 当前运行为第 '{input_value}'批 未达到设定的 '{batch_number}' 批次，暂不执行任务", "无活动计时器")

        try:
            # 计算等待时间
            wait_time = self.calculate_wait_time(time_type, countdown_seconds, target_time)
            if wait_time < 0:
                return ("❌ 无效的等待时间", "无活动计时器")

            # 获取系统命令
            system = platform.system()  # 获取当前系统类型
            cmd = self.get_system_command(action, wait_time)
            if cmd is None:
                return (f"❌ 不支持的操作系统或操作类型", "无活动计时器")

            # 计算执行时间
            action_time = datetime.now() + timedelta(seconds=wait_time)
            
            # 生成计时器ID
            timer_id = threading.get_ident()

            # 取消现有计时器
            with self.timer_lock:
                self.active_timers.clear()
                
                # 对于需要延迟的操作，直接执行系统命令（系统会处理延迟）
                # 对于没有延迟参数的操作（睡眠/休眠），如果需要延迟，使用Python的time.sleep
                if wait_time == 0:
                    subprocess.run(cmd, shell=True, check=True)
                    return (f"✅ 已立即执行 {action} 操作", "无活动计时器")
                else:
                    # 检查操作类型是否支持系统级延迟
                    if system in ["Windows"] and action in ["shutdown", "restart"]:
                        # Windows的关机/重启支持系统级延迟，直接执行命令
                        subprocess.run(cmd, shell=True, check=False)
                    elif system in ["Darwin", "Linux"] and action in ["shutdown", "restart"]:
                        # macOS/Linux的关机/重启支持系统级延迟，直接执行命令
                        subprocess.run(cmd, shell=True, check=False)
                    else:
                        # 对于睡眠/休眠等不支持系统级延迟的操作，使用Python的time.sleep
                        def delayed_action():
                            time.sleep(wait_time)
                            with self.timer_lock:
                                if timer_id in self.active_timers:
                                    del self.active_timers[timer_id]
                                    subprocess.run(cmd, shell=True, check=True)
                        
                        timer_thread = threading.Thread(
                            target=delayed_action,
                            daemon=True
                        )
                        timer_thread.start()
                    
                    # 保存计时器信息
                    self.active_timers[timer_id] = {
                        "action": action,
                        "wait_time": wait_time,
                        "action_time": action_time,
                        "thread": timer_thread if 'timer_thread' in locals() else None
                    }
            
            # 准备返回信息
            if time_type == "countdown":
                time_info = f"倒计时 {wait_time} 秒"
            else:
                time_info = f"目标时间 {target_time}"
            
            status = f"✅ 定时任务已设置 - {time_info}"
            timer_info = f"将在 {action_time.strftime('%Y-%m-%d %H:%M:%S')} 执行 {action} 操作"
            
            return (status, timer_info)
            
        except Exception as e:
            return (f"❌ 发生错误: {str(e)}", "无活动计时器")

NODE_CLASS_MAPPINGS = {
    "XishenShutdownTimerAdvanced": XishenShutdownTimerAdvancedNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenShutdownTimerAdvanced": "定时关机高级-xishen",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']