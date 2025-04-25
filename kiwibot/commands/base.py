from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

class Command(ABC):
    """Base class for all bot commands."""
    
    def __init__(self, bot: Any):
        self.bot = bot
        self.name = self.__class__.__name__.lower()
        self.aliases: list[str] = []
        self.description: str = ""
        self.usage: str = ""
        self.cooldown: float = 0.0  # seconds
        self.last_used: Dict[str, float] = {}  # account_id -> timestamp
    
    @abstractmethod
    async def execute(self, account_id: str, args: list[str]) -> None:
        """Execute the command.
        
        Args:
            account_id: The ID of the account executing the command
            args: List of command arguments
        """
        pass
    
    def can_execute(self, account_id: str) -> bool:
        """Check if the command can be executed (cooldown check).
        
        Args:
            account_id: The ID of the account trying to execute the command
            
        Returns:
            bool: True if the command can be executed, False otherwise
        """
        if self.cooldown <= 0:
            return True
            
        current_time = time.time()
        last_used = self.last_used.get(account_id, 0)
        
        if current_time - last_used < self.cooldown:
            return False
            
        self.last_used[account_id] = current_time
        return True
    
    def get_help(self) -> str:
        """Get help text for the command.
        
        Returns:
            str: Formatted help text
        """
        help_text = f"Command: {self.name}"
        if self.aliases:
            help_text += f"\nAliases: {', '.join(self.aliases)}"
        if self.description:
            help_text += f"\nDescription: {self.description}"
        if self.usage:
            help_text += f"\nUsage: {self.usage}"
        if self.cooldown > 0:
            help_text += f"\nCooldown: {self.cooldown}s"
        return help_text 