"""Monitor MCP server connections."""
from __future__ import annotations
import json
import os
import time
from typing import List
from hermes_neurovision.events import VisionEvent

# Watch for MCP state in hermes config
MCP_CONFIG = os.path.expanduser("~/.hermes/config.yaml")
MCP_STATE_DIR = os.path.expanduser("~/.hermes/mcp/")

class McpSource:
    def __init__(self):
        self._known_servers: set = set()
        self._last_check: float = 0.0
    
    def poll(self, since: float) -> List[VisionEvent]:
        now = time.time()
        # Only check every 5 seconds
        if now - self._last_check < 5.0:
            return []
        self._last_check = now
        events = []
        # Check for MCP state files
        if os.path.isdir(MCP_STATE_DIR):
            current_servers = set()
            for fname in os.listdir(MCP_STATE_DIR):
                if fname.endswith('.json'):
                    server_name = fname[:-5]
                    current_servers.add(server_name)
                    if server_name not in self._known_servers:
                        events.append(VisionEvent(
                            timestamp=now, source='mcp',
                            kind='mcp_connected', severity='info',
                            data={'server': server_name},
                        ))
            # Check for disconnections
            for server in self._known_servers - current_servers:
                events.append(VisionEvent(
                    timestamp=now, source='mcp',
                    kind='mcp_disconnected', severity='warning',
                    data={'server': server},
                ))
            self._known_servers = current_servers
        return events

_default = McpSource()
def poll(since: float) -> List[VisionEvent]:
    return _default.poll(since)
