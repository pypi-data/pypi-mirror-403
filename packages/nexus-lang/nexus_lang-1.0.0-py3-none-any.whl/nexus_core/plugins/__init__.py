"""
Nexus Plugin System
Extensible plugin architecture for adding custom functionality.
"""

import importlib
import importlib.util
import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from enum import Enum


class PluginType(Enum):
    """Types of plugins."""
    LANGUAGE = "language"      # New language support
    ADAPTER = "adapter"        # Memory adapter
    TRANSFORM = "transform"    # Code transformation
    HOOK = "hook"              # Lifecycle hooks
    CLI = "cli"                # CLI commands


class PluginHook(Enum):
    """Lifecycle hooks for plugins."""
    PRE_PARSE = "pre_parse"
    POST_PARSE = "post_parse"
    PRE_COMPILE = "pre_compile"
    POST_COMPILE = "post_compile"
    PRE_RUN = "pre_run"
    POST_RUN = "post_run"
    ON_ERROR = "on_error"
    ON_STATE_CHANGE = "on_state_change"


@dataclass
class PluginMetadata:
    """Plugin manifest information."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.HOOK
    requires: List[str] = field(default_factory=list)
    entry_point: str = "main"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PluginMetadata':
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            plugin_type=PluginType(data.get("type", "hook")),
            requires=data.get("requires", []),
            entry_point=data.get("entry_point", "main")
        )


class NexusPlugin(ABC):
    """
    Base class for all Nexus plugins.
    
    Plugins extend Nexus functionality by implementing
    hooks, adding languages, or providing adapters.
    """
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self._enabled = True
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def enable(self):
        self._enabled = True
        self.on_enable()
    
    def disable(self):
        self._enabled = False
        self.on_disable()
    
    def on_enable(self):
        """Called when plugin is enabled."""
        pass
    
    def on_disable(self):
        """Called when plugin is disabled."""
        pass
    
    @abstractmethod
    def initialize(self, context: dict) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass


class LanguagePlugin(NexusPlugin):
    """Plugin for adding new language support."""
    
    @abstractmethod
    def get_tag(self) -> str:
        """Return the language tag (e.g., 'lua', 'ruby')."""
        pass
    
    @abstractmethod
    def compile(self, code: str, output_dir: str) -> dict:
        """Compile code and return artifact info."""
        pass
    
    @abstractmethod
    def run(self, artifact: dict) -> Any:
        """Run the compiled artifact."""
        pass


class TransformPlugin(NexusPlugin):
    """Plugin for code transformations."""
    
    @abstractmethod
    def transform(self, code: str, language: str) -> str:
        """Transform code before compilation."""
        pass


class HookPlugin(NexusPlugin):
    """Plugin for lifecycle hooks."""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self._hooks: Dict[PluginHook, Callable] = {}
    
    def register_hook(self, hook: PluginHook, callback: Callable):
        """Register a hook callback."""
        self._hooks[hook] = callback
    
    def get_hooks(self) -> Dict[PluginHook, Callable]:
        return self._hooks


class PluginManager:
    """
    Manages plugin discovery, loading, and execution.
    """
    
    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = Path(plugins_dir or ".nexus_plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        
        self._plugins: Dict[str, NexusPlugin] = {}
        self._hooks: Dict[PluginHook, List[Callable]] = {h: [] for h in PluginHook}
        self._languages: Dict[str, LanguagePlugin] = {}
    
    def discover(self) -> List[PluginMetadata]:
        """Discover plugins in the plugins directory."""
        discovered = []
        
        for path in self.plugins_dir.iterdir():
            if path.is_dir():
                manifest_path = path / "nexus_plugin.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            data = json.load(f)
                        discovered.append(PluginMetadata.from_dict(data))
                    except Exception as e:
                        print(f"[NEXUS] Error reading plugin manifest {path}: {e}")
        
        return discovered
    
    def load(self, name: str) -> Optional[NexusPlugin]:
        """Load a plugin by name."""
        if name in self._plugins:
            return self._plugins[name]
        
        plugin_dir = self.plugins_dir / name
        manifest_path = plugin_dir / "nexus_plugin.json"
        
        if not manifest_path.exists():
            print(f"[NEXUS] Plugin not found: {name}")
            return None
        
        try:
            # Load manifest
            with open(manifest_path) as f:
                manifest_data = json.load(f)
            metadata = PluginMetadata.from_dict(manifest_data)
            
            # Load Python module
            module_path = plugin_dir / f"{metadata.entry_point}.py"
            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get plugin class
            plugin_class = getattr(module, "Plugin", None)
            if not plugin_class:
                print(f"[NEXUS] Plugin {name} has no 'Plugin' class")
                return None
            
            # Instantiate
            plugin = plugin_class(metadata)
            if plugin.initialize({}):
                self._plugins[name] = plugin
                self._register_plugin(plugin)
                print(f"[NEXUS] Loaded plugin: {name}")
                return plugin
            else:
                print(f"[NEXUS] Plugin {name} failed to initialize")
                return None
                
        except Exception as e:
            print(f"[NEXUS] Error loading plugin {name}: {e}")
            return None
    
    def _register_plugin(self, plugin: NexusPlugin):
        """Register plugin hooks and capabilities."""
        if isinstance(plugin, LanguagePlugin):
            tag = plugin.get_tag()
            self._languages[tag] = plugin
            print(f"[NEXUS] Registered language: {tag}")
        
        if isinstance(plugin, HookPlugin):
            for hook, callback in plugin.get_hooks().items():
                self._hooks[hook].append(callback)
    
    def load_all(self) -> int:
        """Load all discovered plugins."""
        count = 0
        for meta in self.discover():
            if self.load(meta.name):
                count += 1
        return count
    
    def unload(self, name: str) -> bool:
        """Unload a plugin."""
        if name not in self._plugins:
            return False
        
        plugin = self._plugins[name]
        plugin.disable()
        del self._plugins[name]
        return True
    
    def get_plugin(self, name: str) -> Optional[NexusPlugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)
    
    def get_language(self, tag: str) -> Optional[LanguagePlugin]:
        """Get a language plugin by tag."""
        return self._languages.get(tag)
    
    def execute_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook."""
        results = []
        for callback in self._hooks[hook]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"[NEXUS] Hook {hook.value} error: {e}")
        return results
    
    def list_plugins(self) -> List[dict]:
        """List all loaded plugins."""
        return [
            {
                "name": p.name,
                "version": p.metadata.version,
                "type": p.metadata.plugin_type.value,
                "enabled": p.enabled
            }
            for p in self._plugins.values()
        ]


def create_plugin_template(name: str, plugin_type: PluginType, output_dir: str = "."):
    """Create a plugin template."""
    plugin_dir = Path(output_dir) / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manifest
    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": f"A Nexus {plugin_type.value} plugin",
        "author": "",
        "type": plugin_type.value,
        "entry_point": "main",
        "requires": []
    }
    
    with open(plugin_dir / "nexus_plugin.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create main.py based on type
    if plugin_type == PluginType.LANGUAGE:
        template = '''"""
Nexus Language Plugin: {name}
"""

from nexus_core.plugins import LanguagePlugin, PluginMetadata


class Plugin(LanguagePlugin):
    def initialize(self, context: dict) -> bool:
        return True
    
    def get_tag(self) -> str:
        return "{tag}"
    
    def compile(self, code: str, output_dir: str) -> dict:
        # Implement compilation
        return {{"type": "{tag}", "compiled": True}}
    
    def run(self, artifact: dict) -> any:
        # Implement execution
        pass
'''
        template = template.format(name=name, tag=name.lower())
    
    elif plugin_type == PluginType.HOOK:
        template = '''"""
Nexus Hook Plugin: {name}
"""

from nexus_core.plugins import HookPlugin, PluginMetadata, PluginHook


class Plugin(HookPlugin):
    def initialize(self, context: dict) -> bool:
        self.register_hook(PluginHook.PRE_COMPILE, self.on_pre_compile)
        self.register_hook(PluginHook.POST_COMPILE, self.on_post_compile)
        return True
    
    def on_pre_compile(self, blocks: dict):
        print(f"[{name}] Pre-compile hook")
        return blocks
    
    def on_post_compile(self, artifacts: list):
        print(f"[{name}] Post-compile hook")
        return artifacts
'''
        template = template.format(name=name)
    
    else:
        template = '''"""
Nexus Plugin: {name}
"""

from nexus_core.plugins import NexusPlugin, PluginMetadata


class Plugin(NexusPlugin):
    def initialize(self, context: dict) -> bool:
        print(f"[{name}] Initialized")
        return True
'''
        template = template.format(name=name)
    
    with open(plugin_dir / "main.py", 'w') as f:
        f.write(template)
    
    print(f"[NEXUS] Created plugin template: {plugin_dir}")
    return plugin_dir


# Global plugin manager
_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
