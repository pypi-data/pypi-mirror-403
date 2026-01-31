"""
Anemoi Client
High-level client for A2A communication.

Provides a simple API for sending/receiving messages between agent sessions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

from .messages import (
    AnemoiMessage,
    AnemoiMessageType,
    SessionGenealogy,
    SpawnSessionPayload,
    create_spawn_message,
    create_ready_message,
    create_update_message,
    create_wisdom_broadcast,
)
from .transport import (
    Transport,
    FileTransport,
    FileTransportConfig,
    MCPTransport,
    MCPTransportConfig,
)


@dataclass
class AnemoiClientConfig:
    """Configuration for AnemoiClient."""
    transport: Literal["file", "mcp"] = "file"
    base_path: str = "~/.anemoi"
    
    # MCP server settings
    mcp_server_url: str = "http://localhost:5555"
    mcp_application_id: str = "default"
    mcp_privacy_key: str = "default"
    
    # Auto behaviors
    auto_register: bool = True
    auto_acknowledge_spawn: bool = True


class AnemoiClient:
    """
    High-level client for Anemoi A2A communication.
    
    Example usage:
        client = AnemoiClient("session-123")
        client.send_update("Task completed", {"files": ["main.py"]})
        
        # Fork with context inheritance
        child_id = client.fork_session(parent_state)
        
        # Wait for sibling messages
        msg = client.wait_for_mentions(timeout=30)
    """
    
    def __init__(self, 
                 session_id: str, 
                 config: AnemoiClientConfig = None):
        """
        Initialize AnemoiClient.
        
        Args:
            session_id: Current session ID
            config: Client configuration (defaults to file transport)
        """
        self.session_id = session_id
        self.config = config or AnemoiClientConfig()
        
        # Initialize transport
        self.transport = self._create_transport()
        
        # Session genealogy
        self._genealogy: Optional[SessionGenealogy] = None
        
        # Auto-register on init
        if self.config.auto_register:
            self.transport.register_agent(session_id)
    
    def _create_transport(self) -> Transport:
        """Create transport based on config."""
        base_path = Path(self.config.base_path).expanduser()
        
        if self.config.transport == "file":
            return FileTransport(
                session_id=self.session_id,
                config=FileTransportConfig(base_path=base_path)
            )
        elif self.config.transport == "mcp":
            return MCPTransport(
                session_id=self.session_id,
                config=MCPTransportConfig(
                    server_url=self.config.mcp_server_url,
                    application_id=self.config.mcp_application_id,
                    privacy_key=self.config.mcp_privacy_key
                )
            )
        else:
            raise ValueError(f"Unknown transport: {self.config.transport}")
    
    @property
    def genealogy(self) -> Optional[SessionGenealogy]:
        """Get session genealogy."""
        return self._genealogy
    
    def send_message(self,
                     recipients: List[str],
                     msg_type: AnemoiMessageType,
                     payload: Dict[str, Any],
                     trace_id: Optional[str] = None) -> str:
        """
        Send message to one or more sessions.
        
        Args:
            recipients: List of recipient session IDs
            msg_type: Message type
            payload: Message payload
            trace_id: Optional Langfuse trace ID
            
        Returns:
            Message ID
        """
        message = AnemoiMessage.create(
            msg_type=msg_type,
            sender=self.session_id,
            recipients=recipients,
            payload=payload,
            trace_id=trace_id
        )
        
        self.transport.send(message)
        return message.message_id
    
    def receive_messages(self,
                         msg_types: Optional[List[AnemoiMessageType]] = None,
                         since: Optional[datetime] = None,
                         mark_read: bool = True) -> List[AnemoiMessage]:
        """
        Retrieve messages from inbox.
        
        Args:
            msg_types: Optional filter by message types
            since: Optional filter by timestamp
            mark_read: Whether to archive processed messages
            
        Returns:
            List of AnemoiMessage objects
        """
        return self.transport.receive(
            msg_types=msg_types,
            since=since,
            mark_read=mark_read
        )
    
    def wait_for_mentions(self,
                          timeout: int = 30,
                          msg_types: Optional[List[AnemoiMessageType]] = None) -> Optional[AnemoiMessage]:
        """
        Block until a message arrives or timeout.
        
        Args:
            timeout: Timeout in seconds
            msg_types: Optional filter by message types
            
        Returns:
            AnemoiMessage or None if timeout
        """
        return self.transport.wait_for_message(
            timeout=timeout,
            msg_types=msg_types
        )
    
    def list_agents(self) -> List[str]:
        """
        Discover active agent sessions.
        
        Returns:
            List of active session IDs
        """
        return self.transport.list_agents()
    
    def broadcast(self,
                  msg_type: AnemoiMessageType,
                  payload: Dict[str, Any],
                  trace_id: Optional[str] = None) -> str:
        """
        Send message to all known sibling sessions.
        
        Args:
            msg_type: Message type
            payload: Message payload
            trace_id: Optional trace ID
            
        Returns:
            Message ID
        """
        agents = [a for a in self.list_agents() if a != self.session_id]
        return self.send_message(agents, msg_type, payload, trace_id)
    
    def fork_session(self,
                     parent_state: Dict[str, Any],
                     reason: str = "sub-task") -> str:
        """
        Fork current session with context inheritance.
        
        Args:
            parent_state: Current session state dictionary
            reason: Reason for forking
            
        Returns:
            Child session ID
        """
        child_id = f"session_{uuid.uuid4().hex[:12]}"
        
        # Build genealogy
        parent_ancestors = parent_state.get("ancestor_chain", [])
        ancestor_chain = parent_ancestors + [self.session_id]
        
        genealogy = SessionGenealogy(
            session_id=child_id,
            parent_id=self.session_id,
            spawn_reason="fork",
            spawned_at=datetime.utcnow().isoformat() + "Z",
            depth=len(ancestor_chain),
            ancestor_chain=ancestor_chain
        )
        
        # Extract inherited context
        inherited_context = {
            "ai_assistant": parent_state.get("ai_assistant", "claude"),
            "model": parent_state.get("model", "sonnet"),
            "working_directory": parent_state.get("working_directory"),
            "issue_number": parent_state.get("issue_number"),
            "repository": parent_state.get("repository"),
            "branch": parent_state.get("branch"),
        }
        
        # Create spawn message
        spawn_msg = create_spawn_message(
            parent_session_id=self.session_id,
            child_session_id=child_id,
            inherited_context=inherited_context,
            genealogy=genealogy,
            assumptions=parent_state.get("assumptions", []),
            four_directions=parent_state.get("four_directions")
        )
        
        # Send to child's inbox
        self.transport.send(spawn_msg)
        
        # Update own genealogy
        if self._genealogy:
            self._genealogy.add_child(child_id)
        else:
            self._genealogy = SessionGenealogy(
                session_id=self.session_id,
                children=[child_id]
            )
        
        # Register child in agent registry
        self.transport.register_agent(child_id, metadata={
            "parent_id": self.session_id,
            "spawn_reason": reason,
            "status": "pending"
        })
        
        return child_id
    
    def acknowledge_spawn(self) -> Optional[AnemoiMessage]:
        """
        Check for and acknowledge spawn message.
        
        Called when a new session starts to check if it was spawned
        from a parent session.
        
        Returns:
            The spawn message if found, None otherwise
        """
        spawn_messages = self.receive_messages(
            msg_types=[AnemoiMessageType.SPAWN_SESSION],
            mark_read=True
        )
        
        if not spawn_messages:
            return None
        
        spawn_msg = spawn_messages[0]
        
        # Extract genealogy
        payload = spawn_msg.payload
        genealogy_data = payload.get("genealogy", {})
        self._genealogy = SessionGenealogy.from_dict(genealogy_data) if genealogy_data else None
        
        # Get inherited fields
        inherited_fields = list(payload.get("inherited_context", {}).keys())
        if payload.get("four_directions"):
            inherited_fields.extend(["east", "south", "west", "north"])
        if payload.get("assumptions"):
            inherited_fields.append("assumptions")
        
        # Send acknowledgment
        ready_msg = create_ready_message(
            child_session_id=self.session_id,
            parent_session_id=spawn_msg.sender_session_id,
            inherited_fields=inherited_fields
        )
        self.transport.send(ready_msg)
        
        return spawn_msg
    
    def send_update(self,
                    summary: str,
                    details: Dict[str, Any] = None,
                    update_type: str = "content_written") -> str:
        """
        Broadcast session update to siblings/parent.
        
        Args:
            summary: Brief summary of update
            details: Optional details
            update_type: Type of update
            
        Returns:
            Message ID
        """
        return self.broadcast(
            msg_type=AnemoiMessageType.SESSION_UPDATE,
            payload={
                "update_type": update_type,
                "summary": summary,
                "details": details or {}
            }
        )
    
    def broadcast_wisdom(self,
                         patterns: List[str] = None,
                         mistakes: List[str] = None,
                         approaches: List[str] = None,
                         seeds: List[str] = None) -> str:
        """
        Broadcast wisdom on session completion.
        
        Args:
            patterns: Extracted patterns
            mistakes: Avoided mistakes
            approaches: Recommended approaches
            seeds: Seeds for next session
            
        Returns:
            Message ID
        """
        return self.broadcast(
            msg_type=AnemoiMessageType.WISDOM_BROADCAST,
            payload={
                "extracted_patterns": patterns or [],
                "avoided_mistakes": mistakes or [],
                "recommended_approaches": approaches or [],
                "seeds_for_next": seeds or []
            }
        )
    
    def close(self) -> None:
        """
        Close session and notify others.
        
        Broadcasts SESSION_CLOSING and deregisters from registry.
        """
        self.broadcast(
            msg_type=AnemoiMessageType.SESSION_CLOSING,
            payload={
                "final_status": "completed",
                "closed_at": datetime.utcnow().isoformat() + "Z"
            }
        )
        
        self.transport.deregister_agent(self.session_id)
    
    def __enter__(self) -> "AnemoiClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close session."""
        self.close()


# Convenience functions

def initialize_client(session_id: str, 
                      base_path: str = "~/.anemoi",
                      auto_acknowledge: bool = True) -> AnemoiClient:
    """
    Initialize an Anemoi client and check for spawn messages.
    
    Args:
        session_id: Session ID
        base_path: Base path for file transport
        auto_acknowledge: Whether to auto-acknowledge spawn messages
        
    Returns:
        Configured AnemoiClient
    """
    config = AnemoiClientConfig(
        base_path=base_path,
        auto_acknowledge_spawn=auto_acknowledge
    )
    
    client = AnemoiClient(session_id, config)
    
    if auto_acknowledge:
        spawn_msg = client.acknowledge_spawn()
        if spawn_msg:
            print(f"🔄 Inherited context from parent: {spawn_msg.sender_session_id}")
    
    return client
