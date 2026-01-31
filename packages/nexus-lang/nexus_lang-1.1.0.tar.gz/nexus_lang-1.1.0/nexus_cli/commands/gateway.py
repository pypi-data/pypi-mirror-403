"""
nexus gateway - Start the WebSocket gateway server
"""

import click
import os
from pathlib import Path


@click.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--port', '-p', default=8765, help='Port to bind to')
@click.option('--watch/--no-watch', default=True, help='Watch memory for changes')
def gateway(host, port, watch):
    """
    Start the WebSocket gateway server.
    
    The gateway provides:
    
    - WebSocket connections at ws://host:port/ws
    - Real-time state updates
    - Pub/sub messaging
    - Interactive dashboard at http://host:port/
    
    Examples:
    
      nexus gateway
      
      nexus gateway -p 9000
      
      nexus gateway --host 0.0.0.0 --port 8080
    """
    click.secho(f"⚡ Starting Nexus Gateway", fg='cyan', bold=True)
    click.echo(f"   Dashboard: http://{host}:{port}/")
    click.echo(f"   WebSocket: ws://{host}:{port}/ws")
    click.echo()
    
    try:
        import uvicorn
        from nexus_core.realtime import get_gateway
        
        gateway = get_gateway()
        
        if watch:
            gateway.start_memory_watcher()
            click.echo("   Memory watcher: ACTIVE")
        
        click.echo()
        click.secho("   Press Ctrl+C to stop", fg='yellow')
        click.echo()
        
        uvicorn.run(
            gateway.app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        click.secho("\n⚡ Gateway shutdown complete", fg='yellow')
    except ImportError as e:
        click.secho(f"\n❌ Missing dependency: {e}", fg='red')
        click.echo("   Run: pip install uvicorn fastapi websockets")
        raise SystemExit(1)
    except Exception as e:
        click.secho(f"\n❌ Gateway error: {e}", fg='red')
        raise SystemExit(1)
