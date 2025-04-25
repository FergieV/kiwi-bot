from typing import List, Any
from .base import Command

class MovementCommand(Command):
    """Handles movement-related commands."""
    
    def __init__(self, bot: Any):
        super().__init__(bot)
        self.name = "move"
        self.aliases = ["walk", "run", "go"]
        self.description = "Move your character in a direction"
        self.usage = "!move <direction> [steps]"
        self.cooldown = 0.5  # 500ms cooldown
        
    async def execute(self, account_id: str, args: List[str]) -> None:
        if not args:
            await self.bot.send_message(account_id, "Please specify a direction (nw, sw, ne, se)")
            return
            
        direction = args[0].lower()
        steps = 1
        if len(args) > 1:
            try:
                steps = int(args[1])
            except ValueError:
                await self.bot.send_message(account_id, "Invalid number of steps")
                return
                
        if direction not in ["nw", "sw", "ne", "se"]:
            await self.bot.send_message(account_id, "Invalid direction. Use nw, sw, ne, or se")
            return
            
        # Get character position
        char = self.bot.get_character(account_id)
        if not char:
            await self.bot.send_message(account_id, "Character not found")
            return
            
        # Calculate new position
        x, y = char.position
        if direction == "nw":
            x -= steps
            y -= steps
        elif direction == "sw":
            x -= steps
            y += steps
        elif direction == "ne":
            x += steps
            y -= steps
        elif direction == "se":
            x += steps
            y += steps
            
        # Check if new position is valid
        if not self.bot.is_valid_position(x, y):
            await self.bot.send_message(account_id, "Cannot move there")
            return
            
        # Update position
        char.position = (x, y)
        await self.bot.send_message(account_id, f"Moved {direction} {steps} step(s)") 