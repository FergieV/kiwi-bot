import asyncio
import logging
from datetime import datetime
import re
from typing import Optional
from .__version__ import __version__, __title__

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
        self.app_name = __title__
        self.app_vers = __version__
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
            if self.connected:
                return
                
            self.reader, self.writer = await asyncio.open_connection(
                self.config['connection'][0]['server'],
                self.config['connection'][0]['port']
            )
            self.connected = True
            self.running = True
            self.start_time = datetime.now()
            self.logger.info(f'Connected to server')
            
            # Start the bot's main loop
            asyncio.create_task(self.run())
            asyncio.create_task(self.stay_alive())
            
        except Exception as e:
            self.logger.error(f'Connection failed: {e}')
            raise

    async def send_message(self, msg: str):
        if not self.connected:
            return
            
        # Add print exclusions like in original code
        print_exclusions = [
            '>',
            '<',
            'm 1',
            'm 3',
            'm 7',
            'm 9',
            'lie',
            'sit',
            'stand',
            'vascodagama',
            # Add credential commands to exclusions
            f'account {self.email} {self.character} {self.password}',
            f'color {self.colors}',
            f'desc {self.desc}'
        ]
        
        # Log the message unless it's excluded
        if msg not in print_exclusions:
            formatted = f'[SEND] {msg}'
            self.logger.info(formatted)
            if 'chat' in self.message_handlers:
                self.message_handlers['chat'](formatted)

        # Encode and send the message
        self.writer.write(f'{msg}\n'.encode('iso-8859-1'))
        await self.writer.drain()
        self.logger.debug(f'Sent: {msg}')

    async def read_message(self) -> str:
        data = await self.reader.readline()
        msg = data.decode('iso-8859-1').strip()
        if self.config.get('debug_mode', False):  # First debug print
            if 'debug' in self.message_handlers:
                self.message_handlers['debug'](f'{msg}')
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
        self.writer = None
        self.reader = None
        self.start_time = None
        
    async def handle_message(self, msg: str):
        """Handle incoming messages from the server"""
        self.message_count += 1
        self.last_message_time = datetime.now()
        self.last_message = msg
        self.message_received.set()
        
        # Handle authentication and vascodagama first
        if msg == 'Dragonroar':
            await self.send_message(f'account {self.email} {self.character} {self.password}')
            await self.send_message(f'color {self.colors}')
            await self.send_message(f'desc {self.desc}')
            return

        # Fix vascodagama check
        if msg.startswith(']q') or msg == '&&&&&&&&&&&&&':
            await self.send_message('vascodagama')
            return

        # Handle chat messages (anything starting with parenthesis)
        if msg.startswith('('):
            formatted = msg[1:]  # Remove the leading parenthesis
            self.logger.info(formatted)
            if 'chat' in self.message_handlers:
                self.message_handlers['chat'](formatted)
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

        # Handle owner commands
        if whisperer == self.owner:
            if message.startswith('cmd:'):
                cmd = message[4:]
                if cmd == 'quit':
                    await self.send_message('\"Disconnecting...')
                    await asyncio.sleep(5)
                    self.disconnect()
                else:
                    await self.send_message(cmd)
                    
            elif message.startswith('move:'):
                moves = message[5:].split(',')  # Split into array of moves
                move_aliases = {
                    'nw': 'm 7',
                    'ne': 'm 9',
                    'sw': 'm 1',
                    'se': 'm 3',
                    '<': '<',  # Add direct mappings for special moves
                    '>': '>'
                }
                for move in moves:
                    move = move.strip()  # Remove any whitespace
                    if move in move_aliases:
                        await self.send_message(move_aliases[move])
                    else:
                        await self.send_message(move)
                    await asyncio.sleep(1)  # 1 second delay between moves
                    
            elif message.startswith('say:'):
                say = message[4:]
                await self.send_message(f'\"{say}')

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