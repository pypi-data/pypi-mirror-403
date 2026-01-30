import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from groq import Groq
from .storage import get_api_key
from .prompts import get_planning_prompt, get_eod_summary_prompt, get_decomposition_prompt

class WorkplanAIClient:
    def __init__(self):
        self.api_key = get_api_key()
        if not self.api_key:
            raise ValueError("Groq API key not found. Run `workplan init` first.")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    def generate_plan(self, goal: str, context: Dict[str, Any]) -> List[Dict]:
        """Generates a weekly plan using the 9-stage expansion process."""
        prompt = get_planning_prompt(context, goal)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Generate a weekly plan for the goal: {goal}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            # Handle possible variations in JSON structure (e.g., {"tasks": [...]})
            if "tasks" in data:
                return data["tasks"]
            return data if isinstance(data, list) else []
        except Exception as e:
            # Fallback to a basic structure if AI fails
            return [{"title": f"Error: {str(e)}", "description": "Failed to generate tasks.", "status": "todo"}]

    def generate_eod_summary(self, commits: List[str], goal: str) -> str:
        """Generates a professional daily summary based on Git commits."""
        messages_text = [c['message'] for c in commits]
        prompt = get_eod_summary_prompt(messages_text, goal)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Generate the end-of-day summary."}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Unable to generate summary: {str(e)}"

    def decompose_task(self, task_title: str, task_description: str, context: Dict[str, Any]) -> List[Dict]:
        """Decomposes a task into daily microtasks."""
        prompt = get_decomposition_prompt(task_title, task_description, context)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Decompose the task: {task_title}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("microtasks", [])
        except Exception as e:
            return []

def get_project_context() -> Dict[str, Any]:
    """Gathers local project context, including structure, README, and dependencies."""
    cwd = Path.cwd()
    
    # 1. Top-level files
    files = [f.name for f in cwd.iterdir() if f.is_file() and not f.name.startswith('.')]
    
    # 2. Directory structure (Depth 1-2)
    structure = []
    for d in cwd.iterdir():
        if d.is_dir() and not d.name.startswith('.') and d.name != "__pycache__":
            structure.append(d.name)
            try:
                subs = [s.name for s in d.iterdir() if s.is_dir() and not s.name.startswith('.')]
                if subs:
                    structure.append(f"  └─ {', '.join(subs[:5])}")
            except PermissionError:
                pass

    # 3. Read README content (first 1000 chars)
    readme_content = ""
    for r in ["README.md", "README", "readme.md"]:
        r_path = cwd / r
        if r_path.exists():
            try:
                readme_content = r_path.read_text()[:1000]
                break
            except Exception:
                pass

    # 4. Dependency Analysis (PyPI/NPM/etc.)
    dependencies = []
    # Python - pyproject.toml
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            # Extract dependencies section roughly without full toml parser
            if "dependencies =" in content:
                deps_section = content.split("dependencies =")[1].split("]")[0]
                dependencies.extend([d.strip().strip('"').strip("'") for d in deps_section.split("\n") if d.strip()])
        except Exception:
            pass

    # Python - requirements.txt
    requirements = cwd / "requirements.txt"
    if requirements.exists():
        try:
            dependencies.extend([line.split("==")[0].strip() for line in requirements.read_text().splitlines() if line.strip() and not line.startswith("#")])
        except Exception:
            pass

    # JS/TS - package.json
    package_json = cwd / "package.json"
    if package_json.exists():
        try:
            # Quick check for major dependencies
            content = package_json.read_text()
            if "dependencies" in content:
                dependencies.append("Node.js/NPM project detected")
        except Exception:
            pass

    # 5. Git History (Last 10 commits for momentum context)
    git_history = []
    try:
        cmd = ["git", "log", "-n", "10", "--pretty=format:%h: %s"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            git_history = result.stdout.splitlines()
    except Exception:
        pass

    return {
        "project_name": cwd.name,
        "files": files[:15],
        "structure": structure[:20],
        "readme": readme_content,
        "dependencies": list(set(dependencies))[:30],
        "git_history": git_history
    }
