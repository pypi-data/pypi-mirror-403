"""
nexus run - Run a Nexus file
"""

import click
import sys
import os
from pathlib import Path


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--watch', '-w', is_flag=True, help='Watch for changes and restart')
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def run(file, watch, verbose):
    """
    Run a .nexus file.
    
    This starts the Nexus orchestrator which will:
    
    1. Parse the .nexus file and imports
    2. Generate type files from schema
    3. Compile C, Rust, Java, Go modules
    4. Start all processes with supervision
    
    Examples:
    
      nexus run main.nexus
      
      nexus run app.nexus --watch
      
      nexus run main.nexus --verbose
    """
    file_path = Path(file).resolve()
    
    if not file_path.suffix == '.nexus':
        click.secho(f"Warning: File does not have .nexus extension", fg='yellow')
    
    # Change to file directory for relative imports
    os.chdir(file_path.parent)
    
    click.secho(f"⚡ Starting Nexus Orchestrator", fg='cyan', bold=True)
    click.echo(f"   File: {file_path.name}")
    click.echo()
    
    try:
        from nexus_core import NexusOrchestrator
        
        orchestrator = NexusOrchestrator(str(file_path))
        orchestrator.start()
        
    except KeyboardInterrupt:
        click.secho("\n⚡ Nexus shutdown complete", fg='yellow')
    except Exception as e:
        click.secho(f"\nError: {e}", fg='red')
        if verbose:
            import traceback
            traceback.print_exc()
        raise SystemExit(1)
