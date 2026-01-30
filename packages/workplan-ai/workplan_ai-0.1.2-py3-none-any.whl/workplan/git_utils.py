import subprocess
import re
from pathlib import Path
from typing import List, Set, Dict, Any
from datetime import datetime

def get_recent_commits(days: int = 7) -> List[Dict[str, Any]]:
    """Retrieves commit details (message and files) from the last N days."""
    try:
        # Get commit hashes first
        cmd = ["git", "log", f"--since={days} days ago", "--pretty=format:%H"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        hashes = result.stdout.splitlines()
        
        details = []
        for h in hashes:
            # Get message
            msg_cmd = ["git", "show", "-s", "--format=%s", h]
            msg = subprocess.run(msg_cmd, capture_output=True, text=True, check=True).stdout.strip()
            
            # Get files
            files_cmd = ["git", "show", "--name-only", "--format=", h]
            files = subprocess.run(files_cmd, capture_output=True, text=True, check=True).stdout.splitlines()
            
            details.append({
                "hash": h,
                "message": msg,
                "files": [f.strip() for f in files if f.strip()]
            })
        return details
    except subprocess.CalledProcessError:
        return []

def map_commits_to_tasks(week):
    """
    Updates task statuses based on git activity.
    Uses strict Task-ID matching (e.g., TASK-1) in commit messages.
    """
    commit_details = get_recent_commits()
    
    # Update task statuses
    for task in week.tasks:
        task_id_pattern = re.compile(rf"\b{task.task_id}\b", re.IGNORECASE)
        
        for commit in commit_details:
            # Check for TASK-ID match in message
            if task_id_pattern.search(commit["message"]):
                task.status = "done"
                
                # Link commit hash if not already present
                if commit["hash"] not in task.execution.commits:
                    task.execution.commits.append(commit["hash"])
                
                # Link files changed in this specific commit
                for file in commit["files"]:
                    if file not in task.execution.linked_files:
                        task.execution.linked_files.append(file)
                
                # Update timestamps
                now = datetime.now()
                if not task.execution.first_seen:
                    task.execution.first_seen = now
                task.execution.last_updated = now
    
    return week
