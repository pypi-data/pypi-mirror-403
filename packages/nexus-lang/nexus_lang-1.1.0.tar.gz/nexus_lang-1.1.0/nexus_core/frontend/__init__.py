"""
Nexus Frontend Framework Support
React and Next.js integration with auto-generated WebSocket sync.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class FrontendConfig:
    """Configuration for frontend projects."""
    framework: str  # 'react', 'nextjs', 'vue'
    port: int = 3000
    gateway_url: str = "ws://localhost:8765/ws"
    auto_sync: bool = True
    typescript: bool = True


class ReactGenerator:
    """
    Generates React components with Nexus WebSocket integration.
    """
    
    NEXUS_HOOK = '''
// Auto-generated Nexus WebSocket hook
import { useState, useEffect, useCallback, useRef } from 'react';

interface NexusState {
  [key: string]: any;
}

interface UseNexusOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
}

export function useNexus(options: UseNexusOptions = {}) {
  const {
    url = '{gateway_url}',
    autoConnect = true,
    reconnectInterval = 3000
  } = options;

  const [state, setState] = useState<NexusState>({});
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        setConnected(true);
        setError(null);
        console.log('[Nexus] Connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'welcome') {
          setState(data.state || {});
        } else if (data.type === 'event' && data.event?.type === 'state_update') {
          setState(data.event.payload);
        } else if (data.type === 'state') {
          setState(data.data);
        }
      };

      ws.onerror = (e) => {
        setError('Connection error');
        console.error('[Nexus] Error:', e);
      };

      ws.onclose = () => {
        setConnected(false);
        console.log('[Nexus] Disconnected');
        
        // Auto-reconnect
        if (autoConnect) {
          reconnectRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      setError(String(e));
    }
  }, [url, autoConnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((type: string, payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...payload }));
    }
  }, []);

  const updateState = useCallback((newState: Partial<NexusState>) => {
    send('set_state', { data: { ...state, ...newState } });
  }, [send, state]);

  const subscribe = useCallback((channels: string[]) => {
    send('subscribe', { channels });
  }, [send]);

  const publish = useCallback((channel: string, message: any) => {
    send('publish', { channel, message });
  }, [send]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => disconnect();
  }, [autoConnect, connect, disconnect]);

  return {
    state,
    connected,
    error,
    connect,
    disconnect,
    updateState,
    subscribe,
    publish,
    send
  };
}

// Convenience hook for specific state keys
export function useNexusState<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const { state, updateState } = useNexus();
  const value = (state[key] as T) ?? defaultValue;
  const setValue = (newValue: T) => updateState({ [key]: newValue });
  return [value, setValue];
}
'''

    COMPONENT_TEMPLATE = '''
import React from 'react';
import { useNexus } from './useNexus';

{component_code}
'''

    def __init__(self, config: FrontendConfig):
        self.config = config
    
    def generate_hook(self, output_dir: str) -> str:
        """Generate the useNexus hook file."""
        hook_code = self.NEXUS_HOOK.replace('{gateway_url}', self.config.gateway_url)
        
        hooks_dir = Path(output_dir) / 'hooks'
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        ext = '.ts' if self.config.typescript else '.js'
        hook_path = hooks_dir / f'useNexus{ext}'
        
        with open(hook_path, 'w') as f:
            f.write(hook_code)
        
        return str(hook_path)
    
    def generate_component(self, code: str, output_dir: str, name: str = 'NexusComponent') -> str:
        """Generate a React component with Nexus integration."""
        components_dir = Path(output_dir) / 'components'
        components_dir.mkdir(parents=True, exist_ok=True)
        
        ext = '.tsx' if self.config.typescript else '.jsx'
        component_path = components_dir / f'{name}{ext}'
        
        full_code = self.COMPONENT_TEMPLATE.replace('{component_code}', code)
        
        with open(component_path, 'w') as f:
            f.write(full_code)
        
        return str(component_path)


class NextJSGenerator:
    """
    Generates Next.js pages/components with Nexus integration.
    """
    
    APP_TEMPLATE = '''
// app/layout.tsx - Next.js App Router layout with Nexus provider
import type {{ Metadata }} from 'next';
import {{ NexusProvider }} from '@/components/NexusProvider';
import './globals.css';

export const metadata: Metadata = {{
  title: '{app_name}',
  description: 'Powered by Nexus Polyglot Runtime',
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="en">
      <body>
        <NexusProvider gatewayUrl="{gateway_url}">
          {{children}}
        </NexusProvider>
      </body>
    </html>
  );
}}
'''

    PROVIDER_TEMPLATE = '''
'use client';

import React, {{ createContext, useContext, ReactNode }} from 'react';
import {{ useNexus }} from '@/hooks/useNexus';

interface NexusContextType {{
  state: Record<string, any>;
  connected: boolean;
  updateState: (newState: Partial<Record<string, any>>) => void;
  subscribe: (channels: string[]) => void;
  publish: (channel: string, message: any) => void;
}}

const NexusContext = createContext<NexusContextType | null>(null);

export function NexusProvider({{ 
  children,
  gatewayUrl = '{gateway_url}'
}}: {{ 
  children: ReactNode;
  gatewayUrl?: string;
}}) {{
  const nexus = useNexus({{ url: gatewayUrl }});
  
  return (
    <NexusContext.Provider value={{nexus}}>
      {{children}}
    </NexusContext.Provider>
  );
}}

export function useNexusContext() {{
  const context = useContext(NexusContext);
  if (!context) {{
    throw new Error('useNexusContext must be used within NexusProvider');
  }}
  return context;
}}
'''

    PAGE_TEMPLATE = '''
'use client';

import {{ useNexusContext }} from '@/components/NexusProvider';

export default function {page_name}() {{
  const {{ state, connected, updateState }} = useNexusContext();
  
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">
          ⚡ Nexus + Next.js
        </h1>
        
        <div className="mb-4">
          Status: {{connected ? '🟢 Connected' : '🔴 Disconnected'}}
        </div>
        
        <div className="bg-gray-100 p-4 rounded-lg">
          <pre>{{JSON.stringify(state, null, 2)}}</pre>
        </div>
        
        {page_content}
      </div>
    </main>
  );
}}
'''

    def __init__(self, config: FrontendConfig):
        self.config = config
    
    def generate_project(self, output_dir: str, app_name: str = 'nexus-app') -> dict:
        """Generate a complete Next.js project structure."""
        base = Path(output_dir)
        
        # Create directories
        (base / 'app').mkdir(parents=True, exist_ok=True)
        (base / 'components').mkdir(parents=True, exist_ok=True)
        (base / 'hooks').mkdir(parents=True, exist_ok=True)
        
        # Generate files
        files = {}
        
        # Hook
        react_gen = ReactGenerator(self.config)
        files['hooks/useNexus.ts'] = react_gen.generate_hook(str(base))
        
        # Provider
        provider_code = self.PROVIDER_TEMPLATE.replace('{gateway_url}', self.config.gateway_url)
        provider_path = base / 'components' / 'NexusProvider.tsx'
        with open(provider_path, 'w') as f:
            f.write(provider_code)
        files['components/NexusProvider.tsx'] = str(provider_path)
        
        # Layout
        layout_code = self.APP_TEMPLATE.format(
            app_name=app_name,
            gateway_url=self.config.gateway_url
        )
        layout_path = base / 'app' / 'layout.tsx'
        with open(layout_path, 'w') as f:
            f.write(layout_code)
        files['app/layout.tsx'] = str(layout_path)
        
        # Page
        page_code = self.PAGE_TEMPLATE.format(
            page_name='Home',
            page_content=''
        )
        page_path = base / 'app' / 'page.tsx'
        with open(page_path, 'w') as f:
            f.write(page_code)
        files['app/page.tsx'] = str(page_path)
        
        return files


class FrontendCompiler:
    """
    Compiles frontend blocks from .nexus files.
    """
    
    def __init__(self, output_dir: str = 'nexus_frontend'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def compile_react(self, code: str, config: FrontendConfig = None) -> dict:
        """Compile a >>>react block."""
        config = config or FrontendConfig(framework='react')
        generator = ReactGenerator(config)
        
        # Generate hook
        hook_path = generator.generate_hook(str(self.output_dir))
        
        # Generate component from user code
        component_path = generator.generate_component(code, str(self.output_dir))
        
        return {
            'type': 'react',
            'files': {
                'hook': hook_path,
                'component': component_path
            },
            'instructions': f'''
To run:
  cd {self.output_dir}
  npx create-react-app . --template typescript
  # Copy generated files to src/
  npm start
'''
        }
    
    def compile_nextjs(self, code: str, config: FrontendConfig = None) -> dict:
        """Compile a >>>nextjs block."""
        config = config or FrontendConfig(framework='nextjs')
        generator = NextJSGenerator(config)
        
        files = generator.generate_project(str(self.output_dir))
        
        return {
            'type': 'nextjs',
            'files': files,
            'instructions': f'''
To run:
  cd {self.output_dir}
  npx create-next-app@latest . --typescript --tailwind --app
  # Files are already generated, just run:
  npm run dev
'''
        }


def get_frontend_compiler(output_dir: str = 'nexus_frontend') -> FrontendCompiler:
    """Get a frontend compiler instance."""
    return FrontendCompiler(output_dir)
