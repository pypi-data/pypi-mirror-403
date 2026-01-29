
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tec import main
from tec import backend, config

def test_flag_extraction():
    print("--- Testing Flag Extraction ---")
    
    code = """// TEC_FLAGS_PRE: -x objective-c -fobjc-arc
// TEC_FLAGS_POST: -framework Cocoa -lm
// Some other stuff
#include <stdio.h>
"""
    pre, post = main.extract_flags_from_code(code)
    print(f"Code Sample:\n{code.strip()}")
    print(f"Extracted PRE:  {pre}")
    print(f"Extracted POST: {post}")
    
    if pre == ["-x", "objective-c", "-fobjc-arc"] and post == ["-framework", "Cocoa", "-lm"]:
        print("[PASS] Extraction correct.")
    else:
        print("[FAIL] Extraction incorrect.")
        sys.exit(1)

def test_compilation_flow():
    print("\n--- Testing Compilation with Pre/Post ---")
    if "mac" not in sys.platform and "darwin" not in sys.platform:
        print("Skipping compilation test on non-mac")
        return

    objc_code = """
    #import <Foundation/Foundation.h>
    #include <stdio.h>
    int main() {
        @autoreleasepool {
            NSLog(@"Hello from Pre/Post!");
            printf("Success\\n");
        }
        return 0;
    }
    """
    
    compiler_cfg = config.CompilerConfig(command="auto")
    pre = ["-x", "objective-c", "-fobjc-arc"]
    post = ["-framework", "Foundation"]
    
    success, output = backend.compile_c(objc_code, "test_pre_post", compiler_cfg, pre_flags=pre, post_flags=post)
    
    if success:
        print("[PASS] Compilation successful.")
        if os.path.exists("test_pre_post"):
            os.remove("test_pre_post")
    else:
        print("[FAIL] Compilation failed.")
        print(output)
        sys.exit(1)

if __name__ == "__main__":
    test_flag_extraction()
    test_compilation_flow()
