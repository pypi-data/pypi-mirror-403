import click
import sys
import os
import json
import asyncio
from loguru import logger
from .client import IDSecureClient

@click.group()
@click.option('--url', default=lambda: os.getenv("IDSECURE_BASE_URL"), help="Base URL of IDSecure instance")
@click.option('--user', default=lambda: os.getenv("IDSECURE_USERNAME"), help="Username")
@click.option('--password', default=lambda: os.getenv("IDSECURE_PASSWORD"), help="Password")
@click.pass_context
def cli(ctx, url, user, password):
    """IDSecure CLI Tool"""
    if not url or not user or not password:
        click.echo("Error: Base URL, username, and password must be provided via arguments or environment variables.", err=True)
        ctx.exit(1)
    ctx.obj = IDSecureClient(base_url=url, username=user, password=password)

async def run_async_command(coro):
    try:
        result = await coro
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

@cli.command()
@click.pass_obj
def list_users(client):
    """List users"""
    asyncio.run(run_async_command(client.list_users()))

@cli.command()
@click.pass_obj
def list_devices(client):
    """List devices"""
    asyncio.run(run_async_command(client.list_devices()))

@cli.command()
@click.option('--id', required=True, type=int, help='User ID')
@click.pass_obj
def get_user(client, id):
    """Get a single user's data"""
    asyncio.run(run_async_command(client.get_user(id)))

@cli.command()
@click.option('--id', required=True, type=int, help='User ID')
@click.pass_obj
def delete_user(client, id):
    """Delete a user by ID"""
    asyncio.run(run_async_command(client.delete_user(id)))

def main():
    cli(obj={})

if __name__ == "__main__":
    main()
