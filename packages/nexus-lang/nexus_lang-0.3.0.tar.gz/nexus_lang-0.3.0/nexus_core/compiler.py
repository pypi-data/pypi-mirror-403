import subprocess
import os
import sys
import shutil

class NexusCompiler:
    def __init__(self):
        pass

    def compile(self, blocks):
        artifacts = []
        
        for i, code in enumerate(blocks.get('c', [])):
            filename = f"nexus_module_c_{i}.c"
            exe_name = f"nexus_module_c_{i}.exe"
            full_code = '#include "nexus_core/adapters/nexus.h"\n#include "nexus_generated/nexus_types.h"\n' + code
            with open(filename, "w") as f: f.write(full_code)
            
            cmd = ["gcc", "-o", exe_name, filename, "-I."]
            try:
                print(f"[NEXUS] Compiling {filename} to {exe_name}...")
                subprocess.run(cmd, check=True)
                artifacts.append({'type': 'c', 'bin': exe_name})
            except Exception as e:
                print(f"[NEXUS] C Compilation Failed: {e}")

        for i, code in enumerate(blocks.get('rs', [])):
            filename = f"nexus_module_rs_{i}.rs"
            exe_name = f"nexus_module_rs_{i}.exe"
            full_code = 'mod nexus_generated;\nuse nexus_generated::nexus_types;\n' + code
            with open(filename, "w") as f: f.write(full_code)
            
            project_dir = f"nexus_rust_project_{i}"
            os.makedirs(project_dir, exist_ok=True)
            os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
            
            with open(os.path.join(project_dir, "Cargo.toml"), "w") as f:
                f.write(f"""
[package]
name = "nexus_module_rs_{i}"
version = "0.1.0"
edition = "2021"

[dependencies]
memmap2 = "0.5"
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
nexus_adapter = {{ path = "../../nexus_core/adapters/rust" }}
""")
            
            os.makedirs(os.path.join(project_dir, "src/nexus_generated"), exist_ok=True)
            if os.path.exists("nexus_generated/nexus_types.rs"):
               with open("nexus_generated/nexus_types.rs", "r") as src, open(os.path.join(project_dir, "src/nexus_generated/nexus_types.rs"), "w") as dst:
                   dst.write(src.read())
               with open(os.path.join(project_dir, "src/nexus_generated/mod.rs"), "w") as f:
                   f.write("pub mod nexus_types;")

            full_code = 'mod nexus_generated;\nuse nexus_generated::nexus_types;\nuse nexus_adapter;\n' + code
            with open(os.path.join(project_dir, "src/main.rs"), "w") as f: f.write(full_code)

            try:
                print(f"[NEXUS] Building Rust project {project_dir}...")
                subprocess.run(["cargo", "build", "--release"], cwd=project_dir, check=True)
                bin_path = os.path.join(project_dir, "target", "release", f"nexus_module_rs_{i}.exe")
                shutil.copy(bin_path, exe_name)
                artifacts.append({'type': 'rs', 'bin': exe_name})
            except Exception as e:
                 print(f"[NEXUS] Rust Compilation Failed: {e}")

        for i, code in enumerate(blocks.get('java', [])):
            filename = f"NexusModule_{i}.java"
            full_code = 'import nexus.Nexus;\nimport nexus.GlobalState;\n' + code
            with open(filename, "w") as f: f.write(full_code)
            
            os.makedirs("nexus_build/nexus", exist_ok=True)
            if os.path.exists("nexus_core/adapters/Nexus.java"):
                 shutil.copy("nexus_core/adapters/Nexus.java", "nexus_build/nexus/Nexus.java")
            if os.path.exists("nexus_generated/GlobalState.java"):
                 shutil.copy("nexus_generated/GlobalState.java", "nexus_build/nexus/GlobalState.java")
                 
            try:
                subprocess.run(["javac", "nexus_build/nexus/Nexus.java", "nexus_build/nexus/GlobalState.java"], check=True)
                subprocess.run(["javac", "-cp", "nexus_build", filename], check=True)
                artifacts.append({'type': 'java', 'class': f"NexusModule_{i}", 'cp': 'nexus_build;.'})
            except Exception as e:
                print(f"[NEXUS] Java Compilation Failed: {e}")

        for i, code in enumerate(blocks.get('ts', [])):
            filename = f"nexus_module_ts_{i}.ts"
            with open(filename, "w") as f: f.write(code)
            artifacts.append({'type': 'ts', 'src': filename})
            
        for i, code in enumerate(blocks.get('go', [])):
            filename = f"nexus_module_go_{i}.go"
            with open(filename, "w") as f: f.write(code)
            exe_name = f"nexus_module_go_{i}.exe"
            try:
                subprocess.run(["go", "build", "-o", exe_name, filename], check=True)
                artifacts.append({'type': 'go', 'bin': exe_name})
            except Exception as e:
                print(f"[NEXUS] Go Compilation Failed: {e}")

        for i, code in enumerate(blocks.get('py', [])):
             filename = f"nexus_module_py_{i}.py"
             with open(filename, "w") as f: f.write(code)
             artifacts.append({'type': 'py', 'src': filename})

        if blocks.get('web'):
            for i, code in enumerate(blocks.get('web', [])):
                filename = f"nexus_web_{i}.py"
                with open(filename, "w") as f: f.write(code)
                artifacts.append({'type': 'web', 'src': filename})

        print(f"[NEXUS] Compilation setup complete for {len(artifacts)} modules.")
        return artifacts
