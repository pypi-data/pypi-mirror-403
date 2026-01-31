"""
Nexus CLI - The Universal Polyglot Runtime
Command-line interface for managing Nexus projects.
"""

import click
import sys
import os
import time

# Add parent dir to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .commands import init, run, compile, status, schema, gateway, plugin

# ANSI color codes
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'

BANNER = f"""
{CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   {BOLD}⚡ NEXUS{RESET}{CYAN}  {DIM}v1.0.0{RESET}{CYAN}                                               ║
║   {GREEN}The Universal Polyglot Runtime{RESET}{CYAN}                                ║
║                                                                  ║
║   {DIM}Write Python, C, Rust, Java, Go, TypeScript in ONE file{RESET}{CYAN}        ║
║   {DIM}with zero-copy shared memory between all languages.{RESET}{CYAN}            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
"""

COMMANDS_HELP = f"""
{BOLD}Commands:{RESET}
  {GREEN}init{RESET} <name>        Create a new project {DIM}(basic/web/microservice){RESET}
  {GREEN}run{RESET} <file>         Run a .nexus file
  {GREEN}compile{RESET} <file>     Compile without running
  {GREEN}status{RESET}             Show memory state & active processes
  {GREEN}gateway{RESET}            Start WebSocket gateway {DIM}(http://localhost:8765){RESET}
  {GREEN}schema{RESET}             Validate or generate type definitions
  {GREEN}plugin{RESET}             Manage extensions {DIM}(create/list/load){RESET}

{BOLD}Examples:{RESET}
  {DIM}${RESET} nexus init my-app --template web
  {DIM}${RESET} nexus run main.nexus
  {DIM}${RESET} nexus gateway --port 9000
  {DIM}${RESET} nexus plugin create analyzer --type hook

{DIM}Documentation: https://nexus-lang.dev{RESET}
{DIM}PyPI: https://pypi.org/project/nexus-lang/{RESET}
"""


def print_banner(animate=True):
    """Print the animated Nexus banner."""
    if animate and sys.stdout.isatty():
        for line in BANNER.split('\n'):
            print(line)
            time.sleep(0.02)
    else:
        print(BANNER)


class NexusCLI(click.Group):
    """Custom CLI group with styled help."""
    
    def format_help(self, ctx, formatter):
        print_banner(animate=False)
        formatter.write(COMMANDS_HELP)


@click.group(cls=NexusCLI)
@click.version_option(version='1.0.0', prog_name='Nexus', message=f'{CYAN}⚡ Nexus{RESET} v%(version)s')
@click.pass_context
def cli(ctx):
    """⚡ Nexus - The Universal Polyglot Runtime"""
    ctx.ensure_object(dict)


# Register commands
cli.add_command(init.init)
cli.add_command(run.run)
cli.add_command(compile.compile)
cli.add_command(status.status)
cli.add_command(schema.schema)
cli.add_command(gateway.gateway)
cli.add_command(plugin.plugin)


def main():
    """Entry point for the CLI."""
    # Enable ANSI on Windows
    if sys.platform == 'win32':
        os.system('')
    cli(obj={})


if __name__ == '__main__':
    main()

