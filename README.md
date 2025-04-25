# KiwiBot Framework 🥝

A lightweight, extensible bot framework for Furcadia written in Python. KiwiBot provides a robust foundation for creating and managing Furcadia bots with a focus on simplicity and flexibility.

## Features

- **Command System**: Easy-to-use command framework with cooldown support
- **Account Management**: Secure storage and management of multiple bot accounts
- **Web Interface**: Local web admin panel for managing accounts and settings
- **Extensible**: Simple to add new commands and features
- **Logging**: Comprehensive logging system for debugging and monitoring

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kiwi-bot.git
cd kiwi-bot
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python scripts/init_db.py
```
This will create a default template database with a sample account. You can then edit this account using either the web interface or command line tools.

## Quick Start

1. Edit your bot account:
```bash
# Using the web interface
cd admin
python app.py
# Then open http://127.0.0.1:5000 in your browser

# Or using the command line
python scripts/account_manager.py edit --name default
```

2. Start the bot:
```bash
python main.py --profile default
```

3. Access the web interface:
```bash
cd admin
python app.py
```
Then open `http://127.0.0.1:5000` in your browser.

## Database Configuration

The bot uses SQLite for storing account and connection information:
- Database location: `data/config.db`
- This file is excluded from git tracking to protect your credentials
- Each user should have their own local database file

If you accidentally committed the database file:
```bash
# Remove from git tracking while keeping local file
git rm --cached data/config.db
git commit -m "Remove config.db from git tracking"
git push
```

## Command System

### Using Commands

Commands can be sent to the bot via whispers from the owner character:
```
!move nw 2     # Move 2 steps northwest
!move se 1     # Move 1 step southeast
!help          # Show available commands
```

Available movement directions:
- `nw`: Northwest
- `sw`: Southwest
- `ne`: Northeast
- `se`: Southeast

### Creating New Commands

To create a new command:

1. Create a new file in `kiwibot/commands/`:
```python
from typing import List, Any
from .base import Command

class MyCommand(Command):
    def __init__(self, bot: Any):
        super().__init__(bot)
        self.name = "mycommand"
        self.aliases = ["mc", "mycmd"]
        self.description = "My custom command"
        self.usage = "!mycommand <arg1> [arg2]"
        self.cooldown = 1.0  # 1 second cooldown
    
    async def execute(self, account_id: str, args: List[str]) -> None:
        # Your command logic here
        await self.bot.send_message(account_id, "Command executed!")
```

2. Register the command in `main.py`:
```python
def _register_commands(self):
    # Existing commands
    move_cmd = MovementCommand(self)
    self.commands[move_cmd.name] = move_cmd
    for alias in move_cmd.aliases:
        self.commands[alias] = move_cmd
    
    # Add your new command
    my_cmd = MyCommand(self)
    self.commands[my_cmd.name] = my_cmd
    for alias in my_cmd.aliases:
        self.commands[alias] = my_cmd
```

## Account Management

### Web Interface

The web interface provides an easy way to manage bot accounts:
- Create new accounts
- Edit existing accounts
- Configure connection settings
- View account details

Access it by running:
```bash
cd admin
python app.py
```

### Command Line

Use the account manager script for command-line management:
```bash
# List all accounts
python scripts/account_manager.py list

# Create new account
python scripts/account_manager.py create mybot

# Edit account
python scripts/account_manager.py edit --name mybot

# Delete account
python scripts/account_manager.py delete --name mybot
```

## Configuration

### Database

Account and connection information is stored in SQLite:
- Location: `kiwibot.db`
- Tables: `account`, `connection`

### Logging

Logs are stored in the `logs` directory:
- Format: `kiwibot_<timestamp>.log`
- Level: DEBUG by default

## Running the Bot

Basic usage:
```bash
python main.py --profile mybot
```

Options:
- `--debug`: Enable debug mode (prints raw server messages)
- `--profile <name>`: Use account by profile name
- `--account-id <id>`: Use account by ID
- `--list`: List available accounts

## Security Notes

- The web interface is for local use only
- Account passwords are stored in the database
- Use strong, unique passwords for bot accounts
- Regularly update your bot's credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker. 