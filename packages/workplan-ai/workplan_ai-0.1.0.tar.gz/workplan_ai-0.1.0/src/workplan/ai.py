import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from groq import Groq
from .storage import get_api_key

class WorkplanAIClient:
    def __init__(self):
        self.api_key = get_api_key()
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-maverick-17b-128e-instruct")

    def generate_plan(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes the 9-stage planning logic to generate a structured weekly plan.
        """
        if not self.client:
            raise ValueError("Groq API key not found. Please run `workplan init`.")

        system_prompt = f"""
You are a Senior Software Engineer and Delivery Manager. Your goal is to take a one-line goal and expand it into a professional weekly plan.
Follow these 9 stages of expansion:
1. Intent Expansion: Understand the goal's domain and scope.
2. Context Grounding: Use the provided project context (files, language).
3. Outcome Definition: Define what "Done" looks like for the end of the week.
4. Vertical Decomposition: Break outcomes into independently shippable vertical units.
5. Risk Detection: Identify hidden dependencies or blockers.
6. Estimation: Assign realistic complexity (Story Points).
7. Capacity Check: Ensure the total load fits a single developer's week.
8. Self-Critique: Review and refine the plan for quality and feasibility.
9. Structured Output: Return the final plan as a JSON object.

CONTEXT:
Project Name: {context.get('project_name')}
Architecture/Structure: {context.get('structure')}
Dependencies: {context.get('dependencies')}
Recent Git Activity: {context.get('git_history')}
Files: {context.get('files')}
README Context: {context.get('readme')}

GOAL: {goal}

CODEBASE-AWARE REASONING:
1.  **Strict Grounding**: Utilize the provided Architecture and Files. Reference specific paths.
2.  **Incremental Planning**: Assume the current code is the foundation. Do NOT re-implement existing systems.

VERTICAL SLICING (SENIOR LEVEL):
1.  **NO STANDALONE LAYERS**: You are strictly FORBIDDEN from generating standalone tasks for: "Testing", "Validation", "Styling", "CSS", "UI Polishing", or "Responsive Design". 
2.  **MANDATORY BUNDLING**: These must be BUNDLED into the feature task. (e.g., "Implement Hero Section with full responsive styling and unit tests").
3.  **FILE EXISTENCE VALIDATION**: You MUST only reference files that exist in the provided FILES or STRUCTURE context. Do NOT hallucinate file paths.
    - *Bad*: "Update `src/api/auth.py`" (if auth.py doesn't exist in context)
    - *Good*: "Create `src/api/auth.py` for authentication logic"
4.  **MANDATE FEATURE TITLES**: Every task title must be a standalone technical outcome.
    - *Bad*: "Landing Page Responsive Styling"
    - *Good*: "Hero & Features Responsive UI in `src/pages/index.tsx`"
4.  **HIGH-DENSITY DESCRIPTIONS**: The description MUST specify the technical approach, the specific files modified, and include: "This task includes unit testing and responsive styling."
5.  **Evidence of Done**: Every task description must end with "The tangible deliverable is [specific file change or system state]."

INTERNAL SCHEMA KNOWLEDGE:
- Tasks follow this structure: {{"task_id": "TASK-N", "title": "...", "description": "...", "status": "todo", "points": integer, "points_reasoning": "Brief explanation of effort/complexity justifying the points", "risk": boolean}}
- **DECISION DENSITY & NAMING**: 
    - **BAN** ceremonial words: "Research", "Review", "Define", "Requirements", "Study", "Analyze".
    - **MANDATE** decision-focused verbs: "Align", "Lock", "Finalize", "Confirm", "Prototype", "Implement".
    - Example: Instead of "Define Requirements", use "Align on Data Schema".
- **CORPORATE 6-DAY RHYTHM**:
    - **6-DAY WEEK**: Generate a plan for a 6-day work week. 
    - **DAILY DENSITY**: 1-2 tasks per day (Total range: 8-12 tasks).
    - **CAPACITY**: The total points across all tasks **MUST** be between 15 and 20.
- **PROPORTIONAL POINTS**: 
    - **MANDATORY**: Each task must use a different point value (1, 3, 5, 8). 
    - Setup/Config = 1. Core Logic = 5 or 8.
    - **CRITICAL**: Do NOT assign the same point value to all tasks.
- **HIGH-SIGNAL, LOW-CEREMONY**:
    - **NO STANDALONE ALIGNMENT**: Vague "Align", "Lock", or "Confirm" tasks must be **DELETED**. 
    - **EMBED DECISIONS**: Include any necessary alignment/decisions as the *first sentence* of the relevant implementation task's description.
    - **VERTICAL SLICES**: Every task must be a vertical slice (Code, Tests, or Config).
- **MANAGER-FRIENDLY DESCRIPTIONS**: Every "description" field must be 2-3 sentences long. It must explain **what** is being done, **why** it matters for the week's goal, and what the **tangible deliverable** is. Avoid technical jargon.
- **LEARNING SPIKES & RISK**:
    - Identify technologies in the GOAL not present in the CONTEXT.
    - Categorize initial engagement with new tech as a "Learning Spike" or "Rapid Discovery".
    - **ELEVATE RISK**: Set `risk: true` for any task involving a learning spike or high-uncertainty integration.
- **SCALE CLASSIFICATION**:
    - **Small Goals (1-2 days)**: Penalize ceremonial planning. Planning tasks must be <5% of total effort and renamed as rapid decisions. Transition to vertical slices immediately.
    - **Large Goals**: Justify lightweight design tasks ONLY if they reduce measurable risk.
- **OUTCOME-DRIVEN FOCUS**: Every task must be a vertical slice (Code, Tests, or Config). 

OUTPUT FORMAT:
Return ONLY a JSON object with a key "tasks" containing a list of task objects.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
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
        """
        Generates a professional daily summary based on Git commits.
        """
        if not self.client:
            raise ValueError("Groq API key not found. Please run `workplan init`.")

        messages_text = "\n".join([f"- {c['message']}" for c in commits])
        system_prompt = f"""
You are a senior engineering manager summarizing a developer's day.
The update should be concise, highlight the main accomplishments, and relate them back to the weekly goal.

WEEKLY GOAL: {goal}
ACTIVITY (RECENT COMMITS):
{messages_text}

OUTPUT FORMAT:
Return a short, impactful paragraph or a small set of bullet points. Avoid preamble.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Summarize my day."}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating EOD summary: {str(e)}"

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
