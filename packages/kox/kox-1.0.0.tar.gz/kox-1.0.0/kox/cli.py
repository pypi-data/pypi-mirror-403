"""
Kox 命令行工具
"""
import os
import json
import click
from pathlib import Path
from typing import Optional
from .client import Kox


# 配置文件路径
CONFIG_DIR = Path.home() / '.kox'
CONFIG_FILE = CONFIG_DIR / 'config.json'


def get_config():
    """获取配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config):
    """保存配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_client(host: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, port: Optional[int] = None):
    """获取客户端实例"""
    config = get_config()
    
    # 使用参数或配置中的值
    host = host or config.get('host') or 'localhost'
    user = user or config.get('username')
    password = password or config.get('password')
    port = port if port is not None else config.get('port')
    
    # 如果没有用户名或密码，提示输入
    if not user:
        user = click.prompt('Enter username', type=str)
    if not password:
        password = click.prompt('Enter password', type=str, hide_input=True)
    
    try:
        return Kox(host=host, user=user, password=password, port=port)
    except Exception as e:
        click.echo(f"❌ Connection failed: {e}", err=True)
        raise click.Abort()


@click.group()
@click.version_option(version='1.0.0', prog_name='kox')
def cli():
    """Kox - Code management tool"""
    pass


@cli.command()
@click.argument('username')
def set_username(username):
    """kox set-username <username> - Set default username"""
    config = get_config()
    config['username'] = username
    save_config(config)
    click.echo(f"✓ Username set to: {username}")


@cli.command()
@click.argument('password')
def set_password(password):
    """kox set-password <password> - Set default password"""
    config = get_config()
    config['password'] = password
    save_config(config)
    click.echo("✓ Password set")


@cli.command('del-username')
def del_username():
    """kox del-username - Delete configured username"""
    config = get_config()
    if 'username' in config:
        del config['username']
        save_config(config)
        click.echo("✓ Username deleted")
    else:
        click.echo("⚠ Username not configured")


@cli.command('del-password')
def del_password():
    """kox del-password - Delete configured password"""
    config = get_config()
    if 'password' in config:
        del config['password']
        save_config(config)
        click.echo("✓ Password deleted")
    else:
        click.echo("⚠ Password not configured")


@cli.command()
@click.argument('host')
def set_host(host):
    """kox set-host <host> - Set server address"""
    config = get_config()
    config['host'] = host
    save_config(config)
    click.echo(f"✓ Server address set to: {host}")


@cli.command()
@click.argument('port', type=int)
def set_port(port):
    """kox set-port <port> - Set default port"""
    config = get_config()
    config['port'] = port
    save_config(config)
    click.echo(f"✓ Port set to: {port}")


@cli.command()
@click.option('--project', '-p', required=True, help='Project name')
@click.option('--version', '-v', help='Version number (optional, default: latest)')
@click.option('--location', '-l', default='./', help='Download path (optional, default: current directory)')
@click.option('--host', '-h', help='Server address')
@click.option('--username', '-u', help='Username')
@click.option('--password', '-P', help='Password')
def clone(project, version, location, host, username, password):
    """kox clone -p <project_name> [-v <version>] [-l <location>] [--host <host>] [--username <username>] [--password <password>] - Download project"""
    try:
        client = get_client(host=host, user=username, password=password)
        client.clone(project=project, version=version, path=location)
    except Exception as e:
        click.echo(f"❌ Download failed: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--project', '-p', required=True, help='Project name')
@click.option('--version', '-v', help='Version number (optional, default: auto-increment)')
@click.option('--location', '-l', default='./', help='Upload path (optional, default: current directory)')
@click.option('--project-description', help='Project description (optional)')
@click.option('--version-description', help='Version description (optional)')
@click.option('--host', '-h', help='Server address')
@click.option('--username', '-u', help='Username')
@click.option('--password', '-P', help='Password')
def upload(project, version, location, project_description, version_description, host, username, password):
    """kox upload -p <project_name> [-v <version>] [-l <location>] [--project-description <desc>] [--version-description <desc>] [--host <host>] [--username <username>] [--password <password>] - Upload project"""
    try:
        client = get_client(host=host, user=username, password=password)
        client.upload(project=project, version=version, path=location, 
                     project_description=project_description, version_description=version_description)
    except Exception as e:
        click.echo(f"❌ Upload failed: {e}", err=True)
        raise click.Abort()


@cli.command('show-projects')
@click.option('--host', '-h', help='Server address')
@click.option('--username', '-u', help='Username')
@click.option('--password', '-P', help='Password')
def show_projects(host, username, password):
    """kox show-projects [--host <host>] [--username <username>] [--password <password>] - Show all projects"""
    try:
        client = get_client(host=host, user=username, password=password)
        client.show_projects()
    except Exception as e:
        click.echo(f"❌ Failed to get project list: {e}", err=True)
        raise click.Abort()


@cli.command('show-version')
@click.option('--project', '-p', required=True, help='Project name')
@click.option('--host', '-h', help='Server address')
@click.option('--username', '-u', help='Username')
@click.option('--password', '-P', help='Password')
def show_version(project, host, username, password):
    """kox show-version -p <project_name> [--host <host>] [--username <username>] [--password <password>] - Show project version history"""
    try:
        client = get_client(host=host, user=username, password=password)
        client.show_histories(project=project)
    except Exception as e:
        click.echo(f"❌ Failed to get version history: {e}", err=True)
        raise click.Abort()


@cli.command()
def config():
    """kox config - Show current configuration"""
    config = get_config()
    if config:
        click.echo("Current configuration:")
        for key, value in config.items():
            if key == 'password':
                click.echo(f"  {key}: {'*' * len(str(value))}")
            else:
                click.echo(f"  {key}: {value}")
    else:
        click.echo("No configuration set")


@cli.command('show-config')
def show_config():
    """kox show-config - Show configured host, port, username and password"""
    config = get_config()
    
    # 显示主机地址
    host = config.get('host')
    if host:
        click.echo(f"Host: {host}")
    else:
        click.echo("Host: Host not configured")
    
    # 显示端口
    port = config.get('port')
    if port is not None:
        click.echo(f"Port: {port}")
    else:
        click.echo("Port: Port not configured")
    
    # 显示用户名
    username = config.get('username')
    if username:
        click.echo(f"Username: {username}")
    else:
        click.echo("Username: Username not configured")
    
    # 显示密码
    password = config.get('password')
    if password:
        click.echo("Password: *****")
    else:
        click.echo("Password: Password not configured")


if __name__ == '__main__':
    cli()
