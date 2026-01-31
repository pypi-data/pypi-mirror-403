#!/usr/bin/env python3
"""
Cowork History MCP Server

An MCP server for searching and browsing Claude conversation history with:
- SQLite + FTS5 indexing for fast full-text search
- Filesystem-based path reconstruction (not heuristic)
- Hybrid search: Spotlight (mdfind) + FTS5 + optional vector embeddings
- Incremental index updates
- Ollama setup tools for embedding generation

Usage:
    cowork-history              # Run with stdio transport
    python -m src.cowork_history_server --reindex    # Force full reindex
"""

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import struct
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# Optional httpx for async Ollama status checks
try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# =============================================================================
# Constants & Configuration
# =============================================================================

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
INDEX_DIR = CLAUDE_DIR / ".history-index"
INDEX_DB = INDEX_DIR / "conversations.db"

# Ollama configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")

# Ollama availability cache
_ollama_status_cache: dict[str, Any] = {
    "checked_at": None,
    "running": False,
    "models": [],
    "default_model_available": False,
    "ttl_seconds": 60,
}

# Minimum RAM for optimal performance
MIN_RAM_GB = 8
EMBEDDING_MODEL_RAM_GB = 2  # nomic-embed-text is small

# Initialize MCP server
mcp = FastMCP("cowork-history")


# =============================================================================
# Database Schema & Management
# =============================================================================

SCHEMA = """
-- Main conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    project_encoded TEXT NOT NULL,
    project_path TEXT,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    created_at TEXT,
    topic TEXT,
    message_count INTEGER DEFAULT 0,
    total_chars INTEGER DEFAULT 0,
    indexed_at TEXT NOT NULL
);

-- Full-text search index
CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
    session_id,
    project_path,
    topic,
    content,
    tokenize='porter unicode61'
);

-- Conversation content for FTS
CREATE TABLE IF NOT EXISTS conversation_content (
    conversation_id INTEGER PRIMARY KEY,
    full_text TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Vector embeddings (optional)
CREATE TABLE IF NOT EXISTS embeddings (
    conversation_id INTEGER PRIMARY KEY,
    embedding BLOB,
    model TEXT,
    created_at TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Path reconstruction cache
CREATE TABLE IF NOT EXISTS path_cache (
    encoded_path TEXT PRIMARY KEY,
    actual_path TEXT,
    verified_at TEXT,
    exists_on_disk INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conv_project ON conversations(project_encoded);
CREATE INDEX IF NOT EXISTS idx_conv_modified ON conversations(modified_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
"""


@contextmanager
def get_db():
    """Get database connection with proper settings."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(INDEX_DB), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


# =============================================================================
# System Requirements & Ollama Setup (lifted from massive-context-mcp)
# =============================================================================


def _check_system_requirements() -> dict:
    """Check if the system meets requirements for running Ollama."""
    import platform

    result = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "is_macos": False,
        "is_apple_silicon": False,
        "ram_gb": 0,
        "ram_sufficient": False,
        "homebrew_installed": False,
        "ollama_installed": False,
        "meets_requirements": False,
        "issues": [],
        "recommendations": [],
    }

    # Check macOS
    if platform.system() == "Darwin":
        result["is_macos"] = True
    else:
        result["issues"].append(f"Not macOS (detected: {platform.system()})")
        result["recommendations"].append("Ollama auto-setup is only supported on macOS")

    # Check Apple Silicon
    machine = platform.machine()
    if machine == "arm64":
        result["is_apple_silicon"] = True
        try:
            chip_info = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if chip_info.returncode == 0:
                result["chip"] = chip_info.stdout.strip()
        except Exception:
            result["chip"] = "Apple Silicon (arm64)"
    else:
        result["issues"].append(f"Not Apple Silicon (detected: {machine})")
        result["recommendations"].append("Apple Silicon (M1/M2/M3/M4) recommended for optimal performance")

    # Check RAM
    try:
        if platform.system() == "Darwin":
            mem_info = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if mem_info.returncode == 0:
                ram_bytes = int(mem_info.stdout.strip())
                ram_gb = ram_bytes / (1024**3)
                result["ram_gb"] = round(ram_gb, 1)
                result["ram_sufficient"] = ram_gb >= MIN_RAM_GB

                if not result["ram_sufficient"]:
                    result["issues"].append(f"Low RAM: {result['ram_gb']}GB (recommend {MIN_RAM_GB}GB+)")
    except Exception as e:
        result["issues"].append(f"Could not determine RAM: {e}")

    # Check Homebrew
    try:
        brew_check = subprocess.run(["which", "brew"], capture_output=True, text=True, timeout=5)
        result["homebrew_installed"] = brew_check.returncode == 0
        if result["homebrew_installed"]:
            result["homebrew_path"] = brew_check.stdout.strip()
        else:
            result["recommendations"].append(
                'Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            )
    except Exception:
        result["issues"].append("Could not check for Homebrew")

    # Check if Ollama is installed
    try:
        ollama_check = subprocess.run(["which", "ollama"], capture_output=True, text=True, timeout=5)
        result["ollama_installed"] = ollama_check.returncode == 0
        if result["ollama_installed"]:
            result["ollama_path"] = ollama_check.stdout.strip()
            try:
                version_check = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
                if version_check.returncode == 0:
                    result["ollama_version"] = version_check.stdout.strip()
            except Exception:
                pass
    except Exception:
        pass

    result["meets_requirements"] = result["is_macos"] and result["is_apple_silicon"] and result["ram_sufficient"]

    return result


async def _check_ollama_status(force_refresh: bool = False) -> dict:
    """Check Ollama server status and available models."""
    import time

    cache = _ollama_status_cache
    now = time.time()

    if not force_refresh and cache["checked_at"] is not None:
        if now - cache["checked_at"] < cache["ttl_seconds"]:
            return {
                "running": cache["running"],
                "models": cache["models"],
                "default_model_available": cache["default_model_available"],
                "cached": True,
                "checked_at": cache["checked_at"],
            }

    if not HAS_HTTPX:
        # Fallback to curl
        return await _check_ollama_status_curl()

    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            default_available = any(m.startswith(EMBEDDING_MODEL.split(":")[0]) for m in models)

            cache.update({
                "checked_at": now,
                "running": True,
                "models": models,
                "default_model_available": default_available,
            })

            return {
                "running": True,
                "url": ollama_url,
                "models": models,
                "model_count": len(models),
                "embedding_model": EMBEDDING_MODEL,
                "embedding_model_available": default_available,
                "cached": False,
            }

    except Exception as e:
        cache.update({
            "checked_at": now,
            "running": False,
            "models": [],
            "default_model_available": False,
        })
        return {
            "running": False,
            "url": ollama_url,
            "error": str(e),
            "message": "Ollama server not running. Start with: ollama serve",
            "models": [],
            "embedding_model_available": False,
        }


async def _check_ollama_status_curl() -> dict:
    """Fallback status check using curl."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "curl", "-s", "-m", "2", f"{OLLAMA_URL}/api/tags",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
        if proc.returncode == 0:
            data = json.loads(stdout)
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            return {
                "running": True,
                "models": models,
                "embedding_model_available": EMBEDDING_MODEL.split(":")[0] in models,
            }
    except Exception:
        pass
    return {"running": False, "models": [], "embedding_model_available": False}


async def _setup_ollama(
    install: bool = False,
    start_service: bool = False,
    pull_model: bool = False,
    model: str = "nomic-embed-text",
) -> dict:
    """Setup Ollama: install via Homebrew, start service, and pull model."""
    result = {
        "actions_taken": [],
        "actions_skipped": [],
        "errors": [],
        "success": True,
    }

    sys_check = _check_system_requirements()
    result["system_check"] = sys_check

    if not sys_check["is_macos"]:
        result["errors"].append("Ollama auto-setup only supported on macOS")
        result["success"] = False
        return result

    if not sys_check["homebrew_installed"] and install:
        result["errors"].append(
            "Homebrew required. Install: "
            '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        result["success"] = False
        return result

    # Install Ollama
    if install:
        if sys_check["ollama_installed"]:
            result["actions_skipped"].append("Ollama already installed")
        else:
            try:
                install_proc = subprocess.run(
                    ["brew", "install", "ollama"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if install_proc.returncode == 0:
                    result["actions_taken"].append("Installed Ollama via Homebrew")
                    sys_check["ollama_installed"] = True
                else:
                    result["errors"].append(f"Failed to install: {install_proc.stderr}")
                    result["success"] = False
            except subprocess.TimeoutExpired:
                result["errors"].append("Installation timed out")
                result["success"] = False
            except Exception as e:
                result["errors"].append(f"Installation error: {e}")
                result["success"] = False

    # Start service
    if start_service and result["success"]:
        if not sys_check["ollama_installed"]:
            result["errors"].append("Cannot start: Ollama not installed")
            result["success"] = False
        else:
            status = await _check_ollama_status(force_refresh=True)
            if status.get("running"):
                result["actions_skipped"].append("Service already running")
            else:
                try:
                    subprocess.run(
                        ["brew", "services", "start", "ollama"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    result["actions_taken"].append("Started Ollama service")
                    await asyncio.sleep(2)
                except Exception as e:
                    result["errors"].append(f"Failed to start: {e}")

    # Pull model
    if pull_model and result["success"]:
        if not sys_check["ollama_installed"]:
            result["errors"].append("Cannot pull: Ollama not installed")
            result["success"] = False
        else:
            status = await _check_ollama_status(force_refresh=True)
            model_base = model.split(":")[0]
            already_pulled = any(m.startswith(model_base) for m in status.get("models", []))

            if already_pulled:
                result["actions_skipped"].append(f"Model {model} already available")
            else:
                try:
                    result["actions_taken"].append(f"Pulling {model}...")
                    pull_proc = subprocess.run(
                        ["ollama", "pull", model],
                        capture_output=True,
                        text=True,
                        timeout=1800,
                    )
                    if pull_proc.returncode == 0:
                        result["actions_taken"].append(f"Pulled {model}")
                    else:
                        result["errors"].append(f"Pull failed: {pull_proc.stderr}")
                        result["success"] = False
                except subprocess.TimeoutExpired:
                    result["errors"].append("Pull timed out")
                    result["success"] = False

    if result["success"]:
        result["ollama_status"] = await _check_ollama_status(force_refresh=True)

    return result


async def _setup_ollama_direct(
    install: bool = False,
    start_service: bool = False,
    pull_model: bool = False,
    model: str = "nomic-embed-text",
) -> dict:
    """Setup Ollama via direct download - no Homebrew, no sudo."""
    result = {
        "method": "direct_download",
        "actions_taken": [],
        "actions_skipped": [],
        "errors": [],
        "warnings": [],
        "success": True,
    }

    sys_check = _check_system_requirements()
    result["system_check"] = {
        "is_macos": sys_check["is_macos"],
        "is_apple_silicon": sys_check["is_apple_silicon"],
        "ram_gb": sys_check["ram_gb"],
    }

    if not sys_check["is_macos"]:
        result["errors"].append("Direct download only supported on macOS")
        result["success"] = False
        return result

    home = Path.home()
    install_dir = home / "Applications"
    app_path = install_dir / "Ollama.app"
    cli_path = app_path / "Contents" / "Resources" / "ollama"

    # Install
    if install:
        if app_path.exists():
            result["actions_skipped"].append(f"Already installed at {app_path}")
        else:
            try:
                install_dir.mkdir(parents=True, exist_ok=True)
                download_url = "https://ollama.com/download/Ollama-darwin.zip"
                zip_path = Path("/tmp/Ollama-darwin.zip")
                extract_dir = Path("/tmp/ollama-extract")

                result["actions_taken"].append("Downloading Ollama...")
                download_proc = subprocess.run(
                    ["curl", "-L", "-o", str(zip_path), download_url],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

                if download_proc.returncode != 0:
                    result["errors"].append(f"Download failed: {download_proc.stderr}")
                    result["success"] = False
                    return result

                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
                extract_dir.mkdir(parents=True, exist_ok=True)

                subprocess.run(
                    ["unzip", "-q", str(zip_path), "-d", str(extract_dir)],
                    capture_output=True,
                    timeout=120,
                )

                extracted_app = extract_dir / "Ollama.app"
                if extracted_app.exists():
                    shutil.move(str(extracted_app), str(app_path))
                    result["actions_taken"].append(f"Installed to {app_path}")
                else:
                    result["errors"].append("Could not find Ollama.app in download")
                    result["success"] = False
                    return result

                zip_path.unlink(missing_ok=True)
                shutil.rmtree(extract_dir, ignore_errors=True)

                result["path_setup"] = {
                    "cli_path": str(cli_path),
                    "add_to_path": f'export PATH="{cli_path.parent}:$PATH"',
                }

            except Exception as e:
                result["errors"].append(f"Installation error: {e}")
                result["success"] = False

    # Start service
    if start_service and result["success"]:
        effective_cli = cli_path if cli_path.exists() else None
        if not effective_cli:
            which_proc = subprocess.run(["which", "ollama"], capture_output=True, text=True)
            if which_proc.returncode == 0:
                effective_cli = Path(which_proc.stdout.strip())

        if not effective_cli:
            result["errors"].append("Ollama CLI not found")
            result["success"] = False
        else:
            status = await _check_ollama_status(force_refresh=True)
            if status.get("running"):
                result["actions_skipped"].append("Service already running")
            else:
                subprocess.Popen(
                    ["nohup", str(effective_cli), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                result["actions_taken"].append("Started Ollama service")
                await asyncio.sleep(3)

    # Pull model
    if pull_model and result["success"]:
        effective_cli = cli_path if cli_path.exists() else None
        if not effective_cli:
            which_proc = subprocess.run(["which", "ollama"], capture_output=True, text=True)
            if which_proc.returncode == 0:
                effective_cli = Path(which_proc.stdout.strip())

        if not effective_cli:
            result["errors"].append("Ollama CLI not found")
            result["success"] = False
        else:
            status = await _check_ollama_status(force_refresh=True)
            model_base = model.split(":")[0]
            if any(m.startswith(model_base) for m in status.get("models", [])):
                result["actions_skipped"].append(f"Model {model} already available")
            else:
                try:
                    result["actions_taken"].append(f"Pulling {model}...")
                    pull_proc = subprocess.run(
                        [str(effective_cli), "pull", model],
                        capture_output=True,
                        text=True,
                        timeout=1800,
                    )
                    if pull_proc.returncode == 0:
                        result["actions_taken"].append(f"Pulled {model}")
                    else:
                        result["errors"].append(f"Pull failed: {pull_proc.stderr}")
                        result["success"] = False
                except Exception as e:
                    result["errors"].append(f"Pull error: {e}")
                    result["success"] = False

    if result["success"]:
        result["ollama_status"] = await _check_ollama_status(force_refresh=True)

    return result


# =============================================================================
# Path Reconstruction via Filesystem Probing
# =============================================================================


class PathReconstructor:
    """Reconstructs actual filesystem paths from Claude's lossy encoded paths."""

    def __init__(self):
        self._cache: dict[str, Optional[str]] = {}
        self._common_roots = self._detect_common_roots()

    def _detect_common_roots(self) -> list[Path]:
        candidates = [Path.home(), Path("/Users"), Path("/home"), Path("/var"), Path("/tmp"), Path("/opt")]
        return [p for p in candidates if p.exists()]

    def load_cache(self, conn: sqlite3.Connection):
        cursor = conn.execute("SELECT encoded_path, actual_path FROM path_cache WHERE exists_on_disk = 1")
        for row in cursor:
            self._cache[row["encoded_path"]] = row["actual_path"]

    def save_to_cache(self, conn: sqlite3.Connection, encoded: str, actual: Optional[str]):
        conn.execute(
            """INSERT OR REPLACE INTO path_cache (encoded_path, actual_path, verified_at, exists_on_disk)
               VALUES (?, ?, ?, ?)""",
            (encoded, actual, datetime.now().isoformat(), 1 if actual else 0),
        )

    def reconstruct(self, encoded_path: str, conn: Optional[sqlite3.Connection] = None) -> Optional[str]:
        if encoded_path in self._cache:
            return self._cache[encoded_path]

        clean = encoded_path.lstrip("-")
        parts = clean.split("-")

        if not parts:
            return None

        actual = self._probe_path(parts)
        self._cache[encoded_path] = actual
        if conn:
            self.save_to_cache(conn, encoded_path, actual)

        return actual

    def _probe_path(self, parts: list[str]) -> Optional[str]:
        if not parts:
            return None

        first_lower = parts[0].lower()

        if first_lower == "users" and len(parts) > 1:
            result = self._probe_from(Path("/Users"), parts[1:])
            if result:
                return str(result)

        if first_lower == "home" and len(parts) > 1:
            result = self._probe_from(Path("/home"), parts[1:])
            if result:
                return str(result)

        home = Path.home()
        if home.name.lower() == first_lower or first_lower in home.name.lower():
            result = self._probe_from(home, parts[1:])
            if result:
                return str(result)

        result = self._probe_from(home, parts)
        if result:
            return str(result)

        for root in self._common_roots:
            result = self._probe_from(root, parts)
            if result:
                return str(result)

        return None

    def _probe_from(self, root: Path, parts: list[str], depth: int = 0) -> Optional[Path]:
        if depth > 50:
            return None

        if not root.exists():
            return None

        if not parts:
            return root if root.is_dir() else None

        single = root / parts[0]
        if single.exists():
            result = self._probe_from(single, parts[1:], depth + 1)
            if result:
                return result

        for end_idx in range(2, min(len(parts) + 1, 6)):
            combined_parts = parts[:end_idx]
            remaining = parts[end_idx:]

            for sep in ["_", ".", "-"]:
                combined = sep.join(combined_parts)
                test = root / combined
                if test.exists():
                    result = self._probe_from(test, remaining, depth + 1)
                    if result:
                        return result

            if end_idx == 3:
                mixed1 = f"{combined_parts[0]}_{combined_parts[1]}.{combined_parts[2]}"
                test = root / mixed1
                if test.exists():
                    result = self._probe_from(test, remaining, depth + 1)
                    if result:
                        return result

        return None


path_reconstructor = PathReconstructor()


# =============================================================================
# Conversation Indexing
# =============================================================================


def compute_file_hash(file_path: Path) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_conversation_data(file_path: Path) -> dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", data.get("conversation", []))

    text_parts = []
    topic = ""
    message_count = 0

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        message_count += 1
        role = msg.get("role", "")
        content = msg.get("content", "")

        if isinstance(content, str):
            text_parts.append(content)
            if role == "user" and not topic:
                topic = content[:100]
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        text_parts.append(text)
                        if role == "user" and not topic:
                            topic = text[:100]
                    elif block.get("type") == "tool_use":
                        text_parts.append(f"tool:{block.get('name', '')}")
                        text_parts.append(json.dumps(block.get("input", {})))

    full_text = "\n".join(text_parts)

    return {
        "topic": topic.replace("\n", " ").strip() or "(No topic)",
        "full_text": full_text,
        "message_count": message_count,
        "total_chars": len(full_text),
        "created_at": data.get("created_at"),
    }


def index_conversation(conn: sqlite3.Connection, file_path: Path, project_encoded: str) -> bool:
    session_id = file_path.stem
    file_hash = compute_file_hash(file_path)

    existing = conn.execute("SELECT id, file_hash FROM conversations WHERE session_id = ?", (session_id,)).fetchone()

    if existing and existing["file_hash"] == file_hash:
        return False

    try:
        data = extract_conversation_data(file_path)
    except (json.JSONDecodeError, IOError):
        return False

    stat = file_path.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
    actual_path = path_reconstructor.reconstruct(project_encoded, conn)

    if existing:
        conn.execute(
            """UPDATE conversations SET
               project_path = ?, file_path = ?, file_hash = ?, modified_at = ?,
               topic = ?, message_count = ?, total_chars = ?, indexed_at = ?
               WHERE id = ?""",
            (
                actual_path,
                str(file_path),
                file_hash,
                modified_at,
                data["topic"],
                data["message_count"],
                data["total_chars"],
                datetime.now().isoformat(),
                existing["id"],
            ),
        )
        conv_id = existing["id"]
        conn.execute("DELETE FROM conversations_fts WHERE rowid = ?", (conv_id,))
    else:
        cursor = conn.execute(
            """INSERT INTO conversations
               (session_id, project_encoded, project_path, file_path, file_hash,
                modified_at, created_at, topic, message_count, total_chars, indexed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                project_encoded,
                actual_path,
                str(file_path),
                file_hash,
                modified_at,
                data.get("created_at"),
                data["topic"],
                data["message_count"],
                data["total_chars"],
                datetime.now().isoformat(),
            ),
        )
        conv_id = cursor.lastrowid

    conn.execute(
        "INSERT OR REPLACE INTO conversation_content (conversation_id, full_text) VALUES (?, ?)",
        (conv_id, data["full_text"]),
    )

    conn.execute(
        """INSERT INTO conversations_fts(rowid, session_id, project_path, topic, content)
           VALUES (?, ?, ?, ?, ?)""",
        (conv_id, session_id, actual_path or "", data["topic"], data["full_text"]),
    )

    return True


def run_full_index(conn: sqlite3.Connection) -> tuple[int, int]:
    if not PROJECTS_DIR.exists():
        return 0, 0

    indexed = 0
    total = 0

    path_reconstructor.load_cache(conn)

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        for conv_file in project_dir.rglob("*.json"):
            total += 1
            if index_conversation(conn, conv_file, project_dir.name):
                indexed += 1

    conn.commit()
    return indexed, total


def ensure_index_current(conn: sqlite3.Connection, max_age_seconds: int = 300) -> bool:
    result = conn.execute("SELECT MAX(indexed_at) as last_indexed FROM conversations").fetchone()

    if result and result["last_indexed"]:
        last_indexed = datetime.fromisoformat(result["last_indexed"])
        age = (datetime.now() - last_indexed).total_seconds()
        if age < max_age_seconds:
            return False

    indexed, _ = run_full_index(conn)
    return indexed > 0


# =============================================================================
# Search Implementations
# =============================================================================


def search_fts(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    fts_query = prepare_fts_query(query)

    try:
        cursor = conn.execute(
            """SELECT c.*, bm25(conversations_fts) as score
               FROM conversations_fts
               JOIN conversations c ON conversations_fts.rowid = c.id
               WHERE conversations_fts MATCH ?
               ORDER BY score
               LIMIT ?""",
            (fts_query, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        words = query.split()
        simple_query = " OR ".join(f'"{w}"' for w in words if w)
        if not simple_query:
            return []
        cursor = conn.execute(
            """SELECT c.*, bm25(conversations_fts) as score
               FROM conversations_fts
               JOIN conversations c ON conversations_fts.rowid = c.id
               WHERE conversations_fts MATCH ?
               ORDER BY score
               LIMIT ?""",
            (simple_query, limit),
        )
        return [dict(row) for row in cursor.fetchall()]


def prepare_fts_query(query: str) -> str:
    if any(op in query for op in [" AND ", " OR ", " NOT ", '"']):
        return query

    words = query.split()
    if not words:
        return '""'

    if len(words) == 1:
        return f"{words[0]}*"

    word_parts = " OR ".join(f"{w}*" for w in words)
    phrase = f'"{query}"'
    return f"({word_parts}) OR {phrase}"


def search_spotlight(query: str, scope_dir: Optional[Path] = None, limit: int = 20) -> list[Path]:
    if not shutil.which("mdfind"):
        return []

    cmd = ["mdfind"]
    scope = scope_dir or PROJECTS_DIR
    cmd.extend(["-onlyin", str(scope)])
    spotlight_query = f"kMDItemTextContent == '*{query}*'cd"
    cmd.append(spotlight_query)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            paths = [Path(p) for p in result.stdout.strip().split("\n") if p]
            paths = [p for p in paths if p.suffix == ".json" and p.exists()]
            return paths[:limit]
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return []


async def get_embedding(text: str) -> Optional[list[float]]:
    """Get embedding from Ollama."""
    if HAS_HTTPX:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text[:8000]},
                )
                response.raise_for_status()
                return response.json().get("embedding")
        except Exception:
            pass
    else:
        # Fallback to curl
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl",
                "-s",
                "-m",
                "30",
                f"{OLLAMA_URL}/api/embeddings",
                "-d",
                json.dumps({"model": EMBEDDING_MODEL, "prompt": text[:8000]}),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=35)
            if proc.returncode == 0:
                data = json.loads(stdout)
                return data.get("embedding")
        except Exception:
            pass
    return None


def embedding_to_bytes(embedding: list[float]) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding)


def bytes_to_embedding(data: bytes) -> Optional[list[float]]:
    try:
        count = len(data) // 4
        return list(struct.unpack(f"{count}f", data))
    except struct.error:
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def search_vector(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    status = await _check_ollama_status()
    if not status.get("running") or not status.get("embedding_model_available", status.get("default_model_available")):
        return []

    query_embedding = await get_embedding(query)
    if query_embedding is None:
        return []

    cursor = conn.execute("SELECT conversation_id, embedding FROM embeddings WHERE embedding IS NOT NULL")

    results = []
    for row in cursor:
        stored = bytes_to_embedding(row["embedding"])
        if stored:
            sim = cosine_similarity(query_embedding, stored)
            results.append((row["conversation_id"], sim))

    results.sort(key=lambda x: x[1], reverse=True)

    conv_ids = [r[0] for r in results[:limit]]
    if not conv_ids:
        return []

    placeholders = ",".join("?" * len(conv_ids))
    cursor = conn.execute(f"SELECT * FROM conversations WHERE id IN ({placeholders})", conv_ids)

    convs = {row["id"]: dict(row) for row in cursor.fetchall()}
    return [{**convs[cid], "similarity_score": score} for cid, score in results[:limit] if cid in convs]


async def hybrid_search(
    conn: sqlite3.Connection,
    query: str,
    project_filter: Optional[str] = None,
    limit: int = 20,
    use_spotlight: bool = True,
    use_vectors: bool = True,
) -> list[dict]:
    results_map: dict[str, dict] = {}

    fts_results = search_fts(conn, query, limit * 2)
    for i, r in enumerate(fts_results):
        results_map[r["session_id"]] = {**r, "fts_rank": i + 1, "sources": ["fts"]}

    if use_spotlight:
        scope = None
        if project_filter:
            for pd in PROJECTS_DIR.iterdir():
                if project_filter.lower() in pd.name.lower():
                    scope = pd
                    break

        spotlight_paths = search_spotlight(query, scope, limit * 2)
        for i, path in enumerate(spotlight_paths):
            sid = path.stem
            if sid in results_map:
                results_map[sid]["spotlight_rank"] = i + 1
                results_map[sid]["sources"].append("spotlight")
            else:
                row = conn.execute("SELECT * FROM conversations WHERE session_id = ?", (sid,)).fetchone()
                if row:
                    results_map[sid] = {**dict(row), "spotlight_rank": i + 1, "sources": ["spotlight"]}

    if use_vectors:
        vector_results = await search_vector(conn, query, limit * 2)
        for i, r in enumerate(vector_results):
            sid = r["session_id"]
            if sid in results_map:
                results_map[sid]["vector_rank"] = i + 1
                results_map[sid]["similarity_score"] = r.get("similarity_score", 0)
                results_map[sid]["sources"].append("vector")
            else:
                results_map[sid] = {**r, "vector_rank": i + 1, "sources": ["vector"]}

    if project_filter:
        results_map = {
            k: v
            for k, v in results_map.items()
            if project_filter.lower() in (v.get("project_path") or v.get("project_encoded") or "").lower()
        }

    def score(r: dict) -> float:
        fts = r.get("fts_rank", 100)
        spot = r.get("spotlight_rank", 100)
        vec = r.get("vector_rank", 100)
        source_bonus = (3 - len(r.get("sources", []))) * 10
        return fts * 0.4 + spot * 0.3 + vec * 0.3 + source_bonus

    sorted_results = sorted(results_map.values(), key=score)
    return sorted_results[:limit]


async def generate_embeddings_batch(conn: sqlite3.Connection, batch_size: int = 10) -> int:
    status = await _check_ollama_status()
    if not status.get("running"):
        return 0

    cursor = conn.execute(
        """SELECT c.id, c.topic, cc.full_text
           FROM conversations c
           JOIN conversation_content cc ON c.id = cc.conversation_id
           LEFT JOIN embeddings e ON c.id = e.conversation_id
           WHERE e.conversation_id IS NULL
           LIMIT ?""",
        (batch_size,),
    )

    count = 0
    for row in cursor.fetchall():
        text = f"{row['topic']}\n\n{row['full_text'][:4000]}"
        embedding = await get_embedding(text)

        if embedding:
            conn.execute(
                """INSERT INTO embeddings (conversation_id, embedding, model, created_at)
                   VALUES (?, ?, ?, ?)""",
                (row["id"], embedding_to_bytes(embedding), EMBEDDING_MODEL, datetime.now().isoformat()),
            )
            count += 1

    conn.commit()
    return count


# =============================================================================
# Input Models
# =============================================================================


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class SearchMode(str, Enum):
    AUTO = "auto"
    FTS = "fts"
    SPOTLIGHT = "spotlight"
    VECTOR = "vector"
    HYBRID = "hybrid"


class SearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., description="Search query - natural language, keywords, or \"exact phrase\"", min_length=1)
    project: Optional[str] = Field(default=None, description="Filter by project path (partial match)")
    mode: SearchMode = Field(default=SearchMode.AUTO, description="Search mode: auto, fts, spotlight, vector, hybrid")
    limit: int = Field(default=20, ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    project: Optional[str] = Field(default=None)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GetConversationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    session_id: str = Field(..., min_length=1)
    include_tool_calls: bool = Field(default=False)
    include_thinking: bool = Field(default=False)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ListProjectsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class StatsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ReindexInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generate_embeddings: bool = Field(default=False, description="Generate vector embeddings (requires Ollama)")


# =============================================================================
# Response Formatting
# =============================================================================


def format_results(results: list[dict], fmt: ResponseFormat, title: str = "Results") -> str:
    if fmt == ResponseFormat.JSON:
        return json.dumps({"count": len(results), "results": results}, indent=2, default=str)

    if not results:
        return f"No {title.lower()} found."

    lines = [f"# {title}\n", f"Found **{len(results)}** result(s)\n"]

    for i, r in enumerate(results, 1):
        project = r.get("project_path") or r.get("project_encoded", "unknown")
        modified = r.get("modified_at", "")[:16].replace("T", " ")
        topic = r.get("topic", "(No topic)")
        session_id = r.get("session_id", "")
        sources = r.get("sources", [])
        source_str = f" [{', '.join(sources)}]" if sources and len(sources) > 1 else ""

        lines.append(f"## {i}. {modified}{source_str}")
        lines.append(f"**Project:** `{project}`")
        lines.append(f"**Topic:** {topic}")
        lines.append(f"**Session:** `{session_id}`")

        if "similarity_score" in r:
            lines.append(f"**Similarity:** {r['similarity_score']:.2%}")

        lines.append("")

    return "\n".join(lines)


# =============================================================================
# MCP Tools - Ollama Setup
# =============================================================================


@mcp.tool()
async def history_system_check() -> dict:
    """Check if system meets requirements for Ollama embeddings.

    Verifies: macOS, Apple Silicon (M1/M2/M3/M4), RAM, Homebrew.
    Use before attempting Ollama setup.
    """
    result = _check_system_requirements()

    if result["meets_requirements"]:
        result["summary"] = (
            f"System ready! {result.get('chip', 'Apple Silicon')} with "
            f"{result['ram_gb']}GB RAM. Use history_setup_ollama to install."
        )
    else:
        result["summary"] = f"System check: {len(result['issues'])} issue(s). See 'issues' for details."

    return result


@mcp.tool()
async def history_setup_ollama(
    install: bool = False,
    start_service: bool = False,
    pull_model: bool = False,
    model: str = "nomic-embed-text",
) -> dict:
    """Install Ollama via Homebrew (macOS).

    Requires Homebrew pre-installed. Uses 'brew install' and 'brew services'.
    PROS: Auto-updates, pre-built binaries, managed service.
    CONS: Requires Homebrew, may prompt for sudo on first install.

    Args:
        install: Install Ollama via Homebrew (requires Homebrew)
        start_service: Start Ollama as a background service via brew services
        pull_model: Pull the embedding model (nomic-embed-text)
        model: Model to pull (default: nomic-embed-text)
    """
    if not any([install, start_service, pull_model]):
        sys_check = _check_system_requirements()
        return {
            "message": "No actions specified. Use install=true, start_service=true, or pull_model=true.",
            "system_check": sys_check,
            "example": "history_setup_ollama(install=true, start_service=true, pull_model=true)",
        }

    result = await _setup_ollama(install=install, start_service=start_service, pull_model=pull_model, model=model)

    if result["success"]:
        result["summary"] = (
            f"Setup complete! Actions: {', '.join(result['actions_taken']) or 'none'}. "
            f"Skipped: {', '.join(result['actions_skipped']) or 'none'}."
        )
    else:
        result["summary"] = f"Setup failed: {'; '.join(result['errors'])}"

    return result


@mcp.tool()
async def history_setup_ollama_direct(
    install: bool = False,
    start_service: bool = False,
    pull_model: bool = False,
    model: str = "nomic-embed-text",
) -> dict:
    """Install Ollama via direct download (macOS).

    Downloads from ollama.com to ~/Applications.
    PROS: No Homebrew needed, no sudo required, fully headless.
    CONS: Manual PATH setup, no auto-updates.

    Args:
        install: Download and install Ollama to ~/Applications (no sudo needed)
        start_service: Start Ollama server (ollama serve) in background
        pull_model: Pull the embedding model (nomic-embed-text)
        model: Model to pull (default: nomic-embed-text)
    """
    if not any([install, start_service, pull_model]):
        return {
            "message": "No actions specified. Use install=true, start_service=true, or pull_model=true.",
            "method": "direct_download",
            "advantages": ["No Homebrew required", "No sudo needed", "Fully headless"],
            "example": "history_setup_ollama_direct(install=true, start_service=true, pull_model=true)",
        }

    result = await _setup_ollama_direct(install=install, start_service=start_service, pull_model=pull_model, model=model)

    if result["success"]:
        result["summary"] = f"Setup complete! Actions: {', '.join(result['actions_taken']) or 'none'}."
        if result.get("path_setup"):
            result["summary"] += f" NOTE: Add to PATH: {result['path_setup']['add_to_path']}"
    else:
        result["summary"] = f"Setup failed: {'; '.join(result['errors'])}"

    return result


@mcp.tool()
async def history_ollama_status(force_refresh: bool = False) -> dict:
    """Check Ollama server status and available models.

    Returns whether Ollama is running and if the embedding model is available.
    Use to check if semantic/vector search is available.

    Args:
        force_refresh: Force refresh the cached status (default: false)
    """
    status = await _check_ollama_status(force_refresh=force_refresh)

    if status.get("running") and status.get("embedding_model_available", status.get("default_model_available")):
        status["recommendation"] = "Ollama ready! Vector search enabled."
    elif status.get("running"):
        status["recommendation"] = f"Ollama running but embedding model not found. Run: ollama pull {EMBEDDING_MODEL}"
    else:
        status["recommendation"] = "Ollama not available. Vector search disabled. Install Ollama and run: ollama serve"

    return status


# =============================================================================
# MCP Tools - History Search
# =============================================================================


@mcp.tool(
    name="cowork_history_search",
    annotations={
        "title": "Search Conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def search_conversations(params: SearchInput) -> str:
    """Search Claude conversation history using hybrid search.

    Combines FTS5 full-text search, macOS Spotlight content indexing, and
    optional vector similarity (requires Ollama). Supports natural language,
    keywords, and "exact phrases".

    Examples:
    - "authentication bug" - finds conversations mentioning both words
    - "how to deploy" - semantic search finds related discussions
    - project:"my-app" query:"database" - filter by project
    """
    init_database()

    with get_db() as conn:
        ensure_index_current(conn)

        use_spotlight = params.mode in (SearchMode.AUTO, SearchMode.HYBRID, SearchMode.SPOTLIGHT)
        use_vectors = params.mode in (SearchMode.AUTO, SearchMode.HYBRID, SearchMode.VECTOR)

        if params.mode == SearchMode.FTS:
            results = search_fts(conn, params.query, params.limit)
            for r in results:
                r["sources"] = ["fts"]
        elif params.mode == SearchMode.SPOTLIGHT:
            paths = search_spotlight(params.query, limit=params.limit)
            results = []
            for p in paths:
                row = conn.execute("SELECT * FROM conversations WHERE session_id = ?", (p.stem,)).fetchone()
                if row:
                    results.append({**dict(row), "sources": ["spotlight"]})
        elif params.mode == SearchMode.VECTOR:
            results = await search_vector(conn, params.query, params.limit)
            for r in results:
                r["sources"] = ["vector"]
        else:
            results = await hybrid_search(conn, params.query, params.project, params.limit, use_spotlight, use_vectors)

    return format_results(results, params.response_format, f"Search: {params.query}")


@mcp.tool(
    name="cowork_history_list",
    annotations={
        "title": "List Recent Conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def list_conversations(params: ListInput) -> str:
    """List recent Claude conversations from the index, sorted by modification time."""
    init_database()

    with get_db() as conn:
        ensure_index_current(conn)

        query = "SELECT * FROM conversations"
        args = []

        if params.project:
            query += " WHERE (project_path LIKE ? OR project_encoded LIKE ?)"
            args.extend([f"%{params.project}%", f"%{params.project}%"])

        query += " ORDER BY modified_at DESC LIMIT ?"
        args.append(params.limit)

        results = [dict(row) for row in conn.execute(query, args).fetchall()]

    return format_results(results, params.response_format, "Recent Conversations")


@mcp.tool(
    name="cowork_history_get",
    annotations={
        "title": "Get Conversation Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def get_conversation(params: GetConversationInput) -> str:
    """Get full content of a specific conversation by session ID."""
    init_database()

    with get_db() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE session_id = ?", (params.session_id,)).fetchone()

        if not row:
            return f"Error: Conversation '{params.session_id}' not found."

        file_path = Path(row["file_path"])
        if not file_path.exists():
            return f"Error: File no longer exists at {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            conv_data = json.load(f)

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(conv_data, indent=2)

    lines = [
        f"# Conversation: {params.session_id}",
        f"**Project:** `{row['project_path'] or row['project_encoded']}`",
        f"**Modified:** {row['modified_at'][:16].replace('T', ' ')}",
        "",
    ]

    messages = conv_data.get("messages", conv_data.get("conversation", []))

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        role_display = {"user": "User", "assistant": "Claude", "system": "System"}.get(role, role)

        lines.append(f"## {role_display}")

        if isinstance(content, str):
            lines.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    btype = block.get("type", "")
                    if btype == "text":
                        lines.append(block.get("text", ""))
                    elif btype == "thinking" and params.include_thinking:
                        lines.append(f"\n<details><summary>Thinking</summary>\n{block.get('thinking', '')}\n</details>\n")
                    elif btype == "tool_use" and params.include_tool_calls:
                        lines.append(
                            f"\n**Tool:** `{block.get('name', '')}`\n```json\n{json.dumps(block.get('input', {}), indent=2)}\n```"
                        )
                    elif btype == "tool_result" and params.include_tool_calls:
                        result = str(block.get("content", ""))[:500]
                        lines.append(f"**Result:** `{result}`")

        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="cowork_history_projects",
    annotations={
        "title": "List Projects",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def list_projects(params: ListProjectsInput) -> str:
    """List all projects with conversation history, showing reconstructed paths."""
    init_database()

    with get_db() as conn:
        ensure_index_current(conn)

        cursor = conn.execute(
            """SELECT project_encoded, project_path, COUNT(*) as count,
                      MAX(modified_at) as last_activity, SUM(total_chars) as chars
               FROM conversations GROUP BY project_encoded ORDER BY last_activity DESC"""
        )
        projects = [dict(row) for row in cursor.fetchall()]

    if params.response_format == ResponseFormat.JSON:
        return json.dumps({"count": len(projects), "projects": projects}, indent=2)

    if not projects:
        return "No projects found."

    lines = ["# Projects\n", f"Found **{len(projects)}** project(s)\n"]

    for i, p in enumerate(projects, 1):
        path = p["project_path"] or p["project_encoded"]
        modified = p["last_activity"][:16].replace("T", " ") if p["last_activity"] else "Unknown"

        lines.append(f"## {i}. {path}")
        lines.append(f"- **Conversations:** {p['count']}")
        lines.append(f"- **Last Activity:** {modified}")
        lines.append(f"- **Content:** {p['chars']:,} chars")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="cowork_history_stats",
    annotations={
        "title": "Get Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def get_stats(params: StatsInput) -> str:
    """Get statistics about conversation history and search capabilities."""
    init_database()

    with get_db() as conn:
        ensure_index_current(conn)

        stats = conn.execute(
            """SELECT COUNT(*) as convs, COUNT(DISTINCT project_encoded) as projects,
                      SUM(total_chars) as chars, SUM(message_count) as msgs,
                      MIN(modified_at) as earliest, MAX(modified_at) as latest
               FROM conversations"""
        ).fetchone()

        embedding_count = conn.execute("SELECT COUNT(*) FROM embeddings WHERE embedding IS NOT NULL").fetchone()[0]
        path_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE project_path IS NOT NULL").fetchone()[0]
        total_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]

    ollama_status = await _check_ollama_status()
    ollama_ok = ollama_status.get("running", False) and ollama_status.get(
        "embedding_model_available", ollama_status.get("default_model_available", False)
    )
    spotlight_ok = shutil.which("mdfind") is not None

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(
            {
                "total_conversations": stats["convs"],
                "total_projects": stats["projects"],
                "total_messages": stats["msgs"],
                "total_chars": stats["chars"],
                "paths_reconstructed": f"{path_count}/{total_count}",
                "embeddings": embedding_count,
                "capabilities": {"fts": True, "spotlight": spotlight_ok, "vector": ollama_ok},
            },
            indent=2,
        )

    lines = [
        "# Statistics\n",
        f"**Conversations:** {stats['convs']:,}",
        f"**Projects:** {stats['projects']}",
        f"**Messages:** {stats['msgs']:,}",
        f"**Content:** {stats['chars']:,} chars",
        "",
        f"**Date Range:** {(stats['earliest'] or '')[:10]} to {(stats['latest'] or '')[:10]}",
        f"**Paths Reconstructed:** {path_count}/{total_count}",
        f"**Embeddings:** {embedding_count}",
        "",
        "## Search Capabilities",
        "- **FTS5 Full-Text:** Yes",
        f"- **macOS Spotlight:** {'Yes' if spotlight_ok else 'No'}",
        f"- **Vector Search:** {'Yes' if ollama_ok else 'No (install Ollama + nomic-embed-text)'}",
    ]

    return "\n".join(lines)


@mcp.tool(
    name="cowork_history_reindex",
    annotations={
        "title": "Rebuild Index",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def reindex(params: ReindexInput) -> str:
    """Rebuild the conversation index and optionally generate embeddings."""
    init_database()

    with get_db() as conn:
        indexed, total = run_full_index(conn)

        embedding_count = 0
        if params.generate_embeddings:
            embedding_count = await generate_embeddings_batch(conn, batch_size=50)

    return f"# Reindex Complete\n\n**Scanned:** {total}\n**Updated:** {indexed}\n**Embeddings:** {embedding_count}"


# =============================================================================
# Main
# =============================================================================


def main():
    """Main entry point for the MCP server."""
    if "--reindex" in sys.argv:
        print("Rebuilding index...")
        init_database()
        with get_db() as conn:
            indexed, total = run_full_index(conn)
        print(f"Indexed {indexed}/{total} conversations")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
