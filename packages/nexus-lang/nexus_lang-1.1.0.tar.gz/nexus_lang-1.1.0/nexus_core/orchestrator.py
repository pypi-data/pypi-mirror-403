import sys
import time
import threading
import colorama
from colorama import Fore, Style
import webbrowser
import subprocess
from .memory import NexusMemory
from .parser import NexusParser
from .compiler import NexusCompiler

colorama.init()

from .schema_loader import NexusSchemaLoader

class NexusOrchestrator:
    def __init__(self, nexus_file):
        self.nexus_file = nexus_file
        self.memory = None
        self.parser = NexusParser()
        self.compiler = NexusCompiler()
        self.schema_loader = NexusSchemaLoader()
        self.running = True

    def start(self):
        self._print_banner()
        
        print(f"{Fore.GREEN}[NEXUS] Initializing The Singularity...{Style.RESET_ALL}")
        self.memory = NexusMemory(create=True)
        print(f"{Fore.GREEN}[NEXUS] Singularity Active: {self.memory.filename} ({self.memory.size} bytes){Style.RESET_ALL}")

        print(f"{Fore.GREEN}[NEXUS] Parsing {self.nexus_file}...{Style.RESET_ALL}")
        self.parser.parse_file(self.nexus_file)
        
        if self.parser.blocks.get('schema'):
            print(f"{Fore.GREEN}[NEXUS] Detecting Schema...{Style.RESET_ALL}")
            self.schema_loader.process_schema(self.parser.blocks['schema'][0])
        else:
            print(f"{Fore.YELLOW}[NEXUS] No schema block found.{Style.RESET_ALL}")

        print(f"{Fore.GREEN}[NEXUS] Compiling modules...{Style.RESET_ALL}")
        artifacts = self.compiler.compile(self.parser.blocks)

        self.processes = []
        self._spawn_processes(artifacts)

        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.antigravity_protocol(e)

    def _spawn_processes(self, artifacts):
        print(f"{Fore.CYAN}[NEXUS] Supervisor: Spawning {len(artifacts)} subprocesses...{Style.RESET_ALL}")
        for art in artifacts:
            self._launch_process(art)

    def _launch_process(self, art):
        try:
            proc = None
            cmd = []
            name = "Unknown"
            
            if art['type'] == 'c':
                name = art['bin']
                cmd = [f"./{art['bin']}"]
            elif art['type'] == 'rs':
                name = art['bin']
                cmd = [f"./{art['bin']}"]
            elif art['type'] == 'java':
                name = art['class']
                cp = art.get('cp', '.')
                cmd = ["java", "-cp", cp, art['class']]
            elif art['type'] == 'go':
                name = art['bin']
                cmd = [f"./{art['bin']}"]
            elif art['type'] == 'ts':
                name = art['src']
                cmd = ["npx", "ts-node", art['src']]
            elif art['type'] == 'web':
                name = art['src']
                cmd = ["uvicorn", art['src'].replace('.py', ':app'), "--reload", "--port", "8000"]
            elif art['type'] == 'py':
                name = art['src']
                cmd = ["python", art['src']]

            if cmd:
                print(f"[NEXUS] Launching {art['type'].upper()} Module: {name}")
                if art['type'] == 'ts':
                     proc = subprocess.Popen(cmd, shell=True)
                else:
                     proc = subprocess.Popen(cmd)
                
                existing = next((p for p in self.processes if p['artifact'] == art), None)
                if existing:
                    existing['proc'] = proc
                    existing['restarts'] += 1
                else:
                    self.processes.append({'artifact': art, 'proc': proc, 'restarts': 0, 'cmd': cmd, 'name': name})
            
        except Exception as e:
            print(f"{Fore.RED}[NEXUS] Failed to spawn {art}: {e}{Style.RESET_ALL}")

    def _main_loop(self):
        print(f"{Fore.MAGENTA}[NEXUS] EXECUTION STARTED. Press Ctrl+C to abort.{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}[NEXUS] SUPERVISOR ACTIVE: Monitoring for crashes...{Style.RESET_ALL}")
        
        while self.running:
            time.sleep(1)
            for p_info in self.processes:
                proc = p_info['proc']
                if proc.poll() is not None:
                    code = proc.returncode
                    print(f"{Fore.RED}[NEXUS] ALERT: Process {p_info['name']} died with code {code}!{Style.RESET_ALL}")
                    
                    print(f"{Fore.YELLOW}[NEXUS] PHOENIX PROTOCOL: Respawning {p_info['name']}...{Style.RESET_ALL}")
                    time.sleep(1)
                    self._launch_process(p_info['artifact'])

    def shutdown(self):
        self.running = False
        print(f"{Fore.YELLOW}[NEXUS] Terminating subprocesses...{Style.RESET_ALL}")
        for p_info in self.processes:
            p = p_info['proc']
            try:
                p.terminate()
                p.wait(timeout=1)
            except:
                p.kill() 
        if self.memory:
            self.memory.close()
        print(f"{Fore.CYAN}[NEXUS] System Shutdown.{Style.RESET_ALL}")

    def _print_banner(self):
        banner = r"""
   _   _  _____  __  __  _   _  _____ 
  | \ | ||  ___| \ \/ / | | | ||  ___|
  |  \| || |__    \  /  | | | || |__  
  | . ` ||  __|   /  \  | |_| ||  __| 
  |_| \_|| |___  /_/\_\  \___/ | |___ 
        """
        print(f"{Fore.GREEN}{banner}{Style.RESET_ALL}")
