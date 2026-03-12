"""
Trigger → Action Pipeline
Not just storing, but producing consumable results
"""

import os
from typing import Dict, List, Any, Callable
from datetime import datetime


class TriggerAction:
    """
    Trigger → Action Pipeline
    
    When a memory is added/updated, automatically trigger actions:
    - decision → generate decision.md, update IDE rules
    - todo → add to TODO.md, set reminder
    - issue → create issue.md, link to milestone
    """
    
    TRIGGER_ACTIONS: Dict[str, List[str]] = {
        "decision": ["generate_decision_md", "update_ide_rules"],
        "tech_stack": ["update_ide_rules"],
        "todo": ["add_to_todo_md"],
        "issue": ["create_issue_md"],
        "milestone": ["update_ide_rules"],
        "pattern": ["update_ide_rules"],
    }
    
    def __init__(self, storage, project_path: str = None):
        self.storage = storage
        self.project_path = project_path or os.getcwd()
        self._actions: Dict[str, Callable] = {}
        self._register_default_actions()
    
    def _register_default_actions(self):
        """Register default actions"""
        self._actions["generate_decision_md"] = self._generate_decision_md
        self._actions["update_ide_rules"] = self._update_ide_rules
        self._actions["add_to_todo_md"] = self._add_to_todo_md
        self._actions["create_issue_md"] = self._create_issue_md
    
    def register_action(self, name: str, handler: Callable):
        """Register a custom action"""
        self._actions[name] = handler
    
    def on_memory_change(self, event_type: str, memory: Dict[str, Any]):
        """Trigger actions when memory changes"""
        memory_type = memory.get("type", "")
        actions = self.TRIGGER_ACTIONS.get(memory_type, [])
        
        for action_name in actions:
            if action_name in self._actions:
                try:
                    self._actions[action_name](memory)
                except Exception as e:
                    print(f"⚠️ Action {action_name} failed: {e}")
    
    def _generate_decision_md(self, memory: Dict[str, Any]):
        """Generate decision.md file"""
        decisions_dir = os.path.join(self.project_path, "docs", "decisions")
        os.makedirs(decisions_dir, exist_ok=True)
        
        content = memory.get("content", "")
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"decision_{timestamp}.md"
        
        filepath = os.path.join(decisions_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Decision: {content[:50]}...\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Content**:\n\n{content}\n")
        
        print(f"✅ Generated: {filepath}")
    
    def _update_ide_rules(self, memory: Dict[str, Any] = None):
        """Update IDE rules files (.cursorrules, .trae/rules.md, etc.)"""
        from .ide_rules import IDERulesGenerator
        
        generator = IDERulesGenerator(self.storage, self.project_path)
        generator.update_rules()
        
        print("✅ Updated IDE rules")
    
    def _add_to_todo_md(self, memory: Dict[str, Any]):
        """Add to TODO.md file"""
        todo_file = os.path.join(self.project_path, "TODO.md")
        
        content = memory.get("content", "")
        timestamp = datetime.now().isoformat()
        
        if os.path.exists(todo_file):
            with open(todo_file, "a", encoding="utf-8") as f:
                f.write(f"\n- [ ] {content} (added {timestamp})\n")
        else:
            with open(todo_file, "w", encoding="utf-8") as f:
                f.write(f"# TODO\n\n- [ ] {content} (added {timestamp})\n")
        
        print(f"✅ Added to TODO.md: {content[:50]}...")
    
    def _create_issue_md(self, memory: Dict[str, Any]):
        """Create issue.md file"""
        issues_dir = os.path.join(self.project_path, "docs", "issues")
        os.makedirs(issues_dir, exist_ok=True)
        
        content = memory.get("content", "")
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"issue_{timestamp}.md"
        
        filepath = os.path.join(issues_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Issue: {content[:50]}...\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Description**:\n\n{content}\n\n")
            f.write(f"**Status**: Open\n")
        
        print(f"✅ Created: {filepath}")
