"""
Prompt Loader - loads prompt templates from versioned text files.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent
DEFAULT_VERSION = os.getenv("PROMPT_VERSION", "v1")


def load_prompt(
    prompt_name: str,
    version: Optional[str] = None,
) -> str:
    """
    Load a prompt template from file.
    Strips null bytes and fixes encoding issues automatically.
    """
    version = version or DEFAULT_VERSION
    prompt_path = PROMPTS_DIR / version / f"{prompt_name}.txt"

    if not prompt_path.exists():
        fallback_path = PROMPTS_DIR / "v1" / f"{prompt_name}.txt"
        if fallback_path.exists():
            logger.warning(
                "prompt_loader.version_not_found",
                prompt=prompt_name,
                version=version,
                fallback="v1",
            )
            prompt_path = fallback_path
        else:
            raise FileNotFoundError(
                f"Prompt '{prompt_name}' not found. "
                f"Path checked: {prompt_path}"
            )

    # Read as bytes first to handle any encoding issues
    with open(prompt_path, "rb") as f:
        raw = f.read()

    # Remove null bytes
    raw = raw.replace(b"\x00", b"")

    # Decode
    content = raw.decode("utf-8", errors="ignore").strip()

    if not content:
        raise ValueError(
            f"Prompt '{prompt_name}' is empty after cleaning. "
            f"Run: python recreate_prompts.py"
        )

    logger.debug(
        "prompt_loader.loaded",
        prompt=prompt_name,
        version=version,
        length=len(content),
    )
    return content


def load_prompt_version(version: str, prompt_name: str) -> str:
    return load_prompt(prompt_name, version=version)


def list_available_prompts(version: Optional[str] = None) -> dict:
    result = {}
    for version_dir in PROMPTS_DIR.iterdir():
        if version_dir.is_dir() and not version_dir.name.startswith("."):
            prompts = [p.stem for p in version_dir.glob("*.txt")]
            result[version_dir.name] = sorted(prompts)
    return result


def get_active_version() -> str:
    return DEFAULT_VERSION