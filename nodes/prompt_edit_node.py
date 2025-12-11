#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编辑提示词节点 - 交互式文本编辑工具

功能：
1. 暂停工作流执行，等待用户编辑提示词
2. 支持多行文本编辑，保持原始文本格式
3. 提供完整的编辑界面，包括确认和停止功能
4. 与ComfyUI前端无缝集成，实时更新编辑内容
5. 支持超时机制，避免无限等待

使用场景：
- 需要在工作流执行过程中手动调整提示词
- 对自动生成的提示词进行精细化编辑
- 在批量处理中需要人工干预的场景

技术特点：
- 使用WebSocket实现前后端实时通信
- 支持异步消息处理
- 提供工作流中断功能
- 兼容ComfyUI官方API
"""

"""
ComfyUI Prompt Edit Node
A node that pauses execution and allows users to edit the prompt text before continuing.
"""

import time
import uuid
import server
from aiohttp import web
import aiohttp
import asyncio
import logging

# Global storage for pending prompts
pending_prompts = {}

class XishenPromptEditNode:
    """
    A node that receives text input, pauses execution, and waits for user to edit the text.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "forceInput": True,  # 强制通过连线输入
                }),
                "edited_text_widget": ("STRING", {
                    "multiline": True,  # 多行文本框
                    "default": "",
                    "dynamicPrompts": False
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("edited_text",)
    FUNCTION = "edit_prompt"
    CATEGORY = "🍡Comfyui-xishen"
    OUTPUT_NODE = True

    def __init__(self):
        self.type = "Prompt_Edit"

    def edit_prompt(self, text, edited_text_widget, unique_id=None, prompt=None, extra_pnginfo=None):
        """
        Main function that pauses execution and waits for user input.
        """
        # Generate a unique session ID for this execution
        session_id = str(uuid.uuid4())

        # Use edited_text_widget if it has content, otherwise use incoming text
        if edited_text_widget and edited_text_widget.strip():
            final_text = edited_text_widget
        else:
            final_text = text

        # Store the initial text
        pending_prompts[session_id] = {
            "text": text,
            "unique_id": unique_id,
            "edited_text": final_text,
            "confirmed": False
        }

        # Send session_id and text to frontend (store it on the node)
        prompt_server = server.PromptServer.instance

        # Use asyncio to send the message
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

            if loop is not None:
                # We're in an async context, create a task
                asyncio.create_task(
                    prompt_server.send_sync(
                        "prompt_edit_session",
                        {
                            "session_id": session_id,
                            "node_id": unique_id,
                            "text": text
                        },
                        None  # Send to all clients instead of specific client_id
                    )
                )
            else:
                # We're not in an async context, use run_coroutine_threadsafe
                asyncio.run_coroutine_threadsafe(
                    prompt_server.send_sync(
                        "prompt_edit_session",
                        {
                            "session_id": session_id,
                            "node_id": unique_id,
                            "text": text
                        },
                        None  # Send to all clients instead of specific client_id
                    ),
                    prompt_server.loop
                )
        except Exception as e:
            print(f"Error sending prompt edit session: {e}")

        # Wait for user to confirm (polling approach)
        timeout = 3600  # 1 hour timeout
        start_time = time.time()

        while not pending_prompts[session_id]["confirmed"]:
            time.sleep(0.1)  # Poll every 100ms

            # Check if workflow should be stopped
            if pending_prompts[session_id].get("stopped"):
                print(f"Workflow stopped for session {session_id}")
                # Clean up
                del pending_prompts[session_id]
                # Return an empty string instead of raising exception
                # This allows the workflow to stop gracefully without node errors
                return ("",)

            # Check timeout
            if time.time() - start_time > timeout:
                print(f"Prompt edit timeout for session {session_id}")
                # Clean up
                del pending_prompts[session_id]
                raise Exception("编辑超时（1小时）")

        # Get the edited text
        edited_text = pending_prompts[session_id]["edited_text"]

        # Clean up
        del pending_prompts[session_id]

        return {
            "ui": {"text": [edited_text]},
            "result": (edited_text,)
        }

# Add server routes for handling user interactions
def add_routes(routes):
    """
    Add API routes for the prompt edit functionality.
    """
    
    @routes.post('/prompt_edit/update')
    async def update_prompt(request):
        """
        Update the edited text for a session.
        """
        try:
            data = await request.json()
            session_id = data.get("session_id")
            edited_text = data.get("edited_text")
            
            if session_id in pending_prompts:
                pending_prompts[session_id]["edited_text"] = edited_text
                return web.json_response({"status": "success"})
            else:
                return web.json_response(
                    {"status": "error", "message": "Session not found"},
                    status=404
                )
        except Exception as e:
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    @routes.post('/prompt_edit/confirm')
    async def confirm_prompt(request):
        """
        Confirm the edited text and continue execution.
        """
        try:
            data = await request.json()
            session_id = data.get("session_id")
            edited_text = data.get("edited_text")
            
            if session_id in pending_prompts:
                pending_prompts[session_id]["edited_text"] = edited_text
                pending_prompts[session_id]["confirmed"] = True

                return web.json_response({"status": "success"})
            else:
                return web.json_response(
                    {"status": "error", "message": "Session not found"},
                    status=404
                )
        except Exception as e:
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    @routes.post('/prompt_edit/cancel')
    async def cancel_prompt(request):
        """
        Cancel button just closes the dialog, workflow continues waiting.
        """
        try:
            data = await request.json()
            session_id = data.get("session_id")

            if session_id in pending_prompts:
                # Don't do anything - just acknowledge the cancel
                # The workflow will continue waiting for user to click "Continue" button
                return web.json_response({"status": "success"})
            else:
                return web.json_response(
                    {"status": "error", "message": "Session not found"},
                    status=404
                )
        except Exception as e:
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    @routes.post('/prompt_edit/stop')
    async def stop_workflow(request):
        """
        Stop the current workflow execution using ComfyUI's official interrupt API.
        """
        try:
            data = await request.json()
            session_id = data.get("session_id")

            if session_id in pending_prompts:
                # Set a flag to indicate we need to stop the workflow
                pending_prompts[session_id]["stopped"] = True
                pending_prompts[session_id]["confirmed"] = True
            
            # Use ComfyUI's official interrupt API to stop the workflow
            try:
                # Get the current server instance to determine the port dynamically
                prompt_server = server.PromptServer.instance
                
                if prompt_server and hasattr(prompt_server, 'port'):
                    # Use the dynamically determined port
                    interrupt_url = f"http://localhost:{prompt_server.port}/interrupt"
                else:
                    # Fallback to default port if we can't get the server instance
                    logging.warning("Could not get server instance or port, falling back to default port 8188")
                    interrupt_url = "http://localhost:8188/interrupt"
                    
                async with aiohttp.ClientSession() as session:
                    async with session.post(interrupt_url) as response:
                        if response.status == 200:
                            logging.info("Workflow interrupted successfully using official API")
                        else:
                            logging.warning(f"Official interrupt API returned status: {response.status}")
            except Exception as interrupt_e:
                logging.error(f"Error calling official interrupt API: {interrupt_e}")
            
            if session_id in pending_prompts:
                return web.json_response({"status": "success"})
            else:
                return web.json_response(
                    {"status": "error", "message": "Session not found"},
                    status=404
                )
        except Exception as e:
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )

# Register routes with the server
try:
    prompt_server = server.PromptServer.instance
    if prompt_server is not None:
        add_routes(prompt_server.routes)
except Exception as e:
    print(f"Warning: Could not register Prompt_Edit routes: {e}")

# Register the node
NODE_CLASS_MAPPINGS = {
    "XishenPromptEditNode": XishenPromptEditNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XishenPromptEditNode": "编辑提示词-xishen"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']