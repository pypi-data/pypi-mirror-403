"""
Anemoi Message Types and Schemas
A2A (Agent-to-Agent) message definitions for session coordination.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Literal


class AnemoiMessageType(Enum):
    """Standard A2A message types for session coordination."""
    # Session lifecycle
    SPAWN_SESSION = "SPAWN_SESSION"
    CHILD_SESSION_READY = "CHILD_SESSION_READY"
    SESSION_CLOSING = "SESSION_CLOSING"
    
    # Communication
    SESSION_UPDATE = "SESSION_UPDATE"
    CONTEXT_REQUEST = "CONTEXT_REQUEST"
    CONTEXT_RESPONSE = "CONTEXT_RESPONSE"
    
    # Wisdom sharing
    WISDOM_BROADCAST = "WISDOM_BROADCAST"
    
    # Agent discovery
    AGENT_REGISTER = "AGENT_REGISTER"
    AGENT_DEREGISTER = "AGENT_DEREGISTER"
    AGENT_PING = "AGENT_PING"
    AGENT_PONG = "AGENT_PONG"


@dataclass
class SessionGenealogy:
    """Tracks hierarchical session relationships."""
    session_id: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    siblings: List[str] = field(default_factory=list)
    spawn_reason: Literal["new", "fork", "resume", "handoff"] = "new"
    spawned_at: Optional[str] = None
    depth: int = 0
    ancestor_chain: List[str] = field(default_factory=list)
    
    def add_child(self, child_id: str) -> None:
        """Register a child session."""
        if child_id not in self.children:
            self.children.append(child_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionGenealogy":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AnemoiMessage:
    """Base class for all A2A messages."""
    message_type: AnemoiMessageType
    message_id: str
    sender_session_id: str
    recipient_session_ids: List[str]
    timestamp: str
    payload: Dict[str, Any]
    thread_id: Optional[str] = None
    trace_id: Optional[str] = None
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    
    @classmethod
    def create(cls, 
               msg_type: AnemoiMessageType, 
               sender: str, 
               recipients: List[str], 
               payload: Dict[str, Any],
               thread_id: Optional[str] = None,
               trace_id: Optional[str] = None) -> "AnemoiMessage":
        """Factory method to create a new message."""
        return cls(
            message_type=msg_type,
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            sender_session_id=sender,
            recipient_session_ids=recipients,
            timestamp=datetime.utcnow().isoformat() + "Z",
            payload=payload,
            thread_id=thread_id or f"thread_{uuid.uuid4().hex[:8]}",
            trace_id=trace_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "message_type": self.message_type.value,
            "message_id": self.message_id,
            "sender_session_id": self.sender_session_id,
            "recipient_session_ids": self.recipient_session_ids,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "thread_id": self.thread_id,
            "trace_id": self.trace_id,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnemoiMessage":
        """Create from dictionary."""
        return cls(
            message_type=AnemoiMessageType(data["message_type"]),
            message_id=data["message_id"],
            sender_session_id=data["sender_session_id"],
            recipient_session_ids=data["recipient_session_ids"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            thread_id=data.get("thread_id"),
            trace_id=data.get("trace_id"),
            acknowledged=data.get("acknowledged", False),
            acknowledged_at=data.get("acknowledged_at")
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AnemoiMessage":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def acknowledge(self) -> None:
        """Mark message as acknowledged."""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow().isoformat() + "Z"


# Payload dataclasses

@dataclass
class SpawnSessionPayload:
    """Context transferred when spawning a child session."""
    inherited_context: Dict[str, Any]
    genealogy: SessionGenealogy
    assumptions: List[Dict[str, Any]] = field(default_factory=list)
    four_directions_state: Optional[Dict[str, Any]] = None
    learnings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "inherited_context": self.inherited_context,
            "genealogy": self.genealogy.to_dict() if isinstance(self.genealogy, SessionGenealogy) else self.genealogy,
            "assumptions": self.assumptions,
            "four_directions": self.four_directions_state,
            "learnings": self.learnings,
            "warnings": self.warnings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpawnSessionPayload":
        genealogy_data = data.get("genealogy", {})
        genealogy = SessionGenealogy.from_dict(genealogy_data) if genealogy_data else None
        return cls(
            inherited_context=data.get("inherited_context", {}),
            genealogy=genealogy,
            assumptions=data.get("assumptions", []),
            four_directions_state=data.get("four_directions"),
            learnings=data.get("learnings", []),
            warnings=data.get("warnings", [])
        )


@dataclass
class SessionReadyPayload:
    """Acknowledgment payload when child session initializes."""
    status: str
    inherited_fields: List[str]
    child_trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionReadyPayload":
        return cls(**data)


@dataclass
class SessionUpdatePayload:
    """Payload for session update broadcasts."""
    update_type: Literal["content_written", "file_added", "published", "completed", "wisdom_extracted"]
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionUpdatePayload":
        return cls(**data)


@dataclass
class WisdomBroadcastPayload:
    """Payload for wisdom broadcast on session completion."""
    extracted_patterns: List[str] = field(default_factory=list)
    avoided_mistakes: List[str] = field(default_factory=list)
    recommended_approaches: List[str] = field(default_factory=list)
    seeds_for_next: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WisdomBroadcastPayload":
        return cls(**data)


# Helper functions for creating common messages

def create_spawn_message(parent_session_id: str,
                         child_session_id: str,
                         inherited_context: Dict[str, Any],
                         genealogy: SessionGenealogy,
                         assumptions: List[Dict[str, Any]] = None,
                         four_directions: Dict[str, Any] = None,
                         trace_id: Optional[str] = None) -> AnemoiMessage:
    """Create a SPAWN_SESSION message for forking."""
    payload = SpawnSessionPayload(
        inherited_context=inherited_context,
        genealogy=genealogy,
        assumptions=assumptions or [],
        four_directions_state=four_directions
    )
    
    return AnemoiMessage.create(
        msg_type=AnemoiMessageType.SPAWN_SESSION,
        sender=parent_session_id,
        recipients=[child_session_id],
        payload=payload.to_dict(),
        trace_id=trace_id
    )


def create_ready_message(child_session_id: str,
                         parent_session_id: str,
                         inherited_fields: List[str],
                         trace_id: Optional[str] = None) -> AnemoiMessage:
    """Create a CHILD_SESSION_READY acknowledgment message."""
    payload = SessionReadyPayload(
        status="initialized_with_inherited_context",
        inherited_fields=inherited_fields,
        child_trace_id=trace_id
    )
    
    return AnemoiMessage.create(
        msg_type=AnemoiMessageType.CHILD_SESSION_READY,
        sender=child_session_id,
        recipients=[parent_session_id],
        payload=payload.to_dict(),
        trace_id=trace_id
    )


def create_update_message(session_id: str,
                          recipients: List[str],
                          update_type: str,
                          summary: str,
                          details: Dict[str, Any] = None,
                          trace_id: Optional[str] = None) -> AnemoiMessage:
    """Create a SESSION_UPDATE broadcast message."""
    payload = SessionUpdatePayload(
        update_type=update_type,
        summary=summary,
        details=details or {}
    )
    
    return AnemoiMessage.create(
        msg_type=AnemoiMessageType.SESSION_UPDATE,
        sender=session_id,
        recipients=recipients,
        payload=payload.to_dict(),
        trace_id=trace_id
    )


def create_wisdom_broadcast(session_id: str,
                            recipients: List[str],
                            patterns: List[str] = None,
                            mistakes: List[str] = None,
                            approaches: List[str] = None,
                            seeds: List[str] = None,
                            trace_id: Optional[str] = None) -> AnemoiMessage:
    """Create a WISDOM_BROADCAST message on session completion."""
    payload = WisdomBroadcastPayload(
        extracted_patterns=patterns or [],
        avoided_mistakes=mistakes or [],
        recommended_approaches=approaches or [],
        seeds_for_next=seeds or []
    )
    
    return AnemoiMessage.create(
        msg_type=AnemoiMessageType.WISDOM_BROADCAST,
        sender=session_id,
        recipients=recipients,
        payload=payload.to_dict(),
        trace_id=trace_id
    )
