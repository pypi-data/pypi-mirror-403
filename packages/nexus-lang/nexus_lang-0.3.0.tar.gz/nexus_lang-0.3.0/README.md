# ⚡ Nexus

**The Universal Polyglot Runtime**

Write Python, C, Rust, Java, Go, and TypeScript in a single `.nexus` file with **zero-copy shared memory** between all languages.

```
>>>schema
{ "counter": 0, "message": "Hello!" }

>>>py
print("[Python] Hello from the Singularity!")

>>>c
printf("[C] Counter: %d\n", counter);

>>>rs
println!("[Rust] Message: {}", message);
```

## 🚀 Quick Start

### Install

```bash
pip install nexus-lang
```

### Create a Project

```bash
nexus init my-project
cd my-project
nexus run main.nexus
```

### Or Run Existing File

```bash
nexus run app.nexus
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-language** | Python, C, Rust, Java, Go, TypeScript in one file |
| **Zero-copy memory** | Shared memory segment accessible from all languages |
| **Auto-compilation** | Automatic compilation of C, Rust, Java, Go modules |
| **Process supervision** | Phoenix Protocol auto-restarts crashed modules |
| **Type generation** | Auto-generates types from JSON schema |
| **Web ready** | Built-in FastAPI integration for web blocks |

## 📖 Language Blocks

Use `>>>` followed by language tag to define code blocks:

| Tag | Language | Runtime |
|-----|----------|---------|
| `>>>py` | Python | Python 3.8+ |
| `>>>c` | C | GCC/Clang |
| `>>>rs` | Rust | Cargo |
| `>>>java` | Java | JDK 11+ |
| `>>>go` | Go | Go 1.19+ |
| `>>>ts` | TypeScript | ts-node |
| `>>>web` | FastAPI | uvicorn |
| `>>>schema` | JSON Schema | Type generation |

## 🛠️ CLI Commands

```bash
nexus init <name>              # Create new project
nexus init <name> -t web       # Create with web template
nexus run <file.nexus>         # Run orchestrator
nexus compile <file.nexus>     # Compile only
nexus status                   # Show system status
nexus schema validate <file>   # Validate JSON schema
nexus schema generate <file>   # Generate type files
```

## 📦 Project Structure

```
my-project/
├── main.nexus           # Main application
├── nexus_generated/     # Auto-generated types
│   ├── nexus_types.h    # C structs
│   ├── nexus_types.rs   # Rust structs
│   ├── GlobalState.java # Java class
│   └── types.ts         # TypeScript interface
├── nexus.mem            # Shared memory (runtime)
└── .gitignore
```

## 🔗 Shared Memory API

All languages access the same shared state:

**Python:**
```python
from nexus_core import NexusMemory
mem = NexusMemory(create=False)
state = mem.read_json().unwrap()
```

**C:**
```c
#include "nexus.h"
char* state = nexus_read_state();
nexus_write_state("{\"counter\": 1}");
```

**Rust:**
```rust
use nexus_adapter::Nexus;
let mut nexus = Nexus::new()?;
let state = nexus.read_state();
```

**Java:**
```java
import nexus.Nexus;
Nexus mem = new Nexus();
String state = mem.readState();
```

## 🎯 Use Cases

- **AI/ML Pipelines**: Python model + C inference engine
- **High-performance web**: FastAPI + C/Rust compute
- **Microservices**: Polyglot services with shared state
- **Game engines**: Lua scripting + C++ performance
- **Robotics**: ROS-like architecture, simpler syntax

## 📋 Requirements

- Python 3.8+
- Optional: GCC/Clang (for C blocks)
- Optional: Cargo (for Rust blocks)
- Optional: JDK 11+ (for Java blocks)
- Optional: Go 1.19+ (for Go blocks)

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

**Built with ⚡ by the Nexus Team**
