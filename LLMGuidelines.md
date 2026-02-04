# LLM Coding Guidelines for python-video Project

This document summarizes **all coding guidelines and best practices** followed during development. Future LLMs/agents **must follow these exactly** when adding, updating, or refactoring features to maintain consistency, modularity, structure, and quality. (Derived from iterative tasks on pan_zoom.py, pencil_reveal.py, utils, structure, logs, assets, outputs, etc.)

## 1. Project Structure & Organization
- **Always group by functionality** in `src/` subdirectories (e.g., `animation/`, `audio/`, `aws/`, `captions/`, `cleanup/`, `config/`, `cursor/`, `download/`, `filename/`, `image/`, `utils/`, `video/`, `cli/` for mains).
  - Add `__init__.py` to every subdir for package support.
  - Differentiate mains: CLI scripts **only** in `src/cli/` (e.g., `pan_zoom.py`, `pencil_reveal.py`).
  - Assets (images, fonts, cursors) **must** go in `src/assets/` (update all paths/references).
  - Outputs **always** to root `output/` (fix PROJECT_ROOT if subdir moves break it: `Path(__file__).parent.parent.parent` for config/config.py).
- **Move files/folders** using `run_terminal_cmd` (mkdir, mv, touch __init__.py).
- **Update ALL references** after moves: paths, imports, Readme, run*.sh, examples, usage prints.
- Keep root clean: only run*.sh, requirements.txt, Readme.md, etc.

## 2. Modularity & Code Structure
- **Extract common functionality** to `src/utils/` (e.g., error_handler.py, config_utils.py, cli_utils.py, log_utils.py, etc.).
- **Remove if-else chains** (e.g., manual arg parsing while/if-elif): Use `argparse` (full parser or shared `parse_common_options` in cli_utils).
  - Support modes (single/multi) with sub-logic or positionals/flags.
  - Handle validations post-parse (volume, paths, etc.).
- **Lazy imports** for heavy deps (inside funcs, e.g., `from ..video.video_writer import ...` only when needed).
- **Small if-else ok** if not chains (e.g., _load_cursor); prefer helpers.
- **Keep comments minimal** in changes/edits (e.g., brief "# Relative import..." or none; docstrings only for new funcs).

## 3. Error Handling & Logging
- **Use error_handler everywhere** for fatal errors: `from ..utils.error_handler import handle_error`; `handle_error("msg")` (prints "Error: ", exits).
- **Colored terminal logs** via `log_utils.py` for differentiation:
  - `log_error(msg)`: Red + exit (errors).
  - `log_warning(msg)`: Yellow (warnings).
  - `log_success(msg)`: Green (✓ success).
  - `log_info(msg)`: Default (info/cleanup).
- **Reduce log spam**: Silent downloads (no per-file "Downloaded:"), summary cleanup ("Cleaned up X files"), no unnecessary prints.
- **Update error_handler** to delegate to log_error for colors.
- **Intuitive output**: Focus on high-level progress (video creation, summaries); avoid per-item spam for multi-image.

## 4. Imports & Paths
- **Relative imports** for package (after subdir moves): `from ..config.config import ...`, `from ..utils.log_utils import ...`, `from ..download.download_utils import ...`, etc.
  - Update **everywhere** (CLI, modules, utils, video_writer, animation, etc.) after structure changes.
  - Lazy: Inside main/funcs with comment "# Relative import for grouped structure".
- **Config paths**: PROJECT_ROOT robust (`Path(__file__).parent.parent.parent`); OUTPUT_DIR/TEMP_DIR to root.
- **Assets/fonts**: Always `src/assets/...` (update caption font search, examples, run.sh, pencil cursor args).
- **No broken imports**: After any move, grep/compile all, fix relatives.

## 5. Requirements & Dependencies
- **Always verify/update requirements.txt** with **ALL** external libs (pip-installable):
  - numpy, opencv-python, pillow, requests, boto3, python-dotenv.
  - Run `grep -r "import " src/ | grep -E "(cv2|np|Image|requests|boto3|load_dotenv)"` to check.
  - No extras; stdlib (json, pathlib, argparse, sys, subprocess) omitted.
- **Venv in run scripts**: Check/install deps if missing.

## 6. General Best Practices
- **Test after changes**: `python3 -m py_compile <files>` (all affected); full run if possible.
- **CLI compatibility**: Preserve args (e.g., --multi, positionals); update usage/epilog/examples in prints/Readme.
- **No duplication**: Extract shared (parsing, config validate, logging, error).
- **Minimal comments**: Only essential (e.g., structure notes); docstrings for funcs.
- **Use tools**: search_replace for edits, run_terminal_cmd for mkdir/mv/sed, read/grep for analysis.
- **Package-aware**: Use `python -m src.cli.xxx` in scripts/Readme for -m runs/relatives.

Follow **exactly** to ensure consistency. Update this file if new practices added.
