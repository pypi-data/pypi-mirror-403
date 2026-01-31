"""
nexus status - Show status of running Nexus processes
"""

import click
import os
import json
from pathlib import Path


@click.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
def status(as_json):
    """
    Show status of Nexus system.
    
    Displays:
    
    - Memory file status
    - Current state snapshot
    - Running processes (if managed)
    
    Examples:
    
      nexus status
      
      nexus status --json
    """
    mem_file = Path('nexus.mem')
    
    if as_json:
        result = {"memory_exists": mem_file.exists()}
        
        if mem_file.exists():
            result["memory_size"] = mem_file.stat().st_size
            try:
                from nexus_core import NexusMemory
                mem = NexusMemory(create=False)
                state = mem.read().decode('utf-8')
                result["state"] = json.loads(state) if state else {}
                result["stats"] = mem.get_stats()
                mem.close()
            except Exception as e:
                result["error"] = str(e)
        
        click.echo(json.dumps(result, indent=2))
        return
    
    # Human-readable output
    click.secho("⚡ Nexus Status", fg='cyan', bold=True)
    click.echo()
    
    # Check memory file
    if mem_file.exists():
        size = mem_file.stat().st_size
        click.secho(f"  📦 Memory: ", fg='white', nl=False)
        click.secho(f"ACTIVE", fg='green', bold=True)
        click.echo(f"     File: {mem_file}")
        click.echo(f"     Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
        
        # Try to read state
        try:
            from nexus_core import NexusMemory
            mem = NexusMemory(create=False)
            stats = mem.get_stats()
            
            click.echo(f"     Used: {stats['data_size']:,} bytes ({stats['utilization']*100:.1f}%)")
            
            # Show state preview
            state_raw = mem.read().decode('utf-8')
            if state_raw and state_raw != '{}':
                click.echo()
                click.secho("  📋 State Preview:", fg='white')
                # Truncate if too long
                if len(state_raw) > 200:
                    state_raw = state_raw[:200] + "..."
                click.echo(f"     {state_raw}")
            
            mem.close()
            
        except Exception as e:
            click.secho(f"     Error reading state: {e}", fg='yellow')
    else:
        click.secho(f"  📦 Memory: ", fg='white', nl=False)
        click.secho(f"NOT RUNNING", fg='yellow')
        click.echo(f"     Run 'nexus run <file.nexus>' to start")
    
    # Check for lock files
    lock_files = list(Path('.').glob('.nexus_*.lock'))
    if lock_files:
        click.echo()
        click.secho(f"  🔒 Active Locks: {len(lock_files)}", fg='white')
        for lf in lock_files:
            click.echo(f"     {lf.name}")
    
    click.echo()
