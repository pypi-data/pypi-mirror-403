"""
nexus init - Initialize a new Nexus project
"""

import click
import os
import shutil
from pathlib import Path


TEMPLATES = {
    'basic': '''>>>schema
{
    "counter": 0,
    "message": "Hello from Nexus!"
}

>>>py
import time
from nexus_core import NexusMemory

mem = NexusMemory(create=False)
print("[Python] Connected to Singularity")
while True:
    time.sleep(1)

>>>c
int main() {
    nexus_init();
    printf("[C] Connected to Singularity\\n");
    
    while(1) {
        char* state = nexus_read_state();
        printf("[C] State: %.50s...\\n", state);
        free(state);
        Sleep(2000);
    }
    return 0;
}
''',

    'web': '''>>>schema
{
    "visitors": 0,
    "messages": []
}

>>>web
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nexus_core import NexusMemory
import json

app = FastAPI()
mem = NexusMemory(create=False)

@app.get("/", response_class=HTMLResponse)
async def home():
    state = json.loads(mem.read().decode())
    return f"""
    <html>
    <head><title>Nexus App</title></head>
    <body style="font-family: sans-serif; background: #111; color: #0ff; padding: 40px;">
        <h1>⚡ Welcome to Nexus</h1>
        <p>Visitors: {state.get('visitors', 0)}</p>
        <p><a href="/api/visit" style="color: #0f0;">Click to increment</a></p>
    </body>
    </html>
    """

@app.get("/api/visit")
async def visit():
    state = json.loads(mem.read().decode())
    state['visitors'] = state.get('visitors', 0) + 1
    mem.write(json.dumps(state).encode())
    return {"visitors": state['visitors']}
''',

    'microservice': '''>>>schema
{
    "requests": 0,
    "health": "OK",
    "metrics": {"latency_ms": 0}
}

>>>py
import time
import json
from nexus_core import NexusMemory

mem = NexusMemory(create=False)
print("[Monitor] Starting health monitor...")

while True:
    state = json.loads(mem.read().decode())
    state['health'] = 'OK'
    mem.write(json.dumps(state).encode())
    time.sleep(5)

>>>web
from fastapi import FastAPI
from nexus_core import NexusMemory
import json
import time

app = FastAPI()
mem = NexusMemory(create=False)

@app.get("/health")
async def health():
    state = json.loads(mem.read().decode())
    return {"status": state.get('health', 'UNKNOWN')}

@app.get("/metrics")
async def metrics():
    state = json.loads(mem.read().decode())
    return state.get('metrics', {})

@app.get("/api/process")
async def process():
    start = time.time()
    state = json.loads(mem.read().decode())
    state['requests'] = state.get('requests', 0) + 1
    state['metrics']['latency_ms'] = (time.time() - start) * 1000
    mem.write(json.dumps(state).encode())
    return {"processed": state['requests']}
'''
}


@click.command()
@click.argument('name')
@click.option('--template', '-t', default='basic', 
              type=click.Choice(['basic', 'web', 'microservice']),
              help='Project template to use')
def init(name, template):
    """
    Initialize a new Nexus project.
    
    Examples:
    
      nexus init my-project
      
      nexus init my-api --template web
    """
    project_dir = Path(name)
    
    if project_dir.exists():
        click.secho(f"Error: Directory '{name}' already exists", fg='red')
        raise SystemExit(1)
    
    # Create project structure
    project_dir.mkdir(parents=True)
    (project_dir / 'nexus_generated').mkdir()
    
    # Write main.nexus
    main_file = project_dir / 'main.nexus'
    main_file.write_text(TEMPLATES[template])
    
    # Write .gitignore
    gitignore = project_dir / '.gitignore'
    gitignore.write_text('''# Nexus generated files
nexus_generated/
nexus.mem
*.exe
*.class
*.o
.nexus_*.lock

# Python
__pycache__/
*.pyc
.venv/
''')
    
    # Write README
    readme = project_dir / 'README.md'
    readme.write_text(f'''# {name}

A Nexus polyglot application.

## Quick Start

```bash
cd {name}
nexus run main.nexus
```

## Project Structure

- `main.nexus` - Main application file
- `nexus_generated/` - Auto-generated type files
- `nexus.mem` - Shared memory file (created at runtime)

## Learn More

Visit [Nexus Documentation](https://github.com/nexus-lang/nexus)
''')
    
    click.secho(f"\n⚡ Created Nexus project: {name}", fg='green', bold=True)
    click.echo(f"\n  Template: {template}")
    click.echo(f"  Main file: {main_file}")
    click.echo(f"\nNext steps:\n")
    click.secho(f"  cd {name}", fg='cyan')
    click.secho(f"  nexus run main.nexus", fg='cyan')
    click.echo()
