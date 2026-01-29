#
# The Everything Compiler
# Licensed under the MIT License
# (check LICENSE.TXT for details.)
#
# tec/backend.py
#

import shutil
import subprocess
import platform
import tempfile
import os
from typing import Tuple, Optional
from pathlib import Path

DEFAULT_CFLAGS = []

def get_platform() -> str:
    """
    Returns a string identifying the OS, Architecture, and available C Compiler.
    Format: "{OS} {Arch} {Compiler}"
    """
    os_name = platform.system()
    arch = platform.machine()
    
    candidates = ['gcc', 'clang', 'cl', 'cc']
    
    found_compiler = "no_compiler"
    
    for candidate in candidates:
        if shutil.which(candidate):
            try:
                output = subprocess.check_output(
                    [candidate, '--version'], 
                    stderr=subprocess.STDOUT
                ).decode('utf-8').lower()
                
                if 'clang' in output:
                    found_compiler = 'clang'
                    break
                elif 'gcc' in output or 'free software foundation' in output:
                    found_compiler = 'gcc'
                    break
                elif 'microsoft' in output:
                    found_compiler = 'cl'
                    break
                
                # If we found an executable but couldn't identify the signature,
                # default to the binary name (fallback)
                found_compiler = candidate
                break

            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

    return f"{os_name} {arch} {found_compiler}"

# Flags that conflict with our build process or are fundamentally unsafe for this tool's usage
BLOCKED_FLAGS = {"-o", "-c", "-S", "-E", "-M", "-MM"}

def sanitize_flags(flags: list[str]) -> list[str]:
    """
    Filters a list of flags, keeping everything except conflicting build flags.
    """
    safe_flags = []
    
    # Simple pass: just filter out the blocked flags.
    # We don't try to parse arguments (like -o output) because if we block -o, 
    # the orphan argument will likely cause a harmless compiler error (file not found),
    # which is safer and simpler than trying to implement a full CLI parser.
    
    for flag in flags:
        flag_clean = flag.strip()
        if not flag_clean:
            continue
            
        if flag_clean in BLOCKED_FLAGS:
            continue
            
        safe_flags.append(flag_clean)

    return safe_flags

def compile_c(source_code: str, output_name: str, compiler_config, pre_flags: list[str] = None, post_flags: list[str] = None) -> Tuple[bool, str]:
    """
    Writes source code to a temp file, finds compiler, runs build.
    Command structure: compiler [pre_flags] [source] [post_flags] -o output
    """
    if compiler_config.command != "auto":
        compiler = shutil.which(compiler_config.command)
    else:
        compiler = shutil.which("clang") or shutil.which("gcc") or shutil.which("cl")

    if not compiler:
        return False, "No compiler found (checked clang, gcc, cl). Please install one or configure 'command' in tec.toml."

    fd, temp_path = tempfile.mkstemp(suffix=".c", text=True)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(source_code)
            
        cmd = [compiler]
        
        # Add default flags
        cmd.extend(DEFAULT_CFLAGS)
        
        # Add Pre Flags (e.g. -x objective-c, -std=c99, -c)
        if pre_flags:
            safe_pre = sanitize_flags(pre_flags)
            if safe_pre:
                cmd.extend(safe_pre)
        
        # Source file
        cmd.append(temp_path)

        # Add Post Flags (e.g. -lm, -framework Cocoa)
        if post_flags:
            safe_post = sanitize_flags(post_flags)
            if safe_post:
                cmd.extend(safe_post)
        
        # Output
        cmd.extend(['-o', output_name])
        
        print(f"[$] {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, result.stderr or "Compilation successful."
        else:
            return False, result.stderr + "\n" + result.stdout

    except Exception as e:
        return False, str(e)
    finally:
        # Cleanup temp source file
        if os.path.exists(temp_path):
            os.remove(temp_path)