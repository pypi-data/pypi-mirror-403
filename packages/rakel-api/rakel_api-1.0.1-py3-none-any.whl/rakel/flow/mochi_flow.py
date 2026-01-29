"""
 * . mochimochi . [ FLOW :: mochi_flow ]
 * (  .  )  declarative & soft logic
 * o . . . o
"""

from typing import Union, Callable, Any, Dict, Optional

class MochiFlow:
    def __init__(self, name: str):
        # . check
        self.name = name
        self.steps: Dict[str, dict] = {}
        self.entry_step: Optional[str] = None

    def start(self, name: str, message: Union[str, Callable[[dict], str]]) -> 'MochiFlow':
        # . action
        self.steps[name] = {"name": name, "message": message}
        self.entry_step = name
        return self

    def ai(self, name: str, prompt: str) -> 'MochiFlow':
        # . action
        self.steps[name] = {"name": name, "type": "ai", "message": prompt}
        return self

    def action(self, name: str, handler: Callable[[dict], Any]) -> 'MochiFlow':
        # . action
        self.steps[name] = {"name": name, "type": "action", "handler": handler}
        return self

    def ask(self, name: str, message: Union[str, Callable[[dict], str]], next_step: str = None) -> 'MochiFlow':
        # . action
        self.steps[name] = {"name": name, "type": "ask", "message": message, "next": next_step}
        
        # . return
        return self

    def end(self, name: str, message: Union[str, Callable[[dict], str]]) -> 'MochiFlow':
        # . action
        self.steps[name] = {"name": name, "message": message}
        
        # . return
        return self

    def get_entry(self) -> Optional[str]:
        # . return
        return self.entry_step
