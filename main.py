import asyncio
import logging
import os
import datetime
import json
import re
from pathlib import Path
from typing import Optional

class KiwiBot:
    """
    KiwiBot client for Furcadia
    Handles connection, message parsing, and command processing
    """
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.running = True
        
        # Bot information
        self.app_name = 'kiwibot'
        self.app_vers = '0.7.0'
        
        # Load credentials from config
        self.email = self.config['account'][0]['email']
        self.character = self.config['account'][0]['character']
        self.password = self.config['account'][0]['password']
        self.colors = self.config['account'][0]['colors']
        self.desc = f"{self.config['account'][0]['desc']} [{self.app_name} {self.app_vers}]"
        self.owner = self.config['account'][0]['owner']
        
        # Configure logging
        self._setup_logger()
        
    def _load_config(self, config_path: str) -> dict:
        """Load and parse the configuration file"""
        with open(config_path, 'r') as f:
            return json.load(f)
            
    def _setup_logger(self):
        """Configure logging with timestamp-based filename"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        timestamp = int(datetime.datetime.now().timestamp())
        log_file = log_dir / f'kiwibot_{timestamp}.log'
        
        logging.basicConfig(
            filename=str(log_file),
            encoding='utf-8',
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%m-%d-%Y %H:%M:%S%z'
        )
        logging.info('Bot starting up...')

    async def connect(self):
        """Establish connection to Furcadia server"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.config['connection'][0]['server'],
                self.config['connection'][0]['port']
            )
            self.connected = True
            logging.info('Connected to server')
        except Exception as e:
            logging.error(f'Connection failed: {e}')
            raise

    async def send_message(self, msg: str):
        """Send a message to the server"""
        if not self.connected:
            return
            
        # Messages that shouldn't be logged
        print_exclusions = {
            '>', '<', 'm 1', 'm 3', 'm 7', 'm 9',
            'lie', 'sit', 'stand', 'vascodagama',
            f'account {self.email} {self.character} {self.password}',
            f'color {self.colors}',
            f'desc {self.desc}'
        }
        
        if msg not in print_exclusions:
            print(f'[SEND] {msg}')
            logging.info(f'Sent: {msg}')
            
        self.writer.write(f'{msg}\n'.encode('iso-8859-1'))
        await self.writer.drain()

    async def handle_whisper(self, msg: str):
        """Process whisper messages and handle commands from owner"""
        whisperer = re.search(r'\<name[^\>]+\>([^\<]+)\<\/name\>', msg).group(1)
        message = re.search(r'\"([^\"]+)\"', msg).group(1)
        
        print(f'[RECV] {whisperer} (whisper): {message}')
        
        if whisperer != self.owner:
            return
            
        # Handle owner commands
        if message.startswith('cmd:'):
            cmd = message[4:]
            if cmd == 'quit':
                await self.send_message('\"Disconnecting...')
                await asyncio.sleep(5)
                self.running = False
            else:
                await self.send_message(cmd)
                
        elif message.startswith('move:'):
            moves = message[5:].split(',')
            move_aliases = {'nw': 'm 7', 'ne': 'm 9', 'sw': 'm 1', 'se': 'm 3'}
            
            for move in moves:
                move = move.strip()
                cmd = move_aliases.get(move, move)
                await self.send_message(cmd)
                await asyncio.sleep(0.75)
                
        elif message.startswith('say:'):
            await self.send_message(f'\"{message[4:]}')

    async def stay_alive(self):
        """Keep connection alive by sending periodic messages"""
        while self.running:
            await self.send_message('>')
            await asyncio.sleep(1)
            await self.send_message('<')
            await asyncio.sleep(300)  # 5 minutes

    async def run(self):
        """Main bot loop"""
        try:
            await self.connect()
            # Start keepalive task
            asyncio.create_task(self.stay_alive())
            
            while self.running:
                data = await self.reader.readline()
                msg = data.decode('iso-8859-1').strip()
                
                # Handle server messages
                if msg == 'Dragonroar':
                    await self.send_message(f'account {self.email} {self.character} {self.password}')
                    await self.send_message(f'color {self.colors}')
                    await self.send_message(f'desc {self.desc}')
                    continue
                    
                if msg in ['&&&&&&&&&&&&&', ']q']:
                    await self.send_message('vascodagama')
                    continue
                
                # Handle chat messages
                if msg.startswith('('):
                    if '<font color=\'whisper\'>' in msg:
                        await self.handle_whisper(msg)
                    elif '<font color=\'emote\'>' in msg:
                        # Handle emotes
                        emote = re.search(r'\(\<font\scolor\=\'emote\'\>\<name\sshortname\=\'[^\']+\'\>([^\<]+)\<\/name\>\s(.*)\<\/font\>', msg)
                        print(f'[RECV] {emote.group(1)} {emote.group(2)}')
                    else:
                        # Handle normal chat
                        chat = re.search(r'\(\<name\sshortname\=\'[^\']+\'\>([^\<]+)\<\/name\>\:\s(.*)', msg)
                        if chat:
                            print(f'[RECV] {chat.group(1)}: {chat.group(2)}')
                
        except Exception as e:
            logging.error(f'Error in main loop: {e}')
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            self.connected = False

async def main():
    """Entry point for the bot"""
    config_path = Path('conf/bot.conf')
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return
        
    bot = KiwiBot(str(config_path))
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutting down...")