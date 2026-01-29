
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tec.backend import sanitize_flags

def run_tests():
    test_cases = [
        # (Input, Expected)
        (["-lm"], ["-lm"]),
        (["-lpthread", "-O3"], ["-lpthread", "-O3"]),
        (["-o", "/bin/sh"], ["/bin/sh"]), # -o blocked, argument remains (harmlessly)
        (["-S", "-c"], []), # Compile options blocked
        (["-Wall", "-Wextra", "-Werror"], ["-Wall", "-Wextra", "-Werror"]), # Warnings allowed now
        (["-DDEBUG", "-std=c99"], ["-DDEBUG", "-std=c99"]),
        (["-I/usr/include"], ["-I/usr/include"]),
        (["-g", "-fPIC"], ["-g", "-fPIC"]),
        (["  -lm  "], ["-lm"]),
        ([""], []),
        (["-lm", "-o", "output", "-DTEST"], ["-lm", "output", "-DTEST"]), 
        (["-framework", "Cocoa"], ["-framework", "Cocoa"]),
        (["-L/usr/local/lib"], ["-L/usr/local/lib"]),
        (["-UnknownFlag", "-weird-stuff"], ["-UnknownFlag", "-weird-stuff"]), # Unknown flags allowed
    ]

    failed = False
    for input_flags, expected in test_cases:
        result = sanitize_flags(input_flags)
        if result != expected:
            print(f"[FAIL] Input: {input_flags}")
            print(f"       Expected: {expected}")
            print(f"       Got:      {result}")
            failed = True
        else:
            print(f"[PASS] Input: {input_flags} -> {result}")

    if failed:
        print("Some tests failed.")
        sys.exit(1)
    else:
        print("All tests passed!")

if __name__ == "__main__":
    run_tests()
