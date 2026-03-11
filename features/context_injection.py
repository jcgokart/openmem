"""
Context Injection for AI
Automatically inject relevant context when AI starts
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class ContextInjector:
    """
    Context Injection for AI
    
    Features:
    - Auto-load high-priority memories on startup
    - Auto-retrieve relevant history when making decisions
    - Track memory effectiveness
    """
    
    def __init__(self, storage, project_path: str = None):
        self.storage = storage
        self.project_path = project_path or os.getcwd()
    
    def load_context_for_task(self, task_type: str, limit: int = 10) -> Dict[str, Any]:
        """Load context for a specific task type"""
        context = {
            "task_type": task_type,
            "memories": [],
            "recent_decisions": [],
            "active_todos": [],
            "tech_stack": [],
        }
        
        # Load relevant memories
        memories = self.storage.search(task_type, limit=limit)
        context["memories"] = memories
        
        # Load recent decisions
        decisions = self.storage.search("", limit=5)
        context["recent_decisions"] = [m for m in decisions if m.get("type") == "decision"]
        
        # Load active todos
        todos = self.storage.search("", limit=10)
        context["active_todos"] = [m for m in todos if m.get("type") == "todo"]
        
        # Load tech stack
        tech = self.storage.search("", limit=20)
        context["tech_stack"] = [m for m in tech if m.get("type") == "tech_stack"]
        
        return context
    
    def find_similar_decisions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar decisions from history"""
        results = self.storage.search(query, limit=limit * 2)
        
        decisions = []
        for r in results:
            if r.get("type") == "decision":
                decisions.append({
                    "content": r.get("content"),
                    "metadata": r.get("metadata", {}),
                    "created_at": r.get("created_at"),
                    "relevance": r.get("score", 0),
                })
        
        return decisions[:limit]
    
    def get_effectiveness_feedback(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Get effectiveness feedback for a memory"""
        # This would be stored in metadata
        # For now, return None
        return None
    
    def record_effectiveness(self, memory_id: int, was_useful: bool, feedback: str = None):
        """Record how effective a memory was"""
        # Update memory metadata with effectiveness
        self.storage.update_memory(memory_id, metadata={
            "effectiveness": {
                "was_useful": was_useful,
                "feedback": feedback,
                "recorded_at": datetime.now().isoformat(),
            }
        })
    
    def generate_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate a human-readable context summary"""
        summary = f"# Context for: {context['task_type']}\n\n"
        
        if context["tech_stack"]:
            summary += "## Tech Stack\n"
            for tech in context["tech_stack"]:
                summary += f"- {tech['content']}\n"
            summary += "\n"
        
        if context["recent_decisions"]:
            summary += "## Recent Decisions\n"
            for decision in context["recent_decisions"]:
                summary += f"- {decision['content']}\n"
            summary += "\n"
        
        if context["active_todos"]:
            summary += "## Active TODOs\n"
            for todo in context["active_todos"]:
                summary += f"- [ ] {todo['content']}\n"
            summary += "\n"
        
        return summary
