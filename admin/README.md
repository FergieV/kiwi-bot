# KiwiBot Admin Interface

A local web interface for managing KiwiBot accounts.

## Features

- Account management (list, view, create, edit, delete)
- Secure password handling
- Simple and intuitive interface using Tailwind CSS

## Prerequisites

- Python 3.6 or higher
- Flask
- Tailwind CSS (included via CDN)

## Installation

1. Create a virtual environment:
   ```
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install flask
   ```

## Running the Web Interface

1. Activate the virtual environment (if not already activated)
2. Navigate to the admin directory:
   ```
   cd admin
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open your web browser and go to: `http://127.0.0.1:5000`

## Usage

### Managing Accounts

- **List Accounts**: The home page displays all your KiwiBot accounts
- **View Account**: Click on an account name or the View button to see account details
- **Create Account**: Click "New Account" on the accounts list page
- **Edit Account**: Click the Edit button on an account's details page
- **Delete Account**: Click the Delete button on an account's details page and confirm

### Command Line Usage

After setting up accounts in the web interface, you can run the bot with a specific account:

```
python main.py --account [account_name]
```

Or list all accounts:

```
python main.py --list-accounts
```

## Security Note

This interface is intended for local use only. It should not be exposed to the internet without proper security measures. 