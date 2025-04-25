from typing import List, Any
from .base import Command

class SayCommand(Command):
    """Handles say commands."""
    
    def __init__(self, bot: Any):
        super().__init__(bot)
        self.name = "say"
        self.aliases = ["speak", "talk"]
        self.description = "Make the bot say something"
        self.usage = "!say <message>"
        self.cooldown = 0.5  # 500ms cooldown
        
    async def execute(self, account_id: str, args: List[str]) -> None:
        if not args:
            await self.bot.send_message(account_id, "Please provide a message to say")
            return
            
        message = " ".join(args)
        await self.bot.send_message(f'\"{message}') 