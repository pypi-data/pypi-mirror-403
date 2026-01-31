"""
SimExp Continuation State Module
Agent Continuations for session context inheritance (Phase 1)

Implements JSON state blob transfer between parent and child sessions,
enabling zero-latency context transfer on fork/resume operations.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal


@dataclass
class AssumptionRecord:
    """Validated assumption with confidence and source."""
    assumption: str
    confidence: Literal["low", "medium", "high", "validated"]
    source: str  # "user", "inferred", "inherited", "tested"
    validated_at: Optional[str] = None
    parent_session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssumptionRecord":
        return cls(**data)


@dataclass
class EastContinuation:
    """Vision and intention state to inherit."""
    vision_statement: Optional[str] = None
    goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EastContinuation":
        return cls(**data) if data else cls()


@dataclass  
class SouthContinuation:
    """Growth progress to inherit."""
    files_modified: List[str] = field(default_factory=list)
    tests_added: List[str] = field(default_factory=list)
    content_written_count: int = 0
    incomplete_tasks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SouthContinuation":
        return cls(**data) if data else cls()


@dataclass
class WestContinuation:
    """Sharing state to inherit."""
    published_to: List[str] = field(default_factory=list)
    pending_shares: List[str] = field(default_factory=list)
    collaborators_notified: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WestContinuation":
        return cls(**data) if data else cls()


@dataclass
class NorthContinuation:
    """Reflection wisdom to inherit."""
    extracted_patterns: List[str] = field(default_factory=list)
    avoided_mistakes: List[str] = field(default_factory=list)
    recommended_approaches: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NorthContinuation":
        return cls(**data) if data else cls()


@dataclass
class ContinuationState:
    """Complete transferable state for session continuity."""
    
    # Identity
    session_id: str
    parent_session_id: Optional[str] = None
    spawn_reason: Literal["new", "fork", "resume", "checkpoint"] = "new"
    
    # Core Context
    ai_assistant: str = "claude"
    model: str = "sonnet"
    working_directory: Optional[str] = None
    
    # Task Context
    issue_number: Optional[int] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    
    # Four Directions State
    east: EastContinuation = field(default_factory=EastContinuation)
    south: SouthContinuation = field(default_factory=SouthContinuation)
    west: WestContinuation = field(default_factory=WestContinuation)
    north: NorthContinuation = field(default_factory=NorthContinuation)
    
    # Accumulated Wisdom
    assumptions: List[AssumptionRecord] = field(default_factory=list)
    learnings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Genealogy
    genealogy_depth: int = 0
    ancestor_chain: List[str] = field(default_factory=list)
    
    # Trace Linking
    parent_trace_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "session_id": self.session_id,
            "parent_session_id": self.parent_session_id,
            "spawn_reason": self.spawn_reason,
            "ai_assistant": self.ai_assistant,
            "model": self.model,
            "working_directory": self.working_directory,
            "issue_number": self.issue_number,
            "repository": self.repository,
            "branch": self.branch,
            "east": self.east.to_dict(),
            "south": self.south.to_dict(),
            "west": self.west.to_dict(),
            "north": self.north.to_dict(),
            "assumptions": [a.to_dict() if hasattr(a, 'to_dict') else a for a in self.assumptions],
            "learnings": self.learnings,
            "warnings": self.warnings,
            "genealogy_depth": self.genealogy_depth,
            "ancestor_chain": self.ancestor_chain,
            "parent_trace_id": self.parent_trace_id,
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContinuationState":
        """Create from dictionary."""
        assumptions = [
            AssumptionRecord.from_dict(a) if isinstance(a, dict) else a
            for a in data.get("assumptions", [])
        ]
        
        return cls(
            session_id=data["session_id"],
            parent_session_id=data.get("parent_session_id"),
            spawn_reason=data.get("spawn_reason", "new"),
            ai_assistant=data.get("ai_assistant", "claude"),
            model=data.get("model", "sonnet"),
            working_directory=data.get("working_directory"),
            issue_number=data.get("issue_number"),
            repository=data.get("repository"),
            branch=data.get("branch"),
            east=EastContinuation.from_dict(data.get("east", {})),
            south=SouthContinuation.from_dict(data.get("south", {})),
            west=WestContinuation.from_dict(data.get("west", {})),
            north=NorthContinuation.from_dict(data.get("north", {})),
            assumptions=assumptions,
            learnings=data.get("learnings", []),
            warnings=data.get("warnings", []),
            genealogy_depth=data.get("genealogy_depth", 0),
            ancestor_chain=data.get("ancestor_chain", []),
            parent_trace_id=data.get("parent_trace_id"),
            checkpoint_id=data.get("checkpoint_id"),
            created_at=data.get("created_at", datetime.utcnow().isoformat() + "Z"),
            version=data.get("version", "1.0")
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ContinuationState":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def get_inherited_context(self) -> Dict[str, Any]:
        """Extract context for inheritance to child sessions."""
        return {
            "ai_assistant": self.ai_assistant,
            "model": self.model,
            "working_directory": self.working_directory,
            "issue_number": self.issue_number,
            "repository": self.repository,
            "branch": self.branch
        }


class ContinuationManager:
    """Manages continuation state for sessions."""
    
    CONTINUATIONS_DIR = "continuations"
    CHECKPOINTS_DIR = "checkpoints"
    
    def __init__(self, base_path: str = None):
        """
        Initialize ContinuationManager.
        
        Args:
            base_path: Base path for continuation storage. 
                       Defaults to ~/.simexp
        """
        if base_path:
            self.base_path = Path(base_path).expanduser()
        else:
            self.base_path = Path.home() / ".simexp"
        
        self.continuations_dir = self.base_path / self.CONTINUATIONS_DIR
        self.checkpoints_dir = self.continuations_dir / self.CHECKPOINTS_DIR
        
        # Ensure directories exist
        self.continuations_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
    
    def save_continuation(self, 
                          state: ContinuationState,
                          is_checkpoint: bool = False) -> str:
        """
        Save continuation state.
        
        Args:
            state: ContinuationState to save
            is_checkpoint: If True, save to checkpoints directory
            
        Returns:
            Path to saved file
        """
        if is_checkpoint:
            checkpoint_id = f"{state.session_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            state.checkpoint_id = checkpoint_id
            file_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        else:
            file_path = self.continuations_dir / f"{state.session_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)
        
        # Update latest symlink
        latest_link = self.continuations_dir / "latest.json"
        if latest_link.is_symlink():
            latest_link.unlink()
        elif latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(file_path.name)
        
        return str(file_path)
    
    def load_continuation(self, 
                          session_id: str,
                          checkpoint_id: Optional[str] = None) -> Optional[ContinuationState]:
        """
        Load continuation state for session.
        
        Args:
            session_id: Session ID to load
            checkpoint_id: Optional checkpoint ID to load specific checkpoint
            
        Returns:
            ContinuationState or None if not found
        """
        if checkpoint_id:
            file_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        else:
            file_path = self.continuations_dir / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return ContinuationState.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Failed to load continuation: {e}")
            return None
    
    def load_latest(self) -> Optional[ContinuationState]:
        """Load the most recently saved continuation."""
        latest_link = self.continuations_dir / "latest.json"
        
        if not latest_link.exists():
            return None
        
        try:
            # Resolve symlink
            actual_path = latest_link.resolve()
            with open(actual_path, 'r') as f:
                data = json.load(f)
            return ContinuationState.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Failed to load latest continuation: {e}")
            return None
    
    def fork_continuation(self,
                          parent_state: Dict[str, Any],
                          child_session_id: str,
                          inherit_fields: Optional[List[str]] = None) -> ContinuationState:
        """
        Create child continuation from parent session state.
        
        Args:
            parent_state: Parent session dictionary (from session.json)
            child_session_id: New child session ID
            inherit_fields: Optional list of fields to inherit (default: all)
            
        Returns:
            New ContinuationState for child session
        """
        parent_session_id = parent_state.get("session_id", "unknown")
        
        # Build ancestor chain
        parent_ancestors = parent_state.get("ancestor_chain", [])
        ancestor_chain = parent_ancestors + [parent_session_id]
        
        # Extract assumptions to propagate
        parent_assumptions = parent_state.get("assumptions", [])
        propagated_assumptions = self._propagate_assumptions(
            parent_assumptions, 
            parent_session_id
        )
        
        # Create child continuation
        child = ContinuationState(
            session_id=child_session_id,
            parent_session_id=parent_session_id,
            spawn_reason="fork",
            ai_assistant=parent_state.get("ai_assistant", "claude"),
            model=parent_state.get("model", "sonnet"),
            working_directory=parent_state.get("working_directory") or os.getcwd(),
            issue_number=parent_state.get("issue_number"),
            repository=parent_state.get("repository"),
            branch=parent_state.get("branch"),
            genealogy_depth=parent_state.get("genealogy_depth", 0) + 1,
            ancestor_chain=ancestor_chain,
            parent_trace_id=parent_state.get("trace_id"),
            assumptions=propagated_assumptions
        )
        
        # Inherit Four Directions state
        if not inherit_fields or "east" in inherit_fields:
            east_data = parent_state.get("east", {})
            child.east = EastContinuation(
                vision_statement=east_data.get("vision_statement"),
                goals=east_data.get("goals", []).copy()
            )
        
        if not inherit_fields or "south" in inherit_fields:
            south_data = parent_state.get("south", {})
            child.south = SouthContinuation(
                files_modified=south_data.get("files_added", []).copy(),
                content_written_count=len(south_data.get("content_written", []))
            )
        
        if not inherit_fields or "north" in inherit_fields:
            north_data = parent_state.get("north", {})
            child.north = NorthContinuation(
                extracted_patterns=north_data.get("observed_patterns", []).copy(),
                recommended_approaches=north_data.get("extracted_wisdom", []).copy()
            )
        
        return child
    
    def _propagate_assumptions(self, 
                               parent_assumptions: List[Dict[str, Any]], 
                               parent_session_id: str) -> List[AssumptionRecord]:
        """Propagate high-confidence assumptions to child."""
        propagated = []
        
        for assumption in parent_assumptions:
            confidence = assumption.get("confidence", "low")
            if confidence in ["high", "validated"]:
                propagated.append(AssumptionRecord(
                    assumption=assumption.get("assumption", ""),
                    confidence=confidence,
                    source="inherited",
                    parent_session_id=parent_session_id
                ))
        
        return propagated
    
    def create_checkpoint(self,
                          session_state: Dict[str, Any],
                          checkpoint_name: Optional[str] = None) -> str:
        """
        Save checkpoint for current session.
        
        Args:
            session_state: Current session dictionary
            checkpoint_name: Optional name for checkpoint
            
        Returns:
            Checkpoint ID
        """
        session_id = session_state.get("session_id", "unknown")
        
        # Convert session state to continuation
        continuation = self.fork_continuation(
            parent_state=session_state,
            child_session_id=session_id,
            inherit_fields=None  # All fields
        )
        continuation.spawn_reason = "checkpoint"
        
        # Save as checkpoint
        file_path = self.save_continuation(continuation, is_checkpoint=True)
        
        return continuation.checkpoint_id
    
    def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List available checkpoints for session.
        
        Args:
            session_id: Session ID to list checkpoints for
            
        Returns:
            List of checkpoint records with id and created_at
        """
        checkpoints = []
        
        for file_path in self.checkpoints_dir.glob(f"{session_id}_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                checkpoints.append({
                    "checkpoint_id": data.get("checkpoint_id"),
                    "created_at": data.get("created_at"),
                    "file": str(file_path)
                })
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort by created_at
        checkpoints.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return checkpoints
    
    def cleanup_old_continuations(self, max_age_days: int = 7) -> int:
        """
        Remove old continuation files.
        
        Args:
            max_age_days: Maximum age in days before cleanup
            
        Returns:
            Number of files removed
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        removed = 0
        
        for file_path in self.continuations_dir.glob("*.json"):
            if file_path.name == "latest.json":
                continue
            
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    file_path.unlink()
                    removed += 1
            except (IOError, OSError):
                continue
        
        return removed


# Convenience functions

def generate_session_id() -> str:
    """Generate a new session UUID."""
    return str(uuid.uuid4())


def fork_session_with_continuation(parent_session: Dict[str, Any]) -> tuple[str, ContinuationState]:
    """
    Fork session with full context inheritance.
    
    Args:
        parent_session: Parent session dictionary
        
    Returns:
        Tuple of (child_session_id, ContinuationState)
    """
    child_id = generate_session_id()
    manager = ContinuationManager()
    
    continuation = manager.fork_continuation(
        parent_state=parent_session,
        child_session_id=child_id
    )
    
    manager.save_continuation(continuation)
    
    return child_id, continuation


def load_session_with_continuation(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load session with any available continuation state.
    
    Args:
        session_id: Session ID to load
        
    Returns:
        Session dictionary with continuation data merged in, or None
    """
    manager = ContinuationManager()
    continuation = manager.load_continuation(session_id)
    
    if not continuation:
        return None
    
    # Convert to session dictionary format
    return {
        "session_id": continuation.session_id,
        "parent_session_id": continuation.parent_session_id,
        "spawn_reason": continuation.spawn_reason,
        "ai_assistant": continuation.ai_assistant,
        "model": continuation.model,
        "working_directory": continuation.working_directory,
        "issue_number": continuation.issue_number,
        "repository": continuation.repository,
        "branch": continuation.branch,
        "east": continuation.east.to_dict(),
        "south": continuation.south.to_dict(),
        "west": continuation.west.to_dict(),
        "north": continuation.north.to_dict(),
        "assumptions": [a.to_dict() for a in continuation.assumptions],
        "learnings": continuation.learnings,
        "warnings": continuation.warnings,
        "genealogy_depth": continuation.genealogy_depth,
        "ancestor_chain": continuation.ancestor_chain,
        "parent_trace_id": continuation.parent_trace_id,
        "created_at": continuation.created_at
    }
