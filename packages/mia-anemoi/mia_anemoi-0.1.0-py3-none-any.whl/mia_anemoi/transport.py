"""
Anemoi Transport Layer
Abstractions for message transport between agents.

Supports:
- FileTransport: File-based message queue (local development)
- MCPTransport: MCP server-based transport (production)
"""

import abc
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .messages import AnemoiMessage, AnemoiMessageType


class Transport(abc.ABC):
    """Abstract base class for message transport."""
    
    @abc.abstractmethod
    def send(self, message: AnemoiMessage) -> bool:
        """Send a message. Returns True if successful."""
        pass
    
    @abc.abstractmethod
    def receive(self, 
                msg_types: Optional[List[AnemoiMessageType]] = None,
                since: Optional[datetime] = None,
                mark_read: bool = True) -> List[AnemoiMessage]:
        """Receive messages from inbox."""
        pass
    
    @abc.abstractmethod
    def wait_for_message(self, 
                         timeout: int = 30,
                         msg_types: Optional[List[AnemoiMessageType]] = None) -> Optional[AnemoiMessage]:
        """Block until a message arrives or timeout."""
        pass
    
    @abc.abstractmethod
    def list_agents(self) -> List[str]:
        """Discover active agents."""
        pass
    
    @abc.abstractmethod
    def register_agent(self, session_id: str, metadata: Dict[str, Any] = None) -> None:
        """Register this agent in the registry."""
        pass
    
    @abc.abstractmethod
    def deregister_agent(self, session_id: str) -> None:
        """Deregister this agent."""
        pass


@dataclass
class FileTransportConfig:
    """Configuration for file-based transport."""
    base_path: Path
    inbox_dir: str = "inbox"
    outbox_dir: str = "outbox"
    archive_dir: str = "archive"
    registry_file: str = "agent_registry.json"


class FileTransport(Transport):
    """
    File-based message transport for local development.
    
    Messages are stored as JSON files in inbox/outbox directories.
    Agent registry is a JSON file tracking active sessions.
    """
    
    def __init__(self, session_id: str, config: FileTransportConfig):
        self.session_id = session_id
        self.config = config
        
        self.messages_dir = config.base_path / "messages"
        self.inbox = self.messages_dir / config.inbox_dir / session_id
        self.outbox = self.messages_dir / config.outbox_dir / session_id
        self.archive = self.messages_dir / config.archive_dir / session_id
        self.registry_file = self.messages_dir / config.registry_file
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create directories if they don't exist."""
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)
        self.archive.mkdir(parents=True, exist_ok=True)
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load agent registry from file."""
        if not self.registry_file.exists():
            return {}
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Save agent registry to file."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def _get_recipient_inbox(self, recipient_id: str) -> Path:
        """Get inbox path for a recipient session."""
        return self.messages_dir / self.config.inbox_dir / recipient_id
    
    def send(self, message: AnemoiMessage) -> bool:
        """Send a message to recipients."""
        try:
            # Write to outbox
            outbox_file = self.outbox / f"{message.message_id}.json"
            with open(outbox_file, 'w') as f:
                json.dump(message.to_dict(), f, indent=2)
            
            # Deliver to each recipient's inbox
            for recipient_id in message.recipient_session_ids:
                recipient_inbox = self._get_recipient_inbox(recipient_id)
                recipient_inbox.mkdir(parents=True, exist_ok=True)
                
                inbox_file = recipient_inbox / f"{message.message_id}.json"
                with open(inbox_file, 'w') as f:
                    json.dump(message.to_dict(), f, indent=2)
            
            return True
        except IOError:
            return False
    
    def receive(self,
                msg_types: Optional[List[AnemoiMessageType]] = None,
                since: Optional[datetime] = None,
                mark_read: bool = True) -> List[AnemoiMessage]:
        """Receive messages from inbox."""
        messages = []
        
        for file_path in self.inbox.glob("msg_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                message = AnemoiMessage.from_dict(data)
                
                # Filter by message type
                if msg_types and message.message_type not in msg_types:
                    continue
                
                # Filter by timestamp
                if since:
                    msg_time = datetime.fromisoformat(
                        message.timestamp.replace('Z', '+00:00')
                    )
                    if msg_time < since:
                        continue
                
                messages.append(message)
                
                # Archive if requested
                if mark_read:
                    archive_file = self.archive / file_path.name
                    file_path.rename(archive_file)
                    
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def wait_for_message(self,
                         timeout: int = 30,
                         msg_types: Optional[List[AnemoiMessageType]] = None) -> Optional[AnemoiMessage]:
        """Block until a message arrives or timeout."""
        poll_interval = 0.5
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            messages = self.receive(msg_types=msg_types, mark_read=True)
            if messages:
                return messages[0]
            time.sleep(poll_interval)
        
        return None
    
    def list_agents(self) -> List[str]:
        """Discover active agent sessions."""
        registry = self._load_registry()
        return [
            session_id 
            for session_id, info in registry.items()
            if info.get("status") == "active"
        ]
    
    def register_agent(self, session_id: str, metadata: Dict[str, Any] = None) -> None:
        """Register this agent in the registry."""
        registry = self._load_registry()
        registry[session_id] = {
            "session_id": session_id,
            "registered_at": datetime.utcnow().isoformat() + "Z",
            "inbox_path": str(self._get_recipient_inbox(session_id)),
            "status": "active",
            **(metadata or {})
        }
        self._save_registry(registry)
    
    def deregister_agent(self, session_id: str) -> None:
        """Deregister this agent."""
        registry = self._load_registry()
        if session_id in registry:
            registry[session_id]["status"] = "closed"
            registry[session_id]["closed_at"] = datetime.utcnow().isoformat() + "Z"
            self._save_registry(registry)


@dataclass
class MCPTransportConfig:
    """Configuration for MCP server transport."""
    server_url: str = "http://localhost:5555"
    application_id: str = "simexp"
    privacy_key: str = "default"


class MCPTransport(Transport):
    """
    MCP server-based transport for production use.
    
    Connects to an Anemoi MCP server for real-time A2A messaging.
    Uses threads for message grouping and routing.
    """
    
    def __init__(self, session_id: str, config: MCPTransportConfig):
        self.session_id = session_id
        self.config = config
        self._connected = False
        self._threads: Dict[str, List[AnemoiMessage]] = {}
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        # TODO: Implement MCP client connection
        # This will use the Anemoi MCP primitives:
        # - create_thread()
        # - send_message()
        # - wait_for_mentions()
        # - list_agents()
        # - close_thread()
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        self._connected = False
    
    def send(self, message: AnemoiMessage) -> bool:
        """Send a message via MCP server."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        # TODO: Implement MCP send_message call
        # For now, store in local thread cache
        thread_id = message.thread_id
        if thread_id not in self._threads:
            self._threads[thread_id] = []
        self._threads[thread_id].append(message)
        
        return True
    
    def receive(self,
                msg_types: Optional[List[AnemoiMessageType]] = None,
                since: Optional[datetime] = None,
                mark_read: bool = True) -> List[AnemoiMessage]:
        """Receive messages from MCP server."""
        if not self._connected:
            return []
        
        # TODO: Implement MCP wait_for_mentions call
        # For now, return from local cache
        messages = []
        for thread_msgs in self._threads.values():
            for msg in thread_msgs:
                if self.session_id in msg.recipient_session_ids:
                    if msg_types and msg.message_type not in msg_types:
                        continue
                    messages.append(msg)
        
        return messages
    
    def wait_for_message(self,
                         timeout: int = 30,
                         msg_types: Optional[List[AnemoiMessageType]] = None) -> Optional[AnemoiMessage]:
        """Wait for message from MCP server."""
        # TODO: Implement MCP wait_for_mentions with timeout
        messages = self.receive(msg_types=msg_types)
        return messages[0] if messages else None
    
    def list_agents(self) -> List[str]:
        """List agents via MCP server."""
        # TODO: Implement MCP list_agents call
        return []
    
    def register_agent(self, session_id: str, metadata: Dict[str, Any] = None) -> None:
        """Register with MCP server."""
        # TODO: Implement agent registration
        pass
    
    def deregister_agent(self, session_id: str) -> None:
        """Deregister from MCP server."""
        # TODO: Implement agent deregistration
        pass
