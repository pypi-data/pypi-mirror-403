"""
nexus plugin - Plugin management commands
"""

import click
import os
from pathlib import Path


@click.group()
def plugin():
    """
    Plugin management commands.
    
    Manage Nexus plugins for extending functionality.
    """
    pass


@plugin.command()
@click.argument('name')
@click.option('--type', '-t', 'plugin_type', 
              type=click.Choice(['language', 'hook', 'transform', 'adapter']),
              default='hook', help='Type of plugin')
@click.option('--output', '-o', default='.nexus_plugins', help='Output directory')
def create(name, plugin_type, output):
    """
    Create a new plugin from template.
    
    Examples:
    
      nexus plugin create my-plugin
      
      nexus plugin create lua-support --type language
    """
    from nexus_core.plugins import create_plugin_template, PluginType
    
    type_map = {
        'language': PluginType.LANGUAGE,
        'hook': PluginType.HOOK,
        'transform': PluginType.TRANSFORM,
        'adapter': PluginType.ADAPTER
    }
    
    try:
        path = create_plugin_template(name, type_map[plugin_type], output)
        click.secho(f"✅ Created plugin: {path}", fg='green')
        click.echo(f"   Edit: {path}/main.py")
        click.echo(f"   Manifest: {path}/nexus_plugin.json")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        raise SystemExit(1)


@plugin.command('list')
@click.option('--dir', '-d', 'plugins_dir', default='.nexus_plugins', help='Plugins directory')
def list_plugins(plugins_dir):
    """
    List installed plugins.
    """
    from nexus_core.plugins import PluginManager
    
    manager = PluginManager(plugins_dir)
    discovered = manager.discover()
    
    if not discovered:
        click.echo("No plugins found.")
        click.echo(f"   Directory: {Path(plugins_dir).absolute()}")
        return
    
    click.secho(f"Found {len(discovered)} plugin(s):", fg='cyan')
    click.echo()
    
    for meta in discovered:
        status = "✅" if manager.get_plugin(meta.name) else "○"
        click.echo(f"  {status} {meta.name} v{meta.version}")
        click.echo(f"      Type: {meta.plugin_type.value}")
        if meta.description:
            click.echo(f"      {meta.description}")
        click.echo()


@plugin.command()
@click.argument('name')
@click.option('--dir', '-d', 'plugins_dir', default='.nexus_plugins', help='Plugins directory')
def load(name, plugins_dir):
    """
    Load a plugin.
    """
    from nexus_core.plugins import PluginManager
    
    manager = PluginManager(plugins_dir)
    plugin = manager.load(name)
    
    if plugin:
        click.secho(f"✅ Loaded: {name} v{plugin.metadata.version}", fg='green')
    else:
        click.secho(f"❌ Failed to load: {name}", fg='red')
        raise SystemExit(1)


@plugin.command()
@click.argument('name')
@click.option('--dir', '-d', 'plugins_dir', default='.nexus_plugins', help='Plugins directory')
def info(name, plugins_dir):
    """
    Show plugin information.
    """
    import json
    
    manifest_path = Path(plugins_dir) / name / 'nexus_plugin.json'
    
    if not manifest_path.exists():
        click.secho(f"❌ Plugin not found: {name}", fg='red')
        raise SystemExit(1)
    
    with open(manifest_path) as f:
        data = json.load(f)
    
    click.secho(f"Plugin: {data['name']}", fg='cyan', bold=True)
    click.echo(f"  Version: {data.get('version', 'unknown')}")
    click.echo(f"  Type: {data.get('type', 'hook')}")
    click.echo(f"  Author: {data.get('author', 'unknown')}")
    click.echo(f"  Description: {data.get('description', '')}")
    
    if data.get('requires'):
        click.echo(f"  Requires: {', '.join(data['requires'])}")
