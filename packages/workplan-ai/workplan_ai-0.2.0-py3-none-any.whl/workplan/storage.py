import json
import os
import keyring
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import date, datetime

SERVICE_NAME = "workplan-ai"
API_KEY_NAME = "groq-api-key"
WORKPLAN_DIR = ".workplan"
GLOBAL_ROOT = Path.home() / ".workplan-ai"

# --- Models ---

class ProjectRegistry(BaseModel):
    project_paths: List[str] = Field(default_factory=list)

class ProjectConfig(BaseModel):
    process_type: str = "scrum"
    estimation_mode: str = "story_points"
    capacity_limit: int = 20
    intelligence_mode: str = "local"

class ProjectState(BaseModel):
    project_id: str
    project_name: str
    repo_path: str
    created_at: date = Field(default_factory=date.today)
    config: ProjectConfig = Field(default_factory=ProjectConfig)

class TaskEstimation(BaseModel):
    mode: str = "story_points"
    points: int = 1
    confidence: float = 1.0
    points_reasoning: str = "Initial estimate"

class TaskExecution(BaseModel):
    linked_files: List[str] = Field(default_factory=list)
    commits: List[str] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    actual_days: int = 0

class TaskSignals(BaseModel):
    dependency: bool = False
    risk: bool = False
    carryover: bool = False
    carryover_reason: Optional[str] = None

class Microtask(BaseModel):
    id: str  # e.g. "MT-1"
    title: str
    status: str = "todo"

class Task(BaseModel):
    task_id: str
    title: str
    description: str = ""
    status: str = "todo"  # todo, in_progress, done, blocked
    microtasks: List[Microtask] = Field(default_factory=list)
    estimation: TaskEstimation = Field(default_factory=TaskEstimation)
    execution: TaskExecution = Field(default_factory=TaskExecution)
    signals: TaskSignals = Field(default_factory=TaskSignals)

class WeekMetrics(BaseModel):
    planned_points: int = 0
    completed_points: int = 0
    unplanned_work_ratio: float = 0.0
    focus_score: float = 1.0

class WeekState(BaseModel):
    week_id: str
    goal: str
    start_date: date
    end_date: date
    tasks: List[Task] = Field(default_factory=list)
    metrics: WeekMetrics = Field(default_factory=WeekMetrics)

class HistoryWeek(BaseModel):
    week_id: str
    planned_points: int
    completed_points: int
    carryover_tasks: int
    unplanned_ratio: float
    outcome: str  # partial, complete, failed

class HistoryState(BaseModel):
    weeks: List[HistoryWeek] = Field(default_factory=list)

class UsageState(BaseModel):
    usage_date: date = Field(default_factory=date.today)
    eod_count: int = 0
    plan: str = "free"

class IntelligenceSignals(BaseModel):
    capacity_overload: bool = False
    estimation_bias: str = "none" # overestimate, underestimate, none
    process_mismatch: bool = False

class IntelligenceState(BaseModel):
    planner_version: str = "v1.0"
    last_reasoning_at: Optional[datetime] = None
    signals: IntelligenceSignals = Field(default_factory=IntelligenceSignals)

# --- Storage Logic ---

def get_workplan_path() -> Path:
    return Path.cwd() / WORKPLAN_DIR

def get_file_path(filename: str) -> Path:
    return get_workplan_path() / filename

def init_storage():
    """Initializes the .workplan directory."""
    path = get_workplan_path()
    if not path.exists():
        path.mkdir(parents=True)
    
    # Register project globally
    register_project(Path.cwd())
    
    # Initialize basic project.json if it doesn't exist
    project_file = get_file_path("project.json")
    if not project_file.exists():
        cwd = Path.cwd()
        project = ProjectState(
            project_id=cwd.name.lower().replace(" ", "-"),
            project_name=cwd.name,
            repo_path=str(cwd)
        )
        save_project(project)

def load_json(filename: str, model_class):
    path = get_file_path(filename)
    if not path.exists():
        return None
    with open(path, "r") as f:
        data = json.load(f)
        return model_class(**data)

def save_json(filename: str, model_instance):
    path = get_file_path(filename)
    with open(path, "w") as f:
        # custom_encoder for date/datetime
        def default_serializer(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        json.dump(model_instance.dict(), f, indent=2, default=default_serializer)

# Specialized helpers
def load_project() -> Optional[ProjectState]: return load_json("project.json", ProjectState)
def save_project(state: ProjectState): save_json("project.json", state)

def load_week() -> Optional[WeekState]: return load_json("week.json", WeekState)
def save_week(state: WeekState): save_json("week.json", state)

def load_history() -> HistoryState: 
    return load_json("history.json", HistoryState) or HistoryState()
def save_history(state: HistoryState): save_json("history.json", state)

def load_usage() -> UsageState:
    return load_json("usage.json", UsageState) or UsageState()
def save_usage(state: UsageState): save_json("usage.json", state)

def load_intelligence() -> IntelligenceState:
    return load_json("intelligence.json", IntelligenceState) or IntelligenceState()
def save_intelligence(state: IntelligenceState): save_json("intelligence.json", state)

def set_api_key(api_key: str):
    keyring.set_password(SERVICE_NAME, API_KEY_NAME, api_key)

def get_api_key() -> Optional[str]:
    return keyring.get_password(SERVICE_NAME, API_KEY_NAME)

# --- Global Registry Logic ---
def load_registry() -> ProjectRegistry:
    reg_path = GLOBAL_ROOT / "registry.json"
    if not reg_path.exists():
        return ProjectRegistry()
    with open(reg_path, "r") as f:
        return ProjectRegistry(**json.load(f))

def save_registry(reg: ProjectRegistry):
    if not GLOBAL_ROOT.exists():
        GLOBAL_ROOT.mkdir(parents=True)
    reg_path = GLOBAL_ROOT / "registry.json"
    with open(reg_path, "w") as f:
        json.dump(reg.dict(), f, indent=2)

def register_project(path: Path):
    reg = load_registry()
    path_str = str(path.absolute())
    if path_str not in reg.project_paths:
        reg.project_paths.append(path_str)
        save_registry(reg)
