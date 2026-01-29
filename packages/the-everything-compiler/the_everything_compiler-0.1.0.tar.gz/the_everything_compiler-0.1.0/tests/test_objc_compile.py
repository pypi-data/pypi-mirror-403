
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tec import backend, config

def run_test():
    objc_code = """
    #import <Foundation/Foundation.h>
    #include <stdio.h>

    int main() {
        @autoreleasepool {
            NSLog(@"Hello from Objective-C!");
            printf("ObjC compilation worked\\n");
        }
        return 0;
    }
    """
    
    print("Testing Objective-C compilation...")
    compiler_cfg = config.CompilerConfig(command="auto")
    
    # We must pass -fobjc-arc if we want ARC, usually good practice, but for simple test maybe optional?
    # Actually -framework Foundation is needed.
    flags = ["-x", "objective-c", "-framework", "Foundation"]
    
    success, output = backend.compile_c(objc_code, "test_objc_prog", compiler_cfg, extra_flags=flags)
    
    if success:
        print("[PASS] Compilation successful.")
        # Optional: run it
        import subprocess
        try:
            res = subprocess.run(["./test_objc_prog"], capture_output=True, text=True)
            print("Output:", res.stdout.strip())
            if "ObjC compilation worked" in res.stdout:
                 print("[PASS] Execution verified.")
            else:
                 print("[FAIL] Execution output mismatch.")
        except Exception as e:
            print(f"[FAIL] execution failed: {e}")
            
        # cleanup
        if os.path.exists("test_objc_prog"):
            os.remove("test_objc_prog")
    else:
        print("[FAIL] Compilation failed.")
        print(output)
        sys.exit(1)

if __name__ == "__main__":
    if "mac" not in sys.platform and "darwin" not in sys.platform:
        print("Skipping ObjC test on non-mac platform")
        sys.exit(0)
    run_test()
