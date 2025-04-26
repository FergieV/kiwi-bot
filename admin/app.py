#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Add project root to path to import db.config
sys.path.append(str(Path(__file__).parent.parent))
from db.config import (
    initialize_database, get_account, get_connection_config, 
    set_account, set_connection_config, list_accounts, delete_account,
    list_connection_configs
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kiwi-bot-development-key')

@app.route('/')
def index():
    """Display the account list page"""
    accounts = list_accounts()
    return render_template('index.html', accounts=accounts, title="KiwiBot Accounts")

@app.route('/accounts/<int:account_id>')
def view_account(account_id):
    """Display details for a specific account"""
    account = get_account(account_id=account_id)
    if not account:
        flash(f"Account with ID {account_id} not found", "error")
        return redirect(url_for('index'))
    
    # Ensure all required fields are present
    account_data = {
        'id': account['id'],
        'name': account['name'],
        'email': account['email'],
        'character': account['character'],
        'password': account['password'],
        'colors': account['colors'],
        'description': account['description'],
        'owner': account['owner']
    }
    
    return render_template('account_view.html', 
                         account=account_data, 
                         title=f"Account: {account['name']}")

@app.route('/accounts/new', methods=['GET', 'POST'])
def new_account():
    """Create a new account"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        character = request.form.get('character', '').strip()
        password = request.form.get('password', '').strip()
        colors = request.form.get('colors', '').strip() or "nynn"
        description = request.form.get('description', '').strip()
        owner = request.form.get('owner', '').strip()
        
        # Validate required fields
        if not all([name, email, character, password]):
            flash("Name, email, character, and password are required fields", "error")
            return render_template('account_form.html', title="New Account", 
                                  account={}, connection={}, is_new=True)
        
        # Check if account with this name already exists
        existing = get_account(name=name)
        if existing:
            flash(f"Account with name '{name}' already exists", "error")
            return render_template('account_form.html', title="New Account", 
                                 account=request.form, connection={}, is_new=True)
        
        # Create the account
        account_id = set_account(
            email=email,
            character=character,
            password=password,
            colors=colors,
            description=description,
            owner=owner,
            name=name
        )
        
        if not account_id:
            flash("Failed to create account", "error")
            return render_template('account_form.html', title="New Account", 
                                 account=request.form, connection={}, is_new=True)
        
        flash(f"Account '{name}' created successfully", "success")
        return redirect(url_for('view_account', account_id=account_id))
    
    # GET request - show the form
    return render_template('account_form.html', title="New Account", 
                         account={}, connection={})

@app.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
def edit_account(account_id):
    """Edit an existing account"""
    account = get_account(account_id=account_id)
    if not account:
        flash(f"Account with ID {account_id} not found", "error")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        character = request.form.get('character', '').strip()
        password = request.form.get('password', '').strip()
        colors = request.form.get('colors', '').strip() or "nynn"
        description = request.form.get('description', '').strip()
        owner = request.form.get('owner', '').strip()
        
        # Validate required fields
        if not all([name, email, character]):
            flash("Name, email, and character are required fields", "error")
            return render_template('account_form.html', title=f"Edit Account: {account['name']}", 
                                  account=request.form, connection={})
        
        # Check if the name is being changed and if it conflicts with another account
        if name != account['name']:
            existing = get_account(name=name)
            if existing and existing['id'] != account_id:
                flash(f"Account with name '{name}' already exists", "error")
                return render_template('account_form.html', title=f"Edit Account: {account['name']}", 
                                     account=request.form, connection={})
        
        # Update the account
        updated_id = set_account(
            email=email,
            character=character,
            password=password if password else None,  # Don't update password if empty
            colors=colors,
            description=description,
            owner=owner,
            name=name,
            account_id=account_id
        )
        
        if not updated_id:
            flash("Failed to update account", "error")
            return render_template('account_form.html', title=f"Edit Account: {account['name']}", 
                                 account=request.form, connection={})
        
        flash(f"Account '{name}' updated successfully", "success")
        return redirect(url_for('view_account', account_id=account_id))
    
    # GET request - show the form with current values
    return render_template('account_form.html', title=f"Edit Account: {account['name']}", 
                         account=account, connection={})

@app.route('/accounts/<int:account_id>/delete', methods=['POST'])
def delete_account_route(account_id):
    """Delete an account"""
    account = get_account(account_id=account_id)
    if not account:
        flash(f"Account with ID {account_id} not found", "error")
        return redirect(url_for('index'))
    
    success = delete_account(account_id=account_id)
    if success:
        flash(f"Account '{account['name']}' deleted successfully", "success")
    else:
        flash(f"Failed to delete account '{account['name']}'", "error")
    
    return redirect(url_for('index'))

@app.route('/connections')
def connections():
    """Display all connection settings"""
    connections = list_connection_configs()
    return render_template('connections.html', connections=connections)

@app.route('/connections/edit', methods=['POST'])
def edit_connection():
    """Edit a connection config"""
    account_id = request.form.get('account_id')
    server = request.form.get('server', '').strip() or "lightbringer.furcadia.com"
    
    try:
        account_id = int(account_id)
        port = int(request.form.get('port', '6500'))
    except (ValueError, TypeError):
        flash("Invalid account ID or port number", "error")
        return redirect(url_for('connections'))
    
    # Check if account exists
    account = get_account(account_id=account_id)
    if not account:
        flash(f"Account with ID {account_id} not found", "error")
        return redirect(url_for('connections'))
    
    # Update the connection
    success = set_connection_config(
        server=server,
        port=port,
        account_id=account_id
    )
    
    if success:
        flash(f"Connection settings for '{account['name']}' updated successfully", "success")
    else:
        flash(f"Failed to update connection settings for '{account['name']}'", "error")
    
    return redirect(url_for('connections'))

@app.route('/api/accounts')
def api_list_accounts():
    """API endpoint to get all accounts as JSON"""
    accounts = list_accounts()
    return jsonify(accounts)

@app.route('/api/accounts/<int:account_id>')
def api_get_account(account_id):
    """API endpoint to get account details as JSON"""
    account = get_account(account_id=account_id)
    if not account:
        return jsonify({"error": f"Account with ID {account_id} not found"}), 404
    
    connection = get_connection_config(account_id=account_id)
    return jsonify({"account": account, "connection": connection})

@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags"""
    if value:
        return value.replace('\n', '<br>')
    return ''

@app.context_processor
def utility_processor():
    """Make functions available to templates"""
    return {
        'app_name': 'KiwiBot Manager',
        'app_version': '1.0.0'
    }

def main():
    """Run the Flask application"""
    # Initialize the database
    initialize_database()
    # Run the Flask app
    app.run(debug=True, host='127.0.0.1', port=5000)

if __name__ == '__main__':
    main() 