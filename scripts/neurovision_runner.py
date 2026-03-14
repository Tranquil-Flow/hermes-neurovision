#!/Users/evinova/.hermes/hermes-agent/venv/bin/python3
"""
neurovision_runner.py — Autonomous task executor for hermes-neurovision.

Uses hermes-agent's AIAgent with local qwen3:30b (Ollama) to:
  1. Read TASKS.md and implement the next unchecked task
  2. When all tasks are done, create new original visual screens on a loop

Usage:
    python3 scripts/neurovision_runner.py            # run next task or create screen
    python3 scripts/neurovision_runner.py --screen   # force-create a new screen
    python3 scripts/neurovision_runner.py --loop     # keep running until killed
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
HERMES_AGENT_DIR = Path.home() / ".hermes" / "hermes-agent"
TASKS_FILE = PROJECT_DIR / "TASKS.md"

# ---------------------------------------------------------------------------
# Add hermes-agent to Python path (required to import run_agent).
# This script runs under the hermes venv Python (see shebang), so all
# hermes dependencies (openai, pydantic, etc.) are already available.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(HERMES_AGENT_DIR))
sys.path.insert(0, str(HERMES_AGENT_DIR / "cron"))

# ---------------------------------------------------------------------------
# Force local terminal backend — avoids Docker overhead, runs commands
# directly in the project directory.
# ---------------------------------------------------------------------------
os.environ["TERMINAL_ENV"] = "local"
os.environ["TERMINAL_CWD"] = str(PROJECT_DIR)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [neurovision-runner] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("neurovision-runner")

# ---------------------------------------------------------------------------
# Model config (local Ollama — no API key needed)
# ---------------------------------------------------------------------------
MODEL = "qwen3:30b"
BASE_URL = "http://localhost:11434/v1"
API_KEY = "ollama"

# ---------------------------------------------------------------------------
# System prompt — project context injected into every agent conversation
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are an expert Python developer implementing features for hermes-neurovision,
a terminal ASCII art visualizer that reacts to AI agent events.

PROJECT DIRECTORY: {PROJECT_DIR}
TECH STACK: Python 3.10+ stdlib only (curses, math, random, json, sqlite3) — no external pip packages.

=== KEY ARCHITECTURE PATTERNS ===

Full-screen ASCII themes (the new style):
  - ThemePlugin subclass with build_nodes() returning [] to suppress graph
  - draw_extras(stdscr, state, color_pairs) renders the full ASCII field
  - Per-cell rendering: try: stdscr.addstr(y, x, char, color_pair) except curses.error: pass
  - Register at module bottom: register(MyPlugin())
  - state.width, state.height give terminal dimensions
  - state.frame increments each tick (20fps)
  - Use state.rng for reproducible randomness

Colors in draw_extras:
  cp = color_pairs.get(('key_a', 'key_b'))
  if cp: stdscr.addstr(y, x, char, cp)
  Available color key pairs are theme-defined in ThemeConfig.

Theme plugin file location: hermes_neurovision/theme_plugins/
Theme registry: hermes_neurovision/themes.py (THEMES tuple + build_theme_config)
Plugin loader: hermes_neurovision/theme_plugins/__init__.py (add import in _load_all)
Full-screen themes set: tests/test_themes.py (full_screen_themes set)

=== WORKFLOW — ALWAYS follow this order ===

1. Read TASKS.md to understand the full task spec
2. Read relevant existing files to understand patterns (BEFORE writing any code)
3. Write tests first (TDD)
4. Implement the feature
5. Run: cd {PROJECT_DIR} && python -m pytest tests/ -v 2>&1 | tail -30
6. Fix ALL failures before committing
7. Commit with: cd {PROJECT_DIR} && git add <specific files> && git commit -m "feat: ..."
8. Mark the task done by checking it off in TASKS.md: sed -i '' 's/- \\[ \\] Task N:/- [x] Task N:/' TASKS.md

=== CONSTRAINTS ===
- Pure stdlib only — no pip install
- Each plugin file must be independently understandable
- Always run tests and fix failures before committing
- Commit after EACH completed task, not in batches
- Use descriptive commit messages (what + why)
"""

# ---------------------------------------------------------------------------
# Task parsing
# ---------------------------------------------------------------------------

def get_unchecked_tasks() -> list[str]:
    """Return list of unchecked task descriptions from TASKS.md."""
    if not TASKS_FILE.exists():
        return []
    content = TASKS_FILE.read_text()
    # Match "- [ ] Task N: ..." blocks (multi-line, up to next task/header/EOF)
    pattern = r"^- \[ \] (Task \d+:.*?)(?=\n- \[|\n##|\n---|\Z)"
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
    return [m.strip() for m in matches]


def get_next_task() -> str | None:
    tasks = get_unchecked_tasks()
    return tasks[0] if tasks else None


# ---------------------------------------------------------------------------
# AIAgent runner
# ---------------------------------------------------------------------------

def make_agent(session_suffix: str = "task"):
    """Create AIAgent with qwen3:30b via local Ollama."""
    from run_agent import AIAgent  # imported here so path is set up first

    return AIAgent(
        model=MODEL,
        base_url=BASE_URL,
        api_key=API_KEY,
        max_iterations=80,
        quiet_mode=False,
        skip_memory=True,  # don't pollute hermes memory with task runs
        session_id=f"neurovision_{session_suffix}",
    )


def run_task(task_description: str) -> str:
    """Implement a TASKS.md task using qwen3:30b."""
    log.info("Starting task: %s", task_description[:80])
    agent = make_agent("task")
    prompt = f"""Implement this task from the hermes-neurovision TASKS.md:

{task_description}

Start by reading TASKS.md and the relevant existing source files to understand context.
Then implement, test (python -m pytest tests/ -v), fix any failures, and commit.
Finally, mark the task complete in TASKS.md by changing "- [ ]" to "- [x]" for this task.
"""
    result = agent.run_conversation(prompt, system_message=SYSTEM_PROMPT)
    return result.get("final_response", "(no response)")


def run_creative_screen() -> str:
    """Create a new original ASCII theme when all tasks are done."""
    log.info("All tasks complete — creating new creative screen...")
    agent = make_agent("creative")

    # Read existing theme names to avoid duplicates
    existing = ""
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "-c",
             "from hermes_neurovision.themes import THEMES; print('\\n'.join(THEMES))"],
            capture_output=True, text=True, cwd=str(PROJECT_DIR)
        )
        existing = result.stdout.strip()
    except Exception:
        pass

    prompt = f"""Create a completely new, original ASCII art theme for hermes-neurovision.

Existing themes (do NOT duplicate):
{existing}

Instructions:
1. Read CLAUDE.md for project constraints
2. Read hermes_neurovision/theme_plugins/experimental.py for the full-screen ASCII pattern
3. Read hermes_neurovision/theme_plugins/originals_v2.py for more examples
4. Design a UNIQUE, visually interesting ASCII visualization — something not already in the list above
5. Ideas to consider (pick something fresh and ambitious):
   - Strange attractors (Thomas, Dadras, Halvorsen, etc.)
   - Reaction-diffusion systems (Turing patterns, Gray-Scott)
   - Voronoi diagrams with animated seeds
   - Conway's Game of Life variants (Brian's Brain, Seeds, Day & Night)
   - Fractal Julia sets with animated parameter sweep
   - Fluid simulation (SPH or Eulerian)
   - Perlin-noise terrain flyover
   - Lenia (continuous cellular automaton)
   - Boids flocking with ASCII trails
   - Wave function collapse patterns
   - Chladni figures (vibration mode patterns)
   - Ising model (magnetic spin simulation)
6. Implement it as a full-screen ASCII theme plugin
7. Add to themes.py THEMES tuple and build_theme_config()
8. Add to theme_plugins/__init__.py _load_all()
9. Add to tests/test_themes.py full_screen_themes set
10. Run tests, fix failures, commit

Be ambitious and mathematically interesting. The best themes are visually stunning.
"""
    result = agent.run_conversation(prompt, system_message=SYSTEM_PROMPT)
    return result.get("final_response", "(no response)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="hermes-neurovision autonomous task runner")
    parser.add_argument("--screen", action="store_true",
                        help="Force-create a new creative screen (skip task queue)")
    parser.add_argument("--loop", action="store_true",
                        help="Keep running after each task/screen until killed")
    args = parser.parse_args()

    iteration = 0
    while True:
        iteration += 1
        log.info("=== Iteration %d ===", iteration)

        if args.screen:
            run_creative_screen()
        else:
            task = get_next_task()
            if task:
                run_task(task)
            else:
                log.info("No unchecked tasks found — switching to creative screen mode")
                run_creative_screen()

        if not args.loop:
            break

        log.info("Loop mode: sleeping 60s before next iteration...")
        import time
        time.sleep(60)


if __name__ == "__main__":
    main()
