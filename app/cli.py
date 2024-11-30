import click
from flask.cli import with_appcontext
from app import db
from app.models import Role, User, Settings
import json

@click.command('init-roles')
@with_appcontext
def init_roles_command():
    """Initialize roles with proper permissions."""
    Role.insert_roles()
    click.echo('Roles initialized successfully.')

@click.command('create-admin')
@with_appcontext
@click.option('--username', prompt=True, help='Admin username')
@click.option('--email', prompt=True, help='Admin email')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
def create_admin_command(username, email, password):
    """Create an admin user."""
    # Get admin role
    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        click.echo('Error: Admin role not found. Run init-roles first.')
        return
    
    # Create admin user
    admin = User(
        username=username,
        email=email,
        role=admin_role,
        is_admin=True,
        is_active=True,
        email_confirmed=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully.')

@click.group('settings')
def settings_group():
    """Settings management commands."""
    pass

@settings_group.command('set')
@click.argument('key')
@click.argument('value')
@click.option('--type', '-t', type=click.Choice(['text', 'number', 'boolean', 'json']), default='text')
@with_appcontext
def set_setting(key, value, type):
    """Set a setting value."""
    setting = Settings.query.filter_by(key=key).first()
    
    if type == 'boolean':
        value = value.lower() in ('true', '1', 'yes')
    elif type == 'number':
        value = float(value)
    elif type == 'json':
        value = json.loads(value)
        
    if setting:
        setting.value = value
        setting.type = type
    else:
        setting = Settings(key=key, value=value, type=type)
        db.session.add(setting)
    
    db.session.commit()
    click.echo(f"Setting {key} updated successfully.")

@settings_group.command('get')
@click.argument('key')
@with_appcontext
def get_setting(key):
    """Get a setting value."""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        click.echo(f"{key}: {setting.value} ({setting.type})")
    else:
        click.echo(f"Setting {key} not found.")

@settings_group.command('list')
@with_appcontext
def list_settings():
    """List all settings."""
    settings = Settings.query.all()
    if settings:
        for setting in settings:
            click.echo(f"{setting.key}: {setting.value} ({setting.type})")
    else:
        click.echo("No settings found.")
