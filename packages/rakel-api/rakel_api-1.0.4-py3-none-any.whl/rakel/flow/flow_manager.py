"""
 * . mochimochi . [ FLOW :: flow_manager ]
 * (  .  )  stateful & soft logic
 * o . . . o
"""

from typing import Dict, Any, Optional
from rakel.flow.mochi_flow import MochiFlow
from loguru import logger

class FlowManager:
    def __init__(self, client):
        # . check
        self.client = client
        self.active_flows: Dict[str, dict] = {}

    async def handle_message(self, msg: dict) -> bool:
        # . check
        jid = msg.get("key", {}).get("remoteJid")
        if not jid or jid not in self.active_flows:
            return False

        # . action
        state = self.active_flows[jid]
        flow: MochiFlow = state["flow"]
        step_name = state["step"]
        data = state["data"]

        step = flow.steps.get(step_name)
        if not step:
            del self.active_flows[jid]
            return False

        # Collect data
        content = msg.get("message", {}).get("conversation", "")
        data[step_name] = content

        # Determine next step
        next_step_name = step.get("next") or self._get_next_default(flow, step_name)

        if next_step_name:
            await self._transition(jid, flow, next_step_name, data)
        else:
            del self.active_flows[jid]

        # . sweet return
        return True

    async def start_flow(self, jid: str, flow: MochiFlow):
        # . action
        entry = flow.get_entry()
        if entry:
            await self._transition(jid, flow, entry, {})

    async def _transition(self, jid: str, flow: MochiFlow, step_name: str, data: dict):
        # . action
        step = flow.steps.get(step_name)
        if not step:
            return

        # . log
        logger.debug(f"Mochi-Flow: {jid} transição para passo '{step_name}' (☆^ー^☆)")

        # 🃏 Processamento de Passos Especiais (Mochi-Magic)
        if step.get("type") == "ai":
            # Delegar resolução de IA para o Cliente (Coringa!)
            text = await self.client.solve_ai(step["message"], data)
            data[step_name] = text
            # Auto-Next
            return await self._auto_next(jid, flow, step_name, data)
            
        if step.get("type") == "action" and callable(step.get("handler")):
            # Executar ação customizada
            result = await step["handler"](data)
            data[step_name] = result
            # Auto-Next
            return await self._auto_next(jid, flow, step_name, data)

        # 📝 Mensagem Padrão
        message = step["message"]
        text = message(data) if callable(message) else message
        
        await self.client.send_message(jid, {"text": text})
        
        self.active_flows[jid] = {
            "flow": flow,
            "step": step_name,
            "data": data
        }

    async def _auto_next(self, jid: str, flow: MochiFlow, current_step: str, data: dict):
        next_step = self._get_next_default(flow, current_step)
        if next_step:
            await self._transition(jid, flow, next_step, data)
        else:
            del self.active_flows[jid]

    def _get_next_default(self, flow: MochiFlow, current: str) -> Optional[str]:
        # . action
        keys = list(flow.steps.keys())
        try:
            idx = keys.index(current)
            return keys[idx + 1] if idx + 1 < len(keys) else None
        except ValueError:
            return None
