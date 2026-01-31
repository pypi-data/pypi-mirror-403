"""
nexus schema - Schema management commands
"""

import click
import json
from pathlib import Path


@click.group()
def schema():
    """
    Schema management commands.
    
    Examples:
    
      nexus schema validate schema.json
      
      nexus schema generate schema.json
    """
    pass


@schema.command()
@click.argument('file', type=click.Path(exists=True))
def validate(file):
    """
    Validate a JSON schema file.
    
    Checks that the schema is valid JSON and can be used
    for type generation.
    """
    file_path = Path(file)
    
    try:
        with open(file_path) as f:
            schema_data = json.load(f)
        
        # Check it's a dict
        if not isinstance(schema_data, dict):
            click.secho(f"❌ Schema must be a JSON object", fg='red')
            raise SystemExit(1)
        
        # Check for basic structure
        field_count = len(schema_data)
        
        click.secho(f"✅ Schema is valid!", fg='green', bold=True)
        click.echo(f"   Fields: {field_count}")
        click.echo(f"   Keys: {', '.join(schema_data.keys())}")
        
    except json.JSONDecodeError as e:
        click.secho(f"❌ Invalid JSON: {e}", fg='red')
        raise SystemExit(1)


@schema.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', default='nexus_generated', help='Output directory')
def generate(file, output):
    """
    Generate type files from a schema.
    
    Creates type definitions for C, Rust, Java, and TypeScript.
    """
    file_path = Path(file)
    output_dir = Path(output)
    
    try:
        with open(file_path) as f:
            schema_data = json.load(f)
        
        from nexus_core.schema_loader import NexusSchemaLoader
        
        loader = NexusSchemaLoader()
        loader.process_schema(json.dumps(schema_data), str(output_dir))
        
        click.secho(f"✅ Generated type files in {output_dir}/", fg='green', bold=True)
        click.echo()
        
        for f in output_dir.iterdir():
            click.echo(f"   {f.name}")
        
    except Exception as e:
        click.secho(f"❌ Generation failed: {e}", fg='red')
        raise SystemExit(1)
