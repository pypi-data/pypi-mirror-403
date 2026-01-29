#
# The Everything Compiler
# Licensed under the MIT License
# (check LICENSE.TXT for details.)
#
# tec/config.py
#

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Compatible import for toml parsing
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

@dataclass
class AIConfig:
    service: str
    model: str
    api_key: Optional[str] = None

@dataclass
class CompilerConfig:
    command: str

@dataclass
class Config:
    ai: AIConfig
    compiler: CompilerConfig

DEFAULT_CONFIG_TOML = """# The Everything Compiler Configuration

[ai]
# Service to use: google or openai
service = "google"
# Model to use: gemini-3-flash-preview, gpt-5-nano, etc.
model = "gemini-3-flash-preview"
# API Key
# Preferably set TEC_API_KEY environment variable.
# Or provide it directly below (not recommended to commit keys).
api_key = ""

[compiler]
# Compiler command: "auto" to detect automatically, or specific command like "gcc", "clang"
command = "auto"
"""

def create_default_config(path: Path) -> None:
    """Creates a default tec.toml configuration file."""
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    
    with open(path, "w") as f:
        f.write(DEFAULT_CONFIG_TOML)

def load_config(path: Path = Path("tec.toml")) -> Config:
    """Loads configuration from a TOML file."""
    if not path.exists():
        # Fallback to default values if config doesn't exist?
        # Or maybe raise error? For now, let's return defaults if file missing,
        # but the prompt implies we should parse it. 
        # If missing, creating default in-memory config makes sense for "auto" behavior.
        return Config(
            ai=AIConfig(service="google", model="gemini-3.0", api_key=None),
            compiler=CompilerConfig(command="auto")
        )

    with open(path, "rb") as f:
        data = tomllib.load(f)

    ai_data = data.get("ai", {})
    compiler_data = data.get("compiler", {})

    return Config(
        ai=AIConfig(
            service=ai_data.get("service", "google"),
            model=ai_data.get("model", "gemini-3-flash-preview"),
            api_key=os.environ.get("TEC_API_KEY") or ai_data.get("api_key") or None
        ),
        compiler=CompilerConfig(
            command=compiler_data.get("command", "auto")
        )
    )
