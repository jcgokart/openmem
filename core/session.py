"""
Session Layer for Conversation Context
Solves the problem of context inheritance in conversations
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .unified import UnifiedStorage, EventType


@dataclass
class Message:
    """A message in a session"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class Session:
    """
    Session for conversation context
    
    Features:
    - Start/end session
    - Record messages with context
    - Auto-organize on finalize
    - Track decision changes (e.g., "use JWT" -> "change to OAuth")
    """
    
    def __init__(self, storage: UnifiedStorage, project_id: str = None):
        self.storage = storage
        self.project_id = project_id
        self.session_id = None
        self._messages: List[Message] = []
        self._decisions: List[Dict[str, Any]] = []
        self._active = False
    
    def start(self) -> str:
        """Start a new session"""
        self.session_id = self.storage.start_session(self.project_id)
        self._active = True
        self._messages = []
        self._decisions = []
        return self.session_id
    
    def record(self, role: str, content: str):
        """Record a message in the session"""
        if not self._active:
            raise RuntimeError("Session not started. Call start() first.")
        
        message = Message(role=role, content=content)
        self._messages.append(message)
        
        # Add event
        self.storage.add_event(EventType.MESSAGE_RECORDED, {
            "role": role,
            "content": content
        }, self.session_id)
    
    def record_user(self, content: str):
        """Record a user message"""
        self.record("user", content)
    
    def record_assistant(self, content: str):
        """Record an assistant message"""
        self.record("assistant", content)
    
    def add_decision(self, decision: str, reason: str = None, 
                     replaces: str = None):
        """
        Add a decision
        
        Args:
            decision: The decision content
            reason: Why this decision was made
            replaces: Previous decision ID that this replaces (for tracking changes)
        """
        if not self._active:
            raise RuntimeError("Session not started. Call start() first.")
        
        decision_data = {
            "content": decision,
            "reason": reason,
            "replaces": replaces,
            "timestamp": datetime.now().isoformat()
        }
        
        self._decisions.append(decision_data)
        
        # Add to storage
        memory_id = self.storage.add_memory(
            content=decision,
            memory_type="decision",
            metadata={
                "reason": reason,
                "replaces": replaces,
                "session_id": self.session_id
            },
            session_id=self.session_id
        )
        
        decision_data["memory_id"] = memory_id
        return memory_id
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get session context
        
        Returns all messages and decisions in this session,
        with tracking of decision changes
        """
        if not self.session_id:
            return {}
        
        return self.storage.get_session_context(self.session_id)
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """
        Get decision history with change tracking
        
        Shows how decisions evolved during the session
        """
        context = self.get_context()
        memories = context.get("memories", [])
        
        decisions = [m for m in memories if m.get("type") == "decision"]
        
        # Build decision tree
        decision_map = {d.get("id"): d for d in decisions}
        
        for d in decisions:
            replaces = d.get("metadata", {}).get("replaces")
            if replaces and replaces in decision_map:
                d["replaces_decision"] = decision_map[replaces]
        
        return decisions
    
    def finalize(self, summary: str = None):
        """
        End the session and organize memories
        
        This will:
        1. Mark session as ended
        2. Store summary
        3. Trigger organize event
        """
        if not self._active:
            return
        
        # Generate summary if not provided
        if not summary:
            summary = self._generate_summary()
        
        # End session
        self.storage.end_session(self.session_id, summary)
        
        # Add organize event
        self.storage.add_event(EventType.ORGANIZE_COMPLETED, {
            "summary": summary,
            "message_count": len(self._messages),
            "decision_count": len(self._decisions)
        }, self.session_id)
        
        self._active = False
    
    def _generate_summary(self) -> str:
        """Generate a summary of the session"""
        if not self._messages:
            return ""
        
        # Simple summary: first user message
        for msg in self._messages:
            if msg.role == "user":
                return msg.content[:200]
        
        return ""
    
    def is_active(self) -> bool:
        """Check if session is active"""
        return self._active
    
    def get_messages(self) -> List[Message]:
        """Get all messages in the session"""
        return self._messages.copy()


class SessionManager:
    """
    Manager for multiple sessions
    
    Features:
    - Create and track sessions
    - Get active session
    - List all sessions
    """
    
    def __init__(self, storage: UnifiedStorage):
        self.storage = storage
        self._active_sessions: Dict[str, Session] = {}
    
    def create_session(self, project_id: str = None) -> Session:
        """Create a new session"""
        session = Session(self.storage, project_id)
        session.start()
        self._active_sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        return self._active_sessions.get(session_id)
    
    def get_active_session(self) -> Optional[Session]:
        """Get the currently active session"""
        for session in self._active_sessions.values():
            if session.is_active():
                return session
        return None
    
    def end_session(self, session_id: str, summary: str = None):
        """End a session"""
        session = self._active_sessions.get(session_id)
        if session:
            session.finalize(summary)
            del self._active_sessions[session_id]
    
    def list_sessions(self, project_id: str = None, limit: int = 10) -> List[Dict]:
        """List sessions"""
        conn = self.storage._pool.get_connection()
        cursor = conn.cursor()
        
        if project_id:
            cursor.execute("""
                SELECT id, project_id, started_at, ended_at, summary
                FROM sessions WHERE project_id = ?
                ORDER BY started_at DESC LIMIT ?
            """, (project_id, limit))
        else:
            cursor.execute("""
                SELECT id, project_id, started_at, ended_at, summary
                FROM sessions
                ORDER BY started_at DESC LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        self.storage._pool.return_connection(conn)
        
        return [{
            "id": row[0],
            "project_id": row[1],
            "started_at": row[2],
            "ended_at": row[3],
            "summary": row[4]
        } for row in rows]
