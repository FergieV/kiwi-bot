from typing import List, Any
from .base import Command
import asyncio

class SystemCommand(Command):
    """Handles system-related commands."""
    
    def __init__(self, bot: Any):
        super().__init__(bot)
        self.name = "system"
        self.aliases = ["sys", "cmd"]
        self.description = "System control commands"
        self.usage = "!system <command>"
        self.cooldown = 0.0  # No cooldown for system commands
        
    async def execute(self, account_id: str, args: List[str]) -> None:
        if not args:
            await self.bot.send_message(account_id, "Please specify a system command")
            return
            
        command = args[0].lower()
        
        if command == "quit":
            await self.bot.send_message(account_id, "\"Disconnecting...")
            await asyncio.sleep(5)
            self.bot.running = False
        else:
            await self.bot.send_message(command) 