"""
SimExp Anemoi Client Module
A2A (Agent-to-Agent) communication client for session coordination

This module extends mia-anemoi's AnemoiClient with SimExp-specific
functionality, including integration with the session manager and
Four Directions framework.

Phase 1: File-based message transport (uses ~/.simexp)
Phase 2: MCP server transport (via Anemoi MCP)
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Try to import from mia-anemoi package
try:
    from mia_anemoi import (
        AnemoiClient as BaseAnemoiClient,
        AnemoiClientConfig,
        AnemoiMessage,
        AnemoiMessageType,
        SessionGenealogy,
        create_spawn_message,
        create_ready_message,
        create_update_message,
        create_wisdom_broadcast,
    )
    HAS_MIA_ANEMOI = True
except ImportError:
    HAS_MIA_ANEMOI = False
    # Fallback to local implementations
    from .anemoi_messages import (
        AnemoiMessage,
        AnemoiMessageType,
        SessionGenealogy,
        create_spawn_message,
        create_ready_message,
        create_update_message,
        create_wisdom_broadcast,
    )

from .continuations import (
    ContinuationManager,
    ContinuationState,
    generate_session_id
)


class AnemoiClient:
    """
    SimExp Anemoi client for A2A communication.
    
    Uses mia-anemoi if available, otherwise falls back to file-based transport.
    """
    
    MESSAGES_DIR = "messages"
    INBOX_DIR = "inbox"
    OUTBOX_DIR = "outbox"
    ARCHIVE_DIR = "archive"
    REGISTRY_FILE = "agent_registry.json"
    
    def __init__(self, session_id: str, base_path: str = None):
        """
        Initialize AnemoiClient.
        
        Args:
            session_id: Current session ID
            base_path: Base path for message storage (default: ~/.simexp)
        """
        self.session_id = session_id
        
        if base_path:
            self.base_path = Path(base_path).expanduser()
        else:
            self.base_path = Path.home() / ".simexp"
        
        # Check if we can use mia-anemoi
        self._use_mia_anemoi = HAS_MIA_ANEMOI
        
        if self._use_mia_anemoi:
            # Use mia-anemoi transport
            config = AnemoiClientConfig(
                transport="file",
                base_path=str(self.base_path)
            )
            self._base_client = BaseAnemoiClient(session_id, config)
        else:
            # Setup file-based transport directly
            self._base_client = None
            self.messages_dir = self.base_path / self.MESSAGES_DIR
            self.inbox = self.messages_dir / self.INBOX_DIR / session_id
            self.outbox = self.messages_dir / self.OUTBOX_DIR / session_id
            self.archive = self.messages_dir / self.ARCHIVE_DIR / session_id
            self.registry_file = self.messages_dir / self.REGISTRY_FILE
            self._ensure_directories()
            self._register_agent()
        
        # SimExp-specific: continuation manager
        self.continuation_mgr = ContinuationManager(str(self.base_path))
    
    def _ensure_directories(self) -> None:
        """Create message directories if they don't exist."""
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)
        self.archive.mkdir(parents=True, exist_ok=True)
    
    def _register_agent(self) -> None:
        """Register this session in the agent registry."""
        registry = self._load_registry()
        registry[self.session_id] = {
            "session_id": self.session_id,
            "registered_at": datetime.utcnow().isoformat() + "Z",
            "inbox_path": str(self.inbox),
            "status": "active"
        }
        self._save_registry(registry)
    
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
        return self.messages_dir / self.INBOX_DIR / recipient_id
    
    def send_message(self,
                     recipients: List[str],
                     msg_type: AnemoiMessageType,
                     payload: Dict[str, Any],
                     trace_id: Optional[str] = None) -> str:
        """Send message to one or more sessions."""
        if self._use_mia_anemoi:
            return self._base_client.send_message(recipients, msg_type, payload, trace_id)
        
        # Fallback: file-based transport
        message = AnemoiMessage.create(
            msg_type=msg_type,
            sender=self.session_id,
            recipients=recipients,
            payload=payload,
            trace_id=trace_id
        )
        
        # Write to outbox
        outbox_file = self.outbox / f"{message.message_id}.json"
        with open(outbox_file, 'w') as f:
            json.dump(message.to_dict(), f, indent=2)
        
        # Deliver to each recipient's inbox
        for recipient_id in recipients:
            recipient_inbox = self._get_recipient_inbox(recipient_id)
            recipient_inbox.mkdir(parents=True, exist_ok=True)
            inbox_file = recipient_inbox / f"{message.message_id}.json"
            with open(inbox_file, 'w') as f:
                json.dump(message.to_dict(), f, indent=2)
        
        return message.message_id
    
    def receive_messages(self,
                         msg_types: Optional[List[AnemoiMessageType]] = None,
                         since: Optional[datetime] = None,
                         mark_read: bool = True) -> List[AnemoiMessage]:
        """Retrieve messages from inbox."""
        if self._use_mia_anemoi:
            return self._base_client.receive_messages(msg_types, since, mark_read)
        
        # Fallback: file-based transport
        messages = []
        for file_path in self.inbox.glob("msg_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                message = AnemoiMessage.from_dict(data)
                
                if msg_types and message.message_type not in msg_types:
                    continue
                if since:
                    msg_time = datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
                    if msg_time < since:
                        continue
                
                messages.append(message)
                if mark_read:
                    archive_file = self.archive / file_path.name
                    file_path.rename(archive_file)
            except (json.JSONDecodeError, IOError):
                continue
        
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def wait_for_mentions(self, timeout: int = 30, poll_interval: float = 0.5) -> Optional[AnemoiMessage]:
        """Block until a message arrives or timeout."""
        if self._use_mia_anemoi:
            return self._base_client.wait_for_mentions(timeout)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.receive_messages(mark_read=True)
            if messages:
                return messages[0]
            time.sleep(poll_interval)
        return None
    
    def list_agents(self) -> List[str]:
        """Discover active agent sessions."""
        if self._use_mia_anemoi:
            return self._base_client.list_agents()
        
        registry = self._load_registry()
        return [sid for sid, info in registry.items() if info.get("status") == "active"]
    
    def broadcast(self, msg_type: AnemoiMessageType, payload: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Send message to all known sibling sessions."""
        agents = [a for a in self.list_agents() if a != self.session_id]
        if not agents:
            return self.send_message([], msg_type, payload, trace_id)
        return self.send_message(agents, msg_type, payload, trace_id)
    
    def fork_session(self, parent_state: Dict[str, Any], reason: str = "sub-task") -> str:
        """Fork current session with context inheritance."""
        child_id = generate_session_id()
        
        # Create continuation for child
        continuation = self.continuation_mgr.fork_continuation(
            parent_state=parent_state,
            child_session_id=child_id
        )
        continuation.spawn_reason = "fork"
        self.continuation_mgr.save_continuation(continuation)
        
        # Build genealogy
        genealogy = SessionGenealogy(
            session_id=child_id,
            parent_id=self.session_id,
            spawn_reason="fork",
            spawned_at=datetime.utcnow().isoformat() + "Z",
            depth=continuation.genealogy_depth,
            ancestor_chain=continuation.ancestor_chain
        )
        
        # Create spawn message
        spawn_msg = create_spawn_message(
            parent_session_id=self.session_id,
            child_session_id=child_id,
            inherited_context=continuation.get_inherited_context(),
            genealogy=genealogy,
            assumptions=[a.to_dict() for a in continuation.assumptions],
            four_directions={
                "east": continuation.east.to_dict(),
                "south": continuation.south.to_dict(),
                "west": continuation.west.to_dict(),
                "north": continuation.north.to_dict()
            }
        )
        
        # Write spawn message to child's inbox
        if self._use_mia_anemoi:
            self._base_client.transport.send(spawn_msg)
        else:
            child_inbox = self._get_recipient_inbox(child_id)
            child_inbox.mkdir(parents=True, exist_ok=True)
            inbox_file = child_inbox / f"{spawn_msg.message_id}.json"
            with open(inbox_file, 'w') as f:
                json.dump(spawn_msg.to_dict(), f, indent=2)
        
        # Update registry
        self._update_genealogy_registry(child_id, self.session_id)
        
        return child_id
    
    def _update_genealogy_registry(self, child_id: str, parent_id: str) -> None:
        """Update registry with parent-child relationship."""
        registry = self._load_registry()
        if parent_id in registry:
            children = registry[parent_id].get("children", [])
            if child_id not in children:
                children.append(child_id)
            registry[parent_id]["children"] = children
        registry[child_id] = {
            "session_id": child_id,
            "parent_id": parent_id,
            "registered_at": datetime.utcnow().isoformat() + "Z",
            "inbox_path": str(self._get_recipient_inbox(child_id)) if not self._use_mia_anemoi else "",
            "status": "pending"
        }
        self._save_registry(registry)
    
    def acknowledge_spawn(self) -> Optional[AnemoiMessage]:
        """Check for and acknowledge spawn message."""
        spawn_messages = self.receive_messages(
            msg_types=[AnemoiMessageType.SPAWN_SESSION],
            mark_read=True
        )
        
        if not spawn_messages:
            return None
        
        spawn_msg = spawn_messages[0]
        payload = spawn_msg.payload
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
        self.send_message(
            recipients=[spawn_msg.sender_session_id],
            msg_type=AnemoiMessageType.CHILD_SESSION_READY,
            payload=ready_msg.payload
        )
        
        # Update status
        registry = self._load_registry()
        if self.session_id in registry:
            registry[self.session_id]["status"] = "active"
            self._save_registry(registry)
        
        return spawn_msg
    
    def notify_update(self, update_type: str, summary: str, details: Dict[str, Any] = None) -> str:
        """Broadcast session update to siblings/parent."""
        return self.broadcast(
            msg_type=AnemoiMessageType.SESSION_UPDATE,
            payload={"update_type": update_type, "summary": summary, "details": details or {}}
        )
    
    def broadcast_wisdom(self, patterns: List[str], mistakes: List[str], approaches: List[str], seeds: List[str]) -> str:
        """Broadcast wisdom on session completion."""
        return self.broadcast(
            msg_type=AnemoiMessageType.WISDOM_BROADCAST,
            payload={
                "extracted_patterns": patterns,
                "avoided_mistakes": mistakes,
                "recommended_approaches": approaches,
                "seeds_for_next": seeds
            }
        )
    
    def close_session(self) -> None:
        """Close session and notify others."""
        self.broadcast(
            msg_type=AnemoiMessageType.SESSION_CLOSING,
            payload={"final_status": "completed", "closed_at": datetime.utcnow().isoformat() + "Z"}
        )
        registry = self._load_registry()
        if self.session_id in registry:
            registry[self.session_id]["status"] = "closed"
            registry[self.session_id]["closed_at"] = datetime.utcnow().isoformat() + "Z"
            self._save_registry(registry)
    
    def get_genealogy(self) -> Optional[SessionGenealogy]:
        """Get genealogy information for current session."""
        registry = self._load_registry()
        if self.session_id not in registry:
            return None
        info = registry[self.session_id]
        return SessionGenealogy(
            session_id=self.session_id,
            parent_id=info.get("parent_id"),
            children=info.get("children", []),
            spawn_reason=info.get("spawn_reason", "new"),
            spawned_at=info.get("registered_at"),
            depth=len(info.get("ancestor_chain", [])),
            ancestor_chain=info.get("ancestor_chain", [])
        )
    
    def get_continuation(self) -> Optional[ContinuationState]:
        """Get continuation state for current session."""
        return self.continuation_mgr.load_continuation(self.session_id)
    
    def create_checkpoint(self, session_state: Dict[str, Any], name: str = None) -> str:
        """Create checkpoint of current session."""
        return self.continuation_mgr.create_checkpoint(session_state, checkpoint_name=name)
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List checkpoints for current session."""
        return self.continuation_mgr.list_checkpoints(self.session_id)


# Convenience functions

def initialize_anemoi_session(session_id: str) -> AnemoiClient:
    """Initialize Anemoi client for a session and check for spawn messages."""
    client = AnemoiClient(session_id)
    spawn_msg = client.acknowledge_spawn()
    if spawn_msg:
        print(f"🔄 Inherited context from parent session {spawn_msg.sender_session_id}")
        payload = spawn_msg.payload
        inherited = list(payload.get("inherited_context", {}).keys())
        print(f"   Inherited fields: {', '.join(inherited)}")
    return client


def fork_with_anemoi(parent_session: Dict[str, Any]) -> tuple:
    """Fork session with Anemoi A2A messaging."""
    parent_id = parent_session.get("session_id", "unknown")
    parent_client = AnemoiClient(parent_id)
    child_id = parent_client.fork_session(parent_session)
    print(f"🍴 Forked session {parent_id} → {child_id}")
    return child_id, parent_client
