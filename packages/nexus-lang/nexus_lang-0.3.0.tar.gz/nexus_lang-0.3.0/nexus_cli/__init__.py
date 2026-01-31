"""
Nexus CLI - The Universal Polyglot Runtime
Command-line interface for managing Nexus projects.
"""

import click
import sys
import os

# Add parent dir to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .commands import init, run, compile, status, schema


@click.group()
@click.version_option(version='0.3.0', prog_name='Nexus')
@click.pass_context
def cli(ctx):
    """
    ⚡ Nexus - The Universal Polyglot Runtime
    
    Write Python, C, Rust, Java, Go, and TypeScript in a single file
    with zero-copy shared memory between all languages.
    
    Examples:
    
      nexus init my-project        Create new project
      
      nexus run main.nexus         Run a .nexus file
      
      nexus compile main.nexus     Compile without running
      
      nexus status                 Show running processes
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(init.init)
cli.add_command(run.run)
cli.add_command(compile.compile)
cli.add_command(status.status)
cli.add_command(schema.schema)


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
