#
# The Everything Compiler
# Licensed under the MIT License
# (check LICENSE.TXT for details.)
#
# tec/packer.py
# 

import html
import os
import pathspec
from pathlib import Path
from typing import Generator, Set, List

# --- Configuration ---
# Hardcoded fallbacks in case .gitignore is empty or missing
DEFAULT_IGNORED_DIRS: Set[str] = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'node_modules', 'dist', 'build'}
IGNORED_EXTENSIONS: Set[str] = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.class', '.exe', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.zip', '.tar.gz'}

def load_gitignore(root_path: Path) -> pathspec.PathSpec:
    """
    Loads .gitignore from the root and returns a PathSpec compiler.
    Includes default ignores to ensure basic hygiene.
    """
    gitignore = root_path / ".gitignore"
    patterns = []
    
    # 1. Add defaults first
    patterns.extend(DEFAULT_IGNORED_DIRS)
    
    # 2. Add patterns from file
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            patterns.extend(f.read().splitlines())
            
    # GitWildMatchPattern is the actual syntax used by git
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

def is_binary(file_path: Path) -> bool:
    """Simple heuristic to detect binary files."""
    try:
        with open(file_path, 'rb') as check_file:
            # Read 1KB; if we find a null byte, it's likely binary
            chunk = check_file.read(1024)
            return b'\0' in chunk
    except:
        return True

def pack_directory(root_path: Path) -> Generator[str, None, None]:
    """
    Walks the directory and yields formatted XML chunks.
    """
    spec = load_gitignore(root_path)
    
    yield "<codebase>\n"

    for parent, dirs, files in os.walk(root_path):
        # 1. Prune Directories based on .gitignore
        # This is slightly more complex with pathspec because we need relative paths
        # We iterate backwards to allow safe removal
        for i in range(len(dirs) - 1, -1, -1):
            d = dirs[i]
            dir_path = Path(parent) / d
            rel_path = dir_path.relative_to(root_path)
            
            # pathspec expects a string path (works on Win/Linux/Mac)
            # We append '/' to indicate it is a directory for pattern matching
            if spec.match_file(str(rel_path) + "/"):
                del dirs[i]

        # 2. Process Files
        for file_name in files:
            file_path = Path(parent) / file_name
            
            if file_path.suffix in IGNORED_EXTENSIONS:
                continue

            try:
                rel_path = file_path.relative_to(root_path)
            except ValueError:
                rel_path = file_path

            # Check .gitignore via pathspec
            if spec.match_file(str(rel_path)):
                continue

            if is_binary(file_path):
                yield f'  <file path="{rel_path}" binary="true"/>\n'
                continue

            try:
                # Read content
                content = file_path.read_text(encoding='utf-8', errors='replace')
                safe_content = html.escape(content)
                
                yield f'  <file path="{rel_path}">\n'
                yield f'{safe_content}\n'
                yield '  </file>\n'
            except Exception as e:
                yield f'  \n'

    yield "</codebase>"