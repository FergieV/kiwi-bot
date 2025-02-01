import asyncio
import json
import os
from typing import Dict, List
from .bot import KiwiBot

class BotManager:
    def __init__(self):
        self.bots: Dict[str, KiwiBot] = {}
        self.tasks: Dict[str, List[asyncio.Task]] = {}
        
    async def load_configs(self):
        conf_dir = os.path.join(os.path.dirname(__file__), '..', 'conf')
        for file in os.listdir(conf_dir):
            if file.endswith('.conf'):
                with open(os.path.join(conf_dir, file)) as f:
                    config = json.load(f)
                    bot_name = os.path.splitext(file)[0]
                    self.bots[bot_name] = KiwiBot(config, bot_name)

    async def start_bot(self, bot: KiwiBot):
        """Start a single bot with its required tasks"""
        await bot.connect()  # This now handles its own tasks

    async def stop_bot(self, bot_name: str):
        """Gracefully stop a bot and its tasks"""
        if bot_name in self.bots:
            bot = self.bots[bot_name]
            bot.running = False
            if bot_name in self.tasks:
                for task in self.tasks[bot_name]:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self.tasks[bot_name]
            bot.disconnect()

    async def start_all(self):
        """Start all bots concurrently"""
        await asyncio.gather(
            *(self.start_bot(bot) for bot in self.bots.values())
        )
    
    async def stop_all(self):
        """Stop all bots gracefully"""
        await asyncio.gather(
            *(self.stop_bot(name) for name in list(self.bots.keys()))
        ) 