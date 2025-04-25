import asyncio
import logging
import os
import datetime
import json
import re
import argparse
from pathlib import Path
from typing import Optional, Dict
from kiwibot.__version__ import __version__, __title__, __description__
from db.config import initialize_database, get_account, get_connection_config, migrate_from_old_format, list_accounts
from kiwibot.commands.base import Command
from kiwibot.commands.movement import MovementCommand
from kiwibot.commands.say import SayCommand
from kiwibot.commands.system import SystemCommand

class KiwiBot:
    """
    KiwiBot client for Furcadia
    Handles connection, message parsing, and command processing
    """
    def __init__(self, account_id=None, account_name=None, debug: bool = False):
        self.account = get_account(account_id=account_id, name=account_name)
        self.connection = get_connection_config(account_id=account_id, account_name=account_name)
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.running = True
        self.debug = debug  # Store debug flag
        
        # Bot information
        self.app_name = __title__
        self.app_vers = __version__
        
        # Command handling
        self.commands: Dict[str, Command] = {}
        self._register_commands()
        
        # Load credentials from config
        if self.account:
            self.email = self.account.get('email', '')
            self.character = self.account.get('character', '')
            self.password = self.account.get('password', '')
            self.colors = self.account.get('colors', '')
            self.desc = f"{self.account.get('description', '')} [{self.app_name} v{self.app_vers}]"
            self.owner = self.account.get('owner', '')
        else:
            self.email = ''
            self.character = ''
            self.password = ''
            self.colors = ''
            self.desc = f"[{self.app_name} v{self.app_vers}]"
            self.owner = ''
        
        # Configure logging
        self._setup_logger()
            
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
            if not self.connection:
                logging.error('Connection configuration not found')
                raise ValueError('Connection configuration missing')
                
            server = self.connection.get('server', '')
            port = self.connection.get('port', 0)
            
            if not server or not port:
                logging.error('Server or port not configured')
                raise ValueError('Server configuration missing')
                
            self.reader, self.writer = await asyncio.open_connection(server, port)
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

    def _register_commands(self):
        """Register all available commands"""
        # Register movement command
        move_cmd = MovementCommand(self)
        self.commands[move_cmd.name] = move_cmd
        for alias in move_cmd.aliases:
            self.commands[alias] = move_cmd
            
        # Register say command
        say_cmd = SayCommand(self)
        self.commands[say_cmd.name] = say_cmd
        for alias in say_cmd.aliases:
            self.commands[alias] = say_cmd
            
        # Register system command
        sys_cmd = SystemCommand(self)
        self.commands[sys_cmd.name] = sys_cmd
        for alias in sys_cmd.aliases:
            self.commands[alias] = sys_cmd
    
    async def handle_command(self, account_id: str, command: str, args: list[str]) -> None:
        """Handle a command from the owner"""
        cmd = self.commands.get(command.lower())
        if not cmd:
            await self.send_message(account_id, f"Unknown command: {command}")
            return
            
        if not cmd.can_execute(account_id):
            await self.send_message(account_id, f"Command on cooldown. Please wait {cmd.cooldown}s")
            return
            
        try:
            await cmd.execute(account_id, args)
        except Exception as e:
            logging.error(f"Error executing command {command}: {e}")
            await self.send_message(account_id, f"Error executing command: {e}")

    async def handle_whisper(self, msg: str):
        """Process whisper messages and handle commands from owner"""
        whisperer = re.search(r'\<name[^\>]+\>([^\<]+)\<\/name\>', msg).group(1)
        message = re.search(r'\"([^\"]+)\"', msg).group(1)
        
        print(f'[RECV] {whisperer} (whisper): {message}')
        
        if whisperer != self.owner:
            return
            
        # Handle commands
        if message.startswith('!'):
            parts = message[1:].split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            await self.handle_command(self.account['id'], command, args)
        # Handle legacy commands
        elif message.startswith('cmd:'):
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
                
                # Print raw messages if in debug mode
                if self.debug:
                    print(f'[DEBUG] {msg}')
                
                # Handle server messages
                if msg == 'Dragonroar':
                    await self.send_message(f'account {self.email} {self.character} {self.password}')
                    await self.send_message(f'color {self.colors}')
                    await self.send_message(f'desc {self.desc}')
                    continue
                    
                if msg == '&&&&&&&&&&&&&' or msg.startswith(']q'):
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

def display_accounts():
    """Display a list of available account profiles"""
    accounts = list_accounts()
    
    if not accounts:
        print("No accounts configured. Run with --setup to create an account.")
        return False
        
    print("\nAvailable account profiles:")
    print("--------------------------")
    for account in accounts:
        print(f"  {account['id']}: {account['name']} ({account['character']})")
    print("\nUse --profile <name> or --account-id <id> to select an account.")
    return True

async def main():
    """Entry point for the bot"""
    parser = argparse.ArgumentParser(
        description=f'{__title__} v{__version__} - {__description__}'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode (print raw server messages)'
    )
    parser.add_argument(
        '-p', '--profile',
        help='Select account profile by name'
    )
    parser.add_argument(
        '-i', '--account-id',
        type=int,
        help='Select account profile by ID'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List available account profiles'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    initialize_database()
    
    # Try to migrate from old format if needed
    migrate_from_old_format()
    
    # Handle account listing
    if args.list:
        display_accounts()
        return
    
    # Determine which account to use
    account_id = args.account_id
    account_name = args.profile
    
    # Check if we have configuration
    if account_id:
        account_config = get_account(account_id=account_id)
        if not account_config:
            print(f"Error: Account with ID {account_id} not found.")
            display_accounts()
            return
    elif account_name:
        account_config = get_account(name=account_name)
        if not account_config:
            print(f"Error: Account profile '{account_name}' not found.")
            display_accounts()
            return
    else:
        # No account specified, check if we have any accounts
        accounts = list_accounts()
        if not accounts:
            print("Error: No accounts configured in the database.")
            print("Please create at least one account configuration.")
            return
        
        if len(accounts) > 1:
            print("Multiple account profiles found. Please select one:")
            display_accounts()
            return
            
        # Use the only account
        account_config = get_account(account_id=accounts[0]['id'])
    
    # Get the connection config for this account
    connection_config = get_connection_config(account_id=account_config['id'])
    if not connection_config:
        print(f"Error: No connection configuration found for account '{account_config['name']}'.")
        return
    
    # Start the bot with the selected account
    print(f"Starting bot with account: {account_config['name']} ({account_config['character']})")
    if args.debug:
        print("Debug mode enabled")
    bot = KiwiBot(account_id=account_config['id'], debug=args.debug)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutting down...")