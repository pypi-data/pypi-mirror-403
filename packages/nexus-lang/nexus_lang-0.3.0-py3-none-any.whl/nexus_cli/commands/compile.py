"""
nexus compile - Compile modules without running
"""

import click
import sys
import os
from pathlib import Path


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', default=None, help='Output directory for compiled files')
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def compile(file, output, verbose):
    """
    Compile a .nexus file without running.
    
    This will:
    
    1. Parse the .nexus file and imports
    2. Generate type files from schema
    3. Compile C, Rust, Java, Go modules
    4. Output compiled artifacts
    
    Examples:
    
      nexus compile main.nexus
      
      nexus compile app.nexus -o build/
    """
    file_path = Path(file).resolve()
    
    # Change to file directory
    os.chdir(file_path.parent)
    
    click.secho(f"⚡ Compiling: {file_path.name}", fg='cyan', bold=True)
    click.echo()
    
    try:
        from nexus_core.parser import NexusParser
        from nexus_core.compiler import NexusCompiler
        from nexus_core.schema_loader import NexusSchemaLoader
        
        parser = NexusParser()
        parser.parse_file(str(file_path))
        
        # Process schema if present
        if parser.blocks.get('schema'):
            click.echo("  📋 Processing schema...")
            schema_loader = NexusSchemaLoader()
            schema_loader.process_schema(parser.blocks['schema'][0])
        
        # Compile modules
        click.echo("  🔨 Compiling modules...")
        compiler = NexusCompiler()
        artifacts = compiler.compile(parser.blocks)
        
        click.secho(f"\n✅ Compilation complete!", fg='green', bold=True)
        click.echo(f"\n   Artifacts: {len(artifacts)}")
        
        for art in artifacts:
            art_type = art.get('type', 'unknown').upper()
            art_name = art.get('bin') or art.get('src') or art.get('class', 'unknown')
            click.echo(f"   [{art_type}] {art_name}")
        
        click.echo()
        
    except Exception as e:
        click.secho(f"\n❌ Compilation failed: {e}", fg='red')
        if verbose:
            import traceback
            traceback.print_exc()
        raise SystemExit(1)
