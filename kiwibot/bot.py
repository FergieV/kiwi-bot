import asyncio
import logging
from datetime import datetime
import re
from typing import Optional

class KiwiBot:
    def __init__(self, config: dict, name: str):
        self.config = config
        self.name = name
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.running = False
        self.setup_logger()
        self.email = config['account'][0]['email']
        self.character = config['account'][0]['character']
        self.password = config['account'][0]['password']
        self.colors = config['account'][0]['colors']
        self.desc = config['account'][0]['desc']
        self.owner = config['account'][0]['owner']
        self.app_name = 'kiwibot'
        self.app_vers = '0.7.0-alpha'
        self.desc = self.desc + f' [{self.app_name} {self.app_vers}]'
        
        # Add signal for UI updates
        self.message_received = asyncio.Event()
        self.last_message = None
        self.start_time = None
        self.message_count = 0
        self.last_message_time = None
        self.message_handlers = {}  # Will be set by UI
        
    def setup_logger(self):
        self.logger = logging.getLogger(f'bot.{self.name}')
        
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.config['connection'][0]['server'],
                self.config['connection'][0]['port']
            )
            self.connected = True
            self.start_time = datetime.now()
            self.logger.info(f'Connected to server')
        except Exception as e:
            self.logger.error(f'Connection failed: {e}')
            raise

    async def send_message(self, msg: str):
        if not self.connected:
            return
        self.writer.write(f'{msg}\n'.encode('iso-8859-1'))
        await self.writer.drain()
        self.logger.debug(f'Sent: {msg}')

    async def read_message(self) -> str:
        data = await self.reader.readline()
        msg = data.decode('iso-8859-1').strip()
        self.logger.debug(f'Received: {msg}')
        return msg

    async def run(self):
        self.running = True
        try:
            while self.running:
                msg = await self.read_message()
                await self.handle_message(msg)
        except Exception as e:
            self.logger.error(f'Error in bot loop: {e}')
        finally:
            self.disconnect()

    def disconnect(self):
        if self.writer:
            self.writer.close()
        self.connected = False
        self.running = False 

    async def handle_message(self, msg: str):
        """Handle incoming messages from the server"""
        self.message_count += 1
        self.last_message_time = datetime.now()
        self.last_message = msg
        self.message_received.set()
        
        if msg == 'Dragonroar':
            await self.send_message(f'account {self.email} {self.character} {self.password}')
            await self.send_message(f'color {self.colors}')
            await self.send_message(f'desc {self.desc}')
            return

        if msg in ['&&&&&&&&&&&&&', ']q']:
            await self.send_message('vascodagama')
            return

        # Handle whispers
        whispers = re.compile(r'\(<font color=\'whisper\'>')
        if whispers.match(msg):
            await self.handle_whisper(msg)
            return

        # Handle emotes
        emotes = re.compile(r'\(<font color=\'emote\'>')
        if emotes.match(msg):
            await self.handle_emote(msg)
            return

        # Handle normal chat
        saying = re.compile(r'\(\<name\sshortname\=\'[^\']+\'\>[^\<]+\<\/name\>\:\s(.*)')
        if saying.match(msg):
            await self.handle_chat(msg)
            return

    async def handle_whisper(self, msg: str):
        whisperer = re.search(r'\<name[^\>]+\>([^\<]+)\<\/name\>', msg)
        whisperer = whisperer.group(1)
        message = re.search(r'\"([^\"]+)\"', msg)
        message = message.group(1)
        formatted = f'{whisperer} (whisper): {message}'
        self.logger.info(formatted)
        if 'chat' in self.message_handlers:
            self.message_handlers['chat'](formatted)

    async def handle_emote(self, msg: str):
        emote = re.search(r'\(\<font\scolor\=\'emote\'\>\<name\sshortname\=\'[^\']+\'\>([^\<]+)\<\/name\>\s(.*)\<\/font\>', msg)
        emoter = emote.group(1)
        emoted = emote.group(2)
        formatted = f'{emoter} {emoted}'
        self.logger.info(formatted)
        if 'chat' in self.message_handlers:
            self.message_handlers['chat'](formatted)

    async def handle_chat(self, msg: str):
        saying = re.search(r'\(\<name\sshortname\=\'[^\']+\'\>([^\<]+)\<\/name\>\:\s(.*)', msg)
        sayer = saying.group(1)
        said = saying.group(2)
        formatted = f'{sayer}: {said}'
        self.logger.info(formatted)
        if 'chat' in self.message_handlers:
            self.message_handlers['chat'](formatted)

    async def stay_alive(self):
        """Keep connection alive by sending periodic messages"""
        while self.running:
            await self.send_message('>')
            await asyncio.sleep(1)
            await self.send_message('<')
            await asyncio.sleep(300)  # 5 minutes 