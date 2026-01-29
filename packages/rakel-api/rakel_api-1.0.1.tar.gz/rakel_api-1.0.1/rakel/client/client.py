"""
 * . mochimochi . [ CLIENT :: client ]
 * (  .  )  pythonic & soft logic
 * o . . . o
"""

import asyncio
import json
import subprocess
import os
from typing import Callable, Any
from loguru import logger

from .flow.flow_manager import FlowManager
from .flow.mochi_flow import MochiFlow

class RakelClient:
    def __init__(self, node_path: str = "node", core_script: str = None):
        # . check
        self.node_path = node_path
        self.core_script = core_script or self._get_default_script()
        self.process = None
        self.handlers = {}
        self.callbacks = {}
        self.command_id = 0
        self.flows = FlowManager(self)
        self.ai_handler = None

    def handle_ai(self, handler: Callable[[str, dict], Any]):
        """🤖 Configura o handler de IA (Coringa)"""
        self.ai_handler = handler


    async def solve_ai(self, prompt_template: str, context: dict) -> str:
        """🧩 Resolve a intenção de IA usando o handler configurado"""
        # . check
        if not self.ai_handler:
             return "⚠️ IA não configurada ( . .)"
        
        # . action: Interpolate prompt
        prompt = prompt_template
        for key, value in context.items():
            if isinstance(value, str):
                prompt = prompt.replace(f"{{{key}}}", value)
             
        # . action: Call handler
        if asyncio.iscoroutinefunction(self.ai_handler):
             return await self.ai_handler(prompt, context)
        return self.ai_handler(prompt, context)

    async def send_sticker(self, jid: str, buffer: bytes):
        """🍡 Envia Sticker Mágico (convertido no lado Node.js)"""
        # . action
        import base64
        b64_data = base64.b64encode(buffer).decode('utf-8')
        buffer_param = { "type": "Buffer", "data": b64_data }
        return await self._send_command("sendSticker", {"jid": jid, "buffer": buffer_param})

    async def send_voice(self, jid: str, buffer: bytes):
        """🎤 Envia Áudio Mágico (convertido no lado Node.js)"""
        # . action
        import base64
        b64_data = base64.b64encode(buffer).decode('utf-8')
        buffer_param = { "type": "Buffer", "data": b64_data }
        return await self._send_command("sendVoice", {"jid": jid, "buffer": buffer_param})

    def _get_default_script(self):
        # . action
        # 1. Tenta caminho de desenvolvimento (monorepo)
        dev_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Utils/core-bridge.ts"))
        
        if os.path.exists(dev_path):
            return dev_path
            
        # 2. Tenta caminho de distribuição (pacote instalado)
        dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bridge/core-bridge.ts"))
        return dist_path

    async def connect(self):
        # . action
        # Note: In production we would use npx tsx or compile to JS
        self.process = await asyncio.create_subprocess_exec(
            self.node_path, "npx", "tsx", self.core_script,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # . log
        logger.info("🐍 Rakel-Python connecting to Node-Core... (☆^ー^☆)")
        
        # Start reading stdout
        asyncio.create_task(self._read_output())

    async def use_flow(self, jid: str, flow: MochiFlow):
        # . action
        await self.flows.start_flow(jid, flow)

    def on(self, event_name: str):
        # . action
        def decorator(func: Callable):
            self.handlers[event_name] = func
            return func
        return decorator

    async def send_message(self, jid: str, content: dict):
        # . action
        return await self._send_command("sendMessage", {"jid": jid, "content": content})

    async def _send_command(self, method: str, params: dict):
        # . action
        self.command_id += 1
        cmd_id = str(self.command_id)
        
        future = asyncio.get_event_loop().create_future()
        self.callbacks[cmd_id] = future
        
        cmd = json.dumps({"id": cmd_id, "method": method, "params": params})
        self.process.stdin.write(cmd.encode() + b"\n")
        await self.process.stdin.drain()
        
        return await future

    async def _read_output(self):
        # . action
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            
            try:
                msg = json.loads(line.decode())
                await self._handle_bridge_message(msg)
            except Exception as e:
                logger.error(f"Error parsing bridge message: {e} ( . .)")

    async def _handle_bridge_message(self, msg: dict):
        # . action
        m_type = msg.get("type")
        
        if m_type == "event":
            data = msg.get("data")
            name = msg.get("name")

            if name == "message":
                # Process flows first
                handled = await self.flows.handle_message(data)
                if handled:
                    return

            handler = self.handlers.get(name)
            if handler:
                await handler(data)
        
        elif m_type == "response":
            cb_id = msg.get("id")
            if cb_id in self.callbacks:
                future = self.callbacks.pop(cb_id)
                if "error" in msg:
                    future.set_exception(Exception(msg["error"]))
                else:
                    future.set_result(msg["result"])
