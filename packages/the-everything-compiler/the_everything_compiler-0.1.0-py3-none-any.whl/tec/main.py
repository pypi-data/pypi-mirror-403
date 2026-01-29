#
# The Everything Compiler
# Licensed under the MIT License
# (check LICENSE.TXT for details.)
#
# tec/main.py
#

import argparse
from pathlib import Path
from typing import Tuple
from . import packer, client, backend, config, __version__

def get_instructions(cfg) -> str:
    compiler_cmd = cfg.compiler.command if cfg.compiler.command != "auto" else "auto-detected compiler"
    platform_info = backend.get_platform()
    
    return f"""
You are The Everything Compiler. Your mission is to transpile the provided codebase into a single, self-contained source file.

## Input Format
The input is an XML string containing the codebase structure:
- `<codebase>`: Root element.
- `<file path="...">`: Contains the source code of a file.
- `binary="true"`: Indicates a binary file (content omitted).

## Output Requirements
1. **Single File**: You must merge all logic, definitions, and implementations into one valid source file.
2. **Platform & Compiler**: Target **{platform_info}**. usage **{compiler_cmd}**.
   - You may write any code that this compiler supports (e.g. C, C++, Objective-C, etc).
   - You can use standard libraries (libc, math, etc) and installed system libraries (Cocoa, GTK, etc).
3. **Compilation Command**:
   - The compiler will be run with this structure:
     `{compiler_cmd} [PRE_FLAGS] your_code.c [POST_FLAGS] -o program`
   - **PRE_FLAGS**: Use for mode flags (e.g. `-x objective-c`), standards (`-std=c11`), defines (`-DDEBUG`), or include paths (`-I/path`).
   - **POST_FLAGS**: Use for linking libraries (`-lm`, `-framework Cocoa`, `-lpthread`).
4. **Memory Management**: Handle memory carefully. If the source language has GC, implement a simple arena or reference counting if needed.
5. **Best Effort**: If a construct is impossible to translate perfectly, implement a functional approximation.
6. **Attempts**: You have 5 (five) attempts to produce the code, so you can experiment and try different approaches. Don't stub out functionality if possible.
7. **Required Flags**: 
   - You MUST specify the standard and libraries via comments on the FIRST TWO lines.
   - **Syntax**:
     `// TEC_FLAGS_PRE: ...`  (Flags to place BEFORE the source file)
     `// TEC_FLAGS_POST: ...` (Flags to place AFTER the source file)
   - **Example for C11 with Math**:
     `// TEC_FLAGS_PRE: -std=c11`
     `// TEC_FLAGS_POST: -lm`
   - **Example for macOS Objective-C**:
     `// TEC_FLAGS_PRE: -x objective-c -fobjc-arc`
     `// TEC_FLAGS_POST: -framework Cocoa -framework Foundation`
8. **Experimental**: Be bold and be creative. You should try to make the code work any way possible. It is not going to be read by a human.

## Response Format
Return ONLY the raw source code. Do NOT use markdown code blocks. Do not output explanations.
"""

def extract_flags_from_code(code: str) -> Tuple[list[str], list[str]]:
    """
    Parse the first few lines for TEC_FLAGS_PRE and TEC_FLAGS_POST.
    Returns (pre_flags, post_flags).
    """
    pre_flags = []
    post_flags = []
    
    lines = code.split('\n')
    # scan first 10 lines
    for line in lines[:10]:
        line = line.strip()
        if line.startswith("// TEC_FLAGS_PRE:"):
            content = line.replace("// TEC_FLAGS_PRE:", "").strip()
            pre_flags.extend(content.split())
        elif line.startswith("// TEC_FLAGS_POST:"):
            content = line.replace("// TEC_FLAGS_POST:", "").strip()
            post_flags.extend(content.split())
            
    return pre_flags, post_flags

def entry_point():
    parser = argparse.ArgumentParser(description="The Everything Compiler")
    parser.add_argument("dir_or_cmd", nargs="?", help="Directory to compile or 'init' command")
    parser.add_argument("--version", "-v", action="version", version=f"The Everything Compiler {__version__} ({backend.get_platform()})")
    parser.add_argument("--save-intermediate", "-s", action="store_true", help="Save intermediate C code to files")
    args = parser.parse_args()
    
    if args.dir_or_cmd is None:
        parser.print_help()
        print("\nWelcome to The Everything Compiler!")
        print("Run 'tec init' to generate a configuration file.")
        print("Run 'tec .' to compile the current directory.")
        return
    
    if args.dir_or_cmd == "init":
        print("[+] Initializing configuration...")
        try:
            config.create_default_config(Path("tec.toml"))
            print("[+] Created tec.toml")
        except FileExistsError:
            print("[!] tec.toml already exists.")
        return

    # Load configuration
    cfg = config.load_config()
    
    # 1. Pack
    print("[+] Packing source...")
    source_dir = Path(args.dir_or_cmd)
    if not source_dir.exists():
        print(f"[!] Error: Directory '{source_dir}' does not exist.")
        return
        
    xml_context = "".join(packer.pack_directory(source_dir))
    
    # 2. Transpile
    print("[+] Transpiling...")
    instructions = get_instructions(cfg)
    c_code = client.generate_c_code(xml_context, instructions, cfg.ai)
    
    if args.save_intermediate:
        with open("tec_output_0.c", "w") as f:
             f.write(c_code)
        print("[+] Saved intermediate code to tec_output_0.c")
    
    # 3. Build with Retry Loop
    print("[+] Compiling...")
    
    max_retries = 5
    attempt = 0
    success = False
    
    while attempt < max_retries:
        if attempt > 0:
            print(f"[+] Retry attempt {attempt}/{max_retries}...")
            
        # Extract flags every time, as AI might change them in a fix
        pre_flags, post_flags = extract_flags_from_code(c_code)
            
        success, output = backend.compile_c(c_code, "program", cfg.compiler, pre_flags=pre_flags, post_flags=post_flags)
        
        if success:
            print("[+] Done!")
            break
        else:
            print(f"[!] Build failed (Attempt {attempt+1}):")
            print(output)
            
            # Check if this was the last attempt
            if attempt == max_retries - 1:
                break
                
            print("[+] Fixing...")
            c_code = client.fix_c_code(c_code, output, instructions, cfg.ai)
            attempt += 1
            
            if args.save_intermediate:
                with open(f"tec_output_{attempt}.c", "w") as f:
                     f.write(c_code)
                print(f"[+] Saved intermediate code to tec_output_{attempt}.c")

    if not success:
        print("[!] Final build failed.")