import re

class NexusParser:
    def __init__(self):
        self.blocks = {
            'py': [],
            'js': [],
            'rs': [],
            'c': [],
            'java': [],
            'node': [],
            'ts': [],
            'go': [],
            'web': [],
            'schema': [],
            'react': [],
            'nextjs': [],
        }

    def parse_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.parse_string(content)
        except FileNotFoundError:
            print(f"[NEXUS] Error: File {filepath} not found.")

    def parse_string(self, content: str, base_path="."):
        # Import handling: >>>import "path/to/file.nexus"
        import_pattern = re.compile(r'^>>>import\s+"([^"]+)"', re.MULTILINE)
        for match in import_pattern.finditer(content):
            rel_path = match.group(1)
            import os
            print(f"[NEXUS] Importing {rel_path}...")
            self.parse_file(rel_path)

        # Split by block markers: >>>py, >>>c, >>>java, etc.
        # Using >>> (three arrows) for safer delimiter that won't conflict with operators
        parts = re.split(r'(?m)^>>>(\w+)\s*$', content)
        
        if len(parts) < 2:
            return 
            
        for i in range(1, len(parts), 2):
            block_type = parts[i].strip().lower()
            block_content = parts[i+1].strip()
            
            if block_type == 'import': 
                continue

            if block_type in self.blocks:
                self.blocks[block_type].append(block_content)
            else:
                print(f"[NEXUS] Warning: Unknown block type '>>>{block_type}' - Storing anyway.")
                if block_type not in self.blocks: 
                    self.blocks[block_type] = []
                self.blocks[block_type].append(block_content)

    def get_blocks(self, block_type: str):
        return self.blocks.get(block_type, [])
